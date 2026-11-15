"""Runs of multi-day books: ``kinn book <config>``.

A book config (``books/<config>.yaml``) names the alphas and their weights, the universe, the
risk model, the portfolio constructor, the limits, how to execute and how often to rebalance.
The book carries positions from one session to the next, so months run in order; the state at
each month end is saved and a paused run continues with ``--resume <run_id>``.
"""

from __future__ import annotations

import dataclasses
import importlib.util
import json
import os
import time
from datetime import UTC, date, datetime
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import yaml

from kinn.alpha.base import Alpha
from kinn.core.settings import Settings, load_settings
from kinn.core.types import BookFill
from kinn.costs import model as cost_model
from kinn.data.daily import DailyData, load_daily
from kinn.data.store import DataStore
from kinn.data.universe import Universe
from kinn.engine.daily.engine import BookConfig, BookState, DailyEngine
from kinn.execution.auction import AuctionExecution
from kinn.portfolio.construct import Constructor, Limits, MeanVariance, RankedBook
from kinn.registry import runs as registry
from kinn.reporting import book_metrics
from kinn.risk.model import SingleIndexRisk

REPO_ROOT = Path(__file__).resolve().parents[2]
FIRST_SESSION = date(2003, 9, 10)
FILL_FIELDS = [f.name for f in dataclasses.fields(BookFill)]
CONSTRUCTORS = {"mean_variance": MeanVariance, "ranked": RankedBook}
BOOK_METRICS_SCHEMA = "book-metrics-1"


def books_dir() -> Path:
    return Path(os.environ.get("KINN_BOOKS_DIR") or REPO_ROOT / "books")


def strategies_dir() -> Path:
    return Path(os.environ.get("KINN_STRATEGIES_DIR") or REPO_ROOT / "strategies")


def _merge(base: dict, over: dict) -> dict:
    out = dict(base)
    for key, value in over.items():
        both = isinstance(value, dict) and isinstance(out.get(key), dict)
        same_kind = both and value.get("kind", out[key].get("kind")) == out[key].get("kind")
        out[key] = _merge(out[key], value) if same_kind else value
    return out


def load_book(config: str) -> dict:
    """Read ``books/<config>.yaml``. ``extends: other`` layers it over another config."""
    cfg = yaml.safe_load((books_dir() / f"{config}.yaml").read_text()) or {}
    parent = cfg.pop("extends", None)
    return _merge(load_book(parent), cfg) if parent else cfg


def load_alpha(name: str, params: dict) -> Alpha:
    """Load ``strategies/<name>/alpha.py`` by path and call its ``build(params)``."""
    path = strategies_dir() / name / "alpha.py"
    spec = importlib.util.spec_from_file_location(f"kinn_alpha_{name}", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.build(params)


def parts_of(cfg: dict) -> dict:
    """The models a book config names, built."""
    universe = dict(cfg.get("universe", {}))
    top = universe.pop("top_by_marketcap", None)
    portfolio = dict(cfg.get("portfolio", {}))
    constructor: Constructor = CONSTRUCTORS[portfolio.pop("kind", "mean_variance")](**portfolio)
    short = cfg.get("short", {})
    return {
        "universe": Universe(name=cfg["book"], **universe),
        "top_by_marketcap": top,
        "alphas": [
            (load_alpha(a["strategy"], a.get("params", {})), float(a.get("weight", 1.0)))
            for a in cfg["alphas"]
        ],
        "risk_model": SingleIndexRisk(**cfg.get("risk_model", {})),
        "constructor": constructor,
        "execution": AuctionExecution(**cfg.get("execution", {})),
        "limits": Limits(**cfg.get("limits", {})),
        "config": BookConfig(
            account=float(cfg.get("account", 25_000)),
            rebalance=cfg.get("rebalance", "monthly"),
            borrow_rate=float(short.get("borrow_rate", 0.01)),
            short_min_marketcap=float(short.get("min_marketcap", 1e9)),
            short_min_price=float(short.get("min_price", 5.0)),
            lookahead_check_rate=float(cfg.get("lookahead_check_rate", 0.25)),
            seed=int(cfg.get("seed", 0)),
        ),
    }


def make_engine(cfg: dict, data: DailyData, start_index: int) -> DailyEngine:
    p = parts_of(cfg)
    return DailyEngine(
        data=data, alphas=p["alphas"], risk_model=p["risk_model"], constructor=p["constructor"],
        execution=p["execution"], limits=p["limits"],
        costs=cost_model.load(cfg["cost_calibration"]), config=p["config"],
        start_index=start_index,
    )  # fmt: skip


def start_run(
    config: str,
    *,
    settings: Settings | None = None,
    scratch: bool = False,
    agent: str | None = None,
    repo: Path = REPO_ROOT,
) -> Path:
    """Create the run folder and manifest. Refuses uncommitted code unless ``scratch``."""
    settings = settings or load_settings()
    cfg = load_book(config)
    git = registry.git_state(repo)
    registry.check_clean(git, scratch=scratch)
    store = DataStore(settings)
    start = date.fromisoformat(str(cfg["period"]["start"]))
    end = date.fromisoformat(str(cfg["period"]["end"]))
    everything = store.sessions(FIRST_SESSION, end)  # raises if the period reaches the holdout
    sessions = [d for d in everything if d >= start]
    p = parts_of(cfg)
    lookback = max([p["risk_model"].lookback] + [a.lookback for a, _ in p["alphas"]]) + 2
    history = [d for d in everything if d < start][-lookback:]
    agent = agent or os.environ.get("KINN_AGENT", "human")
    short = registry.config_hash(
        {"config": cfg, "commit": git["commit"], "build": store.build_id, "kind": "book"}
    )
    run_id = registry.new_run_id(agent, cfg["book"], short)
    run_dir = settings.runs_dir / run_id
    (run_dir / "parts").mkdir(parents=True)
    manifest = {
        "schema": registry.MANIFEST_SCHEMA,
        "run_id": run_id,
        "kind": "book",
        "strategy": cfg["book"],
        "alphas": [a["strategy"] for a in cfg["alphas"]],
        "family": cfg.get("family", cfg["book"]),
        "prior_trials": int(cfg.get("prior_trials", 0)),
        "config": config,
        "config_hash": short,
        "resolved_config": cfg,
        "cost_calibration": cfg["cost_calibration"],
        "git": git,
        "scratch": scratch,
        "agent": agent,
        "data_build_id": store.build_id,
        "bars_id": store.info["bars_id"],
        "period": {"start": start.isoformat(), "end": end.isoformat()},
        "history_sessions": [d.isoformat() for d in history],
        "sessions": [d.isoformat() for d in sessions],
        "started_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "finished_at": None,
        "status": "running",
        "schemas": {"metrics": BOOK_METRICS_SCHEMA},
    }
    registry.write_json(run_dir / "manifest.json", manifest)
    return run_dir


def _fundamentals(alphas: list[tuple[Alpha, float]]) -> tuple[str, ...]:
    """The fundamentals the book's alphas declare (``alpha.fundamentals``)."""
    return tuple(sorted({name for a, _ in alphas for name in getattr(a, "fundamentals", ())}))


def _write(rows: list[dict], path: Path) -> None:
    tmp = path.with_suffix(".tmp")
    pq.write_table(pa.Table.from_pylist(rows), tmp)
    os.replace(tmp, path)


def continue_run(
    run_dir: Path, *, settings: Settings | None = None, budget_seconds: float = float("inf")
) -> bool:
    """Simulate pending months in order until done or out of time. True when complete."""
    settings = settings or load_settings()
    deadline = time.time() + budget_seconds
    manifest = json.loads((run_dir / "manifest.json").read_text())
    cfg, parts = manifest["resolved_config"], run_dir / "parts"
    history = [date.fromisoformat(d) for d in manifest["history_sessions"]]
    sessions = [date.fromisoformat(d) for d in manifest["sessions"]]
    months: dict[str, list[int]] = {}
    for offset, day in enumerate(sessions):
        months.setdefault(day.isoformat()[:7], []).append(len(history) + offset)
    done = [m for m in months if (parts / f"{m}.json").exists()]
    pending = [m for m in months if m not in done]
    if pending:
        saved = json.loads((parts / f"{done[-1]}.state.json").read_text()) if done else None
        held = tuple(int(k) for k in saved["positions"]) if saved else ()
        p = parts_of(cfg)
        data = load_daily(
            DataStore(settings, build_id=manifest["data_build_id"]), history + sessions,
            p["universe"], top_by_marketcap=p["top_by_marketcap"], include=held,
            fundamentals=_fundamentals(p["alphas"]),
        )  # fmt: skip
        engine = make_engine(cfg, data, len(history))
        first = months[pending[0]][0]
        if saved:
            state = BookState.from_dict(saved, data, first)
        else:
            state = BookState.from_dict(
                {"cash": engine.config.account, "positions": {}}, data, first
            )
        for month in pending:
            if time.time() > deadline:
                break
            rows = months[month]
            result = engine.run(state, rows[0], rows[-1] + 1)
            _write(result.daily, parts / f"{month}.daily.parquet")
            _write([dataclasses.asdict(f) for f in result.fills], parts / f"{month}.fills.parquet")
            _write(result.positions, parts / f"{month}.positions.parquet")
            registry.write_json(parts / f"{month}.state.json", state.to_dict(data.permatickers))
            registry.write_json(parts / f"{month}.json", result.counts)
    if any(not (parts / f"{m}.json").exists() for m in months):
        return False
    finalize(run_dir)
    return True


def _concat(parts: Path, kind: str) -> pa.Table | None:
    tables = [pq.read_table(p) for p in sorted(parts.glob(f"*.{kind}.parquet"))]
    tables = [t for t in tables if t.num_rows]
    return pa.concat_tables(tables, promote_options="default") if tables else None


def finalize(run_dir: Path) -> None:
    manifest = json.loads((run_dir / "manifest.json").read_text())
    parts = run_dir / "parts"
    counts: dict[str, int] = {}
    for path in sorted(parts.glob("*.json")):
        if path.name.endswith(".state.json"):
            continue
        for key, value in json.loads(path.read_text()).items():
            counts[key] = counts.get(key, 0) + value
    daily = _concat(parts, "daily")
    pq.write_table(daily, run_dir / "daily.parquet")
    for kind in ("fills", "positions"):
        table = _concat(parts, kind)
        if table is not None:
            pq.write_table(table, run_dir / f"{kind}.parquet")
    account = float(manifest["resolved_config"].get("account", 25_000))
    summary = book_metrics.summarize(daily.to_pydict(), account=account, counts=counts)
    summary["schema"] = BOOK_METRICS_SCHEMA
    registry.write_json(run_dir / "metrics.json", summary)
    manifest["status"] = "complete"
    manifest["finished_at"] = datetime.now(UTC).isoformat(timespec="seconds")
    registry.write_json(run_dir / "manifest.json", manifest)
