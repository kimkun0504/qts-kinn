"""The Data page: what the research data holds. Read from the build's own description, the
Parquet files' metadata (row counts only), the sealed calendar and the versioned inputs; no
holdout row is read. Worked out once per build and kept until the build changes.
"""

from __future__ import annotations

import json
from collections import Counter
from datetime import date, timedelta
from pathlib import Path

import pyarrow.parquet as pq

from kinn.core.settings import HOLDOUT_START, Settings
from kinn.data import inputs
from kinn.data.store import DataStore

TABLES = (
    ("panel", "panel/*.parquet", "One row per company and session: prices, volume, market value"),
    ("security master", "master/security_master.parquet", "Every company, listed or delisted"),
    ("symbol history", "master/symbol_history.parquet", "Each ticker a company traded under"),
    ("splits", "master/splits.parquet", "Splits as the vendor gives them"),
    ("dividends", "master/dividends.parquet", "Cash per share by ex-date, spinoffs included"),
    ("8-K events", "sharadar/events.parquet", "8-K filings with their item codes"),
    ("fundamentals", "sharadar/sf1.parquet", "As-reported statements, by filing date"),
    ("vendor daily", "sharadar/daily.parquet", "The vendor's daily valuation figures"),
)
_CACHE: dict[str, dict] = {}


def _rows(files: list[Path]) -> int | None:
    try:
        return sum(pq.ParquetFile(f).metadata.num_rows for f in files)
    except (OSError, ValueError):
        return None


def _size(files: list[Path]) -> int:
    return sum(f.stat().st_size for f in files if f.is_file())


def _builds(settings: Settings, current: str) -> list[dict]:
    out = []
    for folder in sorted((settings.data_dir / "builds").iterdir()):
        info = folder / "build.json"
        if not info.is_file():
            continue
        try:
            meta = json.loads(info.read_text())
        except ValueError:
            continue
        out.append({"id": folder.name, "created_at": meta.get("created_at"),
                    "data_version": meta.get("data_version"), "bars_id": meta.get("bars_id"),
                    "current": folder.name == current})  # fmt: skip
    return sorted(out, key=lambda b: b["created_at"] or "", reverse=True)


def _unseals(settings: Settings) -> dict:
    log = settings.data_dir / "unseal_log.jsonl"
    if not log.is_file():
        return {"reads": 0, "last": None}
    last, reads = None, 0
    for line in log.read_text().splitlines():
        try:
            entry = json.loads(line)
        except ValueError:
            continue
        reads += 1
        last = entry.get("at") or last
    return {"reads": reads, "last": last}


def _inputs(settings: Settings) -> list[dict]:
    out = []
    for name in ("form4", "form8k_timed"):
        try:
            meta = inputs.info(settings, name)
        except Exception:  # noqa: BLE001  an input not built is listed as such
            out.append({"name": name, "built": False})
            continue
        out.append({
            "name": name, "built": True, "input_id": meta.get("input_id"),
            "version": meta.get("version"), "rows": meta.get("rows"),
            "first": meta.get("first_filed") or meta.get("first_accepted_day"),
            "last": meta.get("last_filed") or meta.get("last_accepted_day"),
            "built_at": meta.get("built_at"), "basis": meta.get("coverage_basis"),
        })  # fmt: skip
    return out


def catalog(settings: Settings, store: DataStore) -> dict:
    if store.build_id in _CACHE:
        return {**_CACHE[store.build_id], "seal": {**_CACHE[store.build_id]["seal"],
                                                   **_unseals(settings)}}  # fmt: skip
    info = store.info
    sessions = store.sessions(date(1990, 1, 1), HOLDOUT_START - timedelta(days=1))
    companies = store.securities().to_pylist()
    categories = Counter(c.get("category") or "Unknown" for c in companies)
    sectors = Counter(c.get("sector") or "Unknown" for c in companies)
    tables = []
    for name, pattern, note in TABLES:
        files = sorted(store.root.glob(pattern))
        if files:
            tables.append({"name": name, "path": pattern, "files": len(files), "rows": _rows(files),
                           "bytes": _size(files), "note": note})  # fmt: skip
    bars = []
    for kind in ("daily", "minute"):
        files = sorted((store.bars_root / kind).glob("*"))
        years = sorted({f.name.split("=")[-1].split(".")[0] for f in files if "=" in f.name})
        bars.append({"name": f"{kind} bars", "path": f"bars/{info.get('bars_id')}/{kind}",
                     "files": len(files), "years": years})  # fmt: skip
    out = {
        "schema": "data-catalog-1",
        "build": {"id": store.build_id, "created_at": info.get("created_at"),
                  "data_version": info.get("data_version"), "bars_id": info.get("bars_id"),
                  "sharadar_snapshot": info.get("sharadar_snapshot"),
                  "panel": info.get("panel") or {}},
        "builds": _builds(settings, store.build_id),
        "calendar": {"first": sessions[0].isoformat() if sessions else None,
                     "last": sessions[-1].isoformat() if sessions else None,
                     "sessions": len(sessions)},
        "companies": {"total": len(companies),
                      "delisted": sum(bool(c.get("delisted")) for c in companies),
                      "categories": categories.most_common(8),
                      "sectors": sectors.most_common(12)},
        "tables": tables, "bars": bars, "inputs": _inputs(settings),
        "seal": {"holdout_start": HOLDOUT_START.isoformat(), **_unseals(settings)},
    }  # fmt: skip
    _CACHE.clear()
    _CACHE[store.build_id] = out
    return out
