"""Build the processed data, in resumable steps that fit a time budget.

Two levels, so the large bar conversion is not redone when the small tables change:

- ``bars/<bars_id>/``     Massive bars as Parquet; depends only on the raw files.
- ``builds/<build_id>/``  security master, daily panel, Sharadar tables; depends on the bars,
  the Sharadar snapshot and ``DATA_VERSION``. ``build_id`` is what every run records.

``builds/CURRENT`` names the build that readers use by default.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import duckdb
import pyarrow.parquet as pq

from kinn.core.settings import HOLDOUT_START, Settings
from kinn.data import bars, master, panel, raw, sharadar

DATA_VERSION = "data-1"
SHARADAR_TABLES = ("TICKERS", "ACTIONS", "DAILY", "SEP", "EVENTS")


@dataclass(frozen=True)
class BuildPaths:
    bars_id: str
    bars_root: Path
    build_id: str
    build_root: Path
    snapshot: Path


def paths(settings: Settings) -> BuildPaths:
    bars_identifier = bars.bars_id(settings.raw_dir)
    snapshot = raw.sharadar_snapshot(settings.raw_dir)
    zips = [raw.sharadar_zip(snapshot, t) for t in SHARADAR_TABLES]
    build_identifier = raw.fingerprint(
        [(z.name, z.stat().st_size) for z in zips],
        bars_identifier,
        DATA_VERSION,
        HOLDOUT_START.isoformat(),
    )
    return BuildPaths(
        bars_identifier,
        settings.data_dir / "bars" / bars_identifier,
        build_identifier,
        settings.data_dir / "builds" / build_identifier,
        snapshot,
    )


def build_bars(settings: Settings, *, budget_seconds: float, workers: int = 4) -> tuple[int, int]:
    """Convert pending bar files. Returns (finished now, still pending)."""
    root = paths(settings).bars_root
    total_done = 0
    while True:
        steps = bars.pending_steps(settings.raw_dir, root)
        if not steps:
            return total_done, 0
        done = bars.run_steps(steps, budget_seconds=budget_seconds, workers=workers)
        total_done += done
        if done < len(steps):
            return total_done, len(steps) - done


def _write_master(p: BuildPaths) -> None:
    shar, out = p.build_root / "sharadar", p.build_root / "master"
    out.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect()
    tmp = out / "security_master.tmp"
    con.execute(
        f"""copy (select permaticker, ticker, name, exchange, category, siccode, sector, industry,
                         currency, location, firstpricedate as first_price_date,
                         lastpricedate as last_price_date,
                         lastpricedate is not null as delisted
                  from '{shar}/tickers.parquet' order by permaticker)
            to '{tmp}' (format parquet, compression zstd)"""
    )
    os.replace(tmp, out / "security_master.parquet")
    tmp = out / "splits.tmp"
    con.execute(
        f"""copy (select s.permaticker, a.date, a.value as ratio
                  from '{shar}/actions.parquet' a join '{shar}/tickers.parquet' s using (ticker)
                  where a.action = 'split' and a.value > 0 order by 1, 2)
            to '{tmp}' (format parquet, compression zstd)"""
    )
    os.replace(tmp, out / "splits.parquet")
    con.close()
    history = master.symbol_history(
        pq.read_table(shar / "tickers.parquet"),
        sharadar.read_ticker_changes(raw.sharadar_zip(p.snapshot, "ACTIONS")),
    )
    tmp = out / "symbol_history.tmp"
    pq.write_table(history, tmp, compression="zstd")
    os.replace(tmp, out / "symbol_history.parquet")


def build_tables(settings: Settings, *, budget_seconds: float = 3600.0) -> tuple[str, list[str]]:
    """Build ``builds/<build_id>/``. Returns (build_id, steps still pending)."""
    p = paths(settings)
    shar = p.build_root / "sharadar"
    deadline = time.monotonic() + budget_seconds
    info_path = p.build_root / "build.json"

    steps: list[tuple[str, Path, object]] = [
        (
            "sharadar tickers",
            shar / "tickers.parquet",
            lambda: sharadar.ingest_tickers(
                raw.sharadar_zip(p.snapshot, "TICKERS"), shar / "tickers.parquet"
            ),
        )
    ]
    for table in ("ACTIONS", "DAILY", "SEP", "EVENTS"):
        dst = shar / f"{table.lower()}.parquet"
        steps.append(
            (
                f"sharadar {table.lower()}",
                dst,
                lambda t=table, d=dst: sharadar.ingest_dated(raw.sharadar_zip(p.snapshot, t), t, d),
            )
        )
    steps.append(
        ("master", p.build_root / "master" / "symbol_history.parquet", lambda: _write_master(p))
    )

    def finish() -> None:
        if not any((p.bars_root / "daily").glob("*.parquet")):
            raise FileNotFoundError("daily bars are not built yet; run `kinn data bars` first")
        stats = panel.build_panel(bars_root=p.bars_root, build_root=p.build_root)
        info = {
            "build_id": p.build_id,
            "bars_id": p.bars_id,
            "data_version": DATA_VERSION,
            "holdout_start": HOLDOUT_START.isoformat(),
            "sharadar_snapshot": p.snapshot.name,
            "created_at": datetime.now(UTC).isoformat(timespec="seconds"),
            "panel": stats,
        }
        tmp = info_path.with_suffix(".tmp")
        tmp.write_text(json.dumps(info, indent=2) + "\n")
        os.replace(tmp, info_path)

    steps.append(("panel", info_path, finish))

    pending = [name for name, dst, _ in steps if not dst.exists()]
    for name, dst, run in steps:
        if dst.exists():
            continue
        if time.monotonic() > deadline:
            break
        run()
        pending.remove(name)
    if not pending:
        (settings.data_dir / "builds" / "CURRENT").write_text(p.build_id + "\n")
    return p.build_id, pending
