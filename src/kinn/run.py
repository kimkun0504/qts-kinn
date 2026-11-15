"""The one entry point for runs: ``kinn run <strategy> --config <name>``.

A run is resumable: sessions are simulated a month at a time into ``parts/`` and a run that
stops (time budget, crash) continues with ``--resume <run_id>``. Sessions are independent
(fixed-dollar sizing, flat every night), so the months can run in parallel.
"""

from __future__ import annotations

import dataclasses
import importlib.util
import json
import multiprocessing
import os
import random
import time
from concurrent.futures import ProcessPoolExecutor
from datetime import UTC, date, datetime
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import yaml

from kinn.core.settings import Settings, load_settings
from kinn.core.types import Trade
from kinn.costs import model as cost_model
from kinn.data.store import DataStore
from kinn.engine.intraday.data import load_day
from kinn.engine.intraday.simulator import FillConfig, simulate_day
from kinn.engine.intraday.strategy import (
    Strategy,
    check_no_lookahead,
    compute_features,
    day_signals,
)
from kinn.registry import runs as registry
from kinn.reporting import metrics as metrics_module
from kinn.risk import overlay
from kinn.risk.sizing import RiskConfig
from kinn.validation import event_study

REPO_ROOT = Path(__file__).resolve().parents[2]
TRADE_FIELDS = [f.name for f in dataclasses.fields(Trade)]
COUNT_KEYS = (
    "signals",
    "rejected_capital",
    "rejected_size",
    "unfilled",
    "lookahead_checks",
    "rejected_risk",
    "paused_sessions",
)


def strategies_dir() -> Path:
    return Path(os.environ.get("KINN_STRATEGIES_DIR") or REPO_ROOT / "strategies")


def load_strategy(name: str, params: dict) -> Strategy:
    """Load ``strategies/<name>/strategy.py`` by path and call its ``build(params)``."""
    path = strategies_dir() / name / "strategy.py"
    spec = importlib.util.spec_from_file_location(f"kinn_strategy_{name}", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.build(params)


def load_config(name: str, config: str) -> tuple[dict, dict]:
    folder = strategies_dir() / name
    meta = yaml.safe_load((folder / "strategy.yaml").read_text())
    cfg = yaml.safe_load((folder / "configs" / f"{config}.yaml").read_text()) or {}
    return meta, cfg


def _trades_table(trades: list[Trade]) -> pa.Table:
    return pa.table({f: [getattr(t, f) for t in trades] for f in TRADE_FIELDS})


def _month_key(day: date) -> str:
    return f"{day.year}-{day.month:02d}"


def run_month(job: dict) -> str:
    """Simulate one month for one run. Runs in a worker process."""
    shared = {k: v for k, v in job.items() if k not in ("config", "parts", "kind")}
    shared["runs"] = [{"config": job["config"], "parts": job["parts"], "kind": job.get("kind")}]
    return run_month_multi(shared)


def run_month_multi(job: dict) -> str:
    """Simulate one month's sessions for several configs of one strategy, loading each session
    once. Every config writes its own part files, exactly as if it had run alone."""
    settings = Settings(**{k: Path(v) for k, v in job["settings"].items()})
    store = DataStore(settings, build_id=job["build_id"])
    costs = cost_model.load(job["cost_calibration"])
    runs = []
    for spec in job["runs"]:
        cfg = spec["config"]
        runs.append({
            "strategy": load_strategy(job["strategy"], cfg.get("params", {})),
            "risk": RiskConfig(**cfg.get("risk", {})),
            "fills": FillConfig(**cfg.get("fills", {})),
            "rate": float(cfg.get("lookahead_check_rate", 0.1)),
            "seed": cfg.get("seed", 0),
            "study": spec.get("kind") == "event_study",
            "parts": Path(spec["parts"]),
            "trades": [], "events": [], "counts": dict.fromkeys(COUNT_KEYS, 0),
        })  # fmt: skip
    first = runs[0]["strategy"]
    if any(r["strategy"].universe.where() != first.universe.where() for r in runs):
        raise ValueError("configs run together must share one universe")
    share_features = all(
        [f.name for f in r["strategy"].features] == [f.name for f in first.features] for r in runs
    )
    for day in (date.fromisoformat(d) for d in job["sessions"]):
        data = load_day(store, day, first.universe)
        shared = compute_features(first, data.view) if share_features and len(runs) > 1 else None
        for r in runs:
            strategy, counts = r["strategy"], r["counts"]
            if shared is None:
                signals = day_signals(strategy, data.view)
            else:
                signals = strategy.signals(data.view, shared)
            rng = random.Random(f"{r['seed']}:{day.isoformat()}")
            if signals and rng.random() < r["rate"]:
                cut = rng.randrange(data.view.open_minute, data.view.close_minute)
                check_no_lookahead(strategy, data.view, signals, [cut])
                counts["lookahead_checks"] += 1
            if r["study"]:
                counts["signals"] += len(signals)
                for signal in signals:
                    row = event_study.measure(
                        day, data.view.symbols[signal.symbol], signal,
                        open_minute=data.view.open_minute, close_minute=data.view.close_minute,
                        official_close=data.official_close.get(signal.symbol), costs=costs,
                        position_dollars=r["risk"].position_dollars,
                        no_entry_before_close=r["fills"].no_entry_before_close,
                    )  # fmt: skip
                    if row is None:
                        counts["unfilled"] += 1
                    else:
                        r["events"].append(row)
                continue
            result = simulate_day(data, signals, risk=r["risk"], config=r["fills"], costs=costs)
            r["trades"].extend(result.trades)
            for key in (
                "signals",
                "rejected_capital",
                "rejected_size",
                "unfilled",
                "rejected_risk",
            ):
                counts[key] += getattr(result, key)
    for r in runs:
        tmp = r["parts"] / f"{job['month']}.parquet.tmp"
        if r["study"]:
            table = pa.Table.from_pylist(r["events"], schema=event_study.SCHEMA)
        else:
            table = _trades_table(r["trades"])
        pq.write_table(table, tmp)
        os.replace(tmp, r["parts"] / f"{job['month']}.parquet")
        registry.write_json(r["parts"] / f"{job['month']}.json", r["counts"])
    return job["month"]


def start_run(
    strategy: str,
    config: str,
    *,
    settings: Settings | None = None,
    scratch: bool = False,
    agent: str | None = None,
    repo: Path = REPO_ROOT,
    kind: str = "backtest",
) -> Path:
    """Create the run folder and manifest. Refuses uncommitted code unless ``scratch``."""
    settings = settings or load_settings()
    meta, cfg = load_config(strategy, config)
    git = registry.git_state(repo)
    registry.check_clean(git, scratch=scratch)
    store = DataStore(settings)
    period = cfg.get("period", {})
    start = date.fromisoformat(str(period.get("start", "2003-09-10")))
    end = date.fromisoformat(str(period.get("end", "2023-11-08")))
    sessions = store.sessions(start, end)  # raises if the period reaches the holdout
    agent = agent or os.environ.get("KINN_AGENT", "human")
    short = registry.config_hash(
        {
            "meta": meta,
            "config": cfg,
            "commit": git["commit"],
            "build": store.build_id,
            "kind": kind,
        }
    )
    run_id = registry.new_run_id(agent, strategy, short)
    run_dir = settings.runs_dir / run_id
    (run_dir / "parts").mkdir(parents=True)
    manifest = {
        "schema": registry.MANIFEST_SCHEMA,
        "run_id": run_id,
        "kind": kind,  # backtest | event_study
        "strategy": strategy,
        "family": meta.get("family", strategy),
        "prior_trials": int(meta.get("prior_trials", 0)),
        "config": config,
        "config_hash": short,
        "resolved_config": cfg,
        "cost_calibration": meta["cost_calibration"],
        "git": git,
        "scratch": scratch,
        "agent": agent,
        "data_build_id": store.build_id,
        "bars_id": store.info["bars_id"],
        "period": {"start": start.isoformat(), "end": end.isoformat()},
        "sessions": [d.isoformat() for d in sessions],
        "started_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "finished_at": None,
        "status": "running",
        "schemas": {"trades": registry.TRADES_SCHEMA, "equity": registry.EQUITY_SCHEMA,
                    "metrics": registry.METRICS_SCHEMA},
    }  # fmt: skip
    registry.write_json(run_dir / "manifest.json", manifest)
    return run_dir


def continue_run(
    run_dir: Path,
    *,
    settings: Settings | None = None,
    budget_seconds: float = float("inf"),
    workers: int = 1,
) -> bool:
    """Simulate pending months until done or out of time. Returns True when the run is complete."""
    settings = settings or load_settings()
    manifest = json.loads((run_dir / "manifest.json").read_text())
    months: dict[str, list[str]] = {}
    for day in manifest["sessions"]:
        months.setdefault(day[:7], []).append(day)
    parts = run_dir / "parts"
    pending = [m for m in months if not (parts / f"{m}.json").exists()]
    base = {
        "settings": {k: str(v) for k, v in dataclasses.asdict(settings).items()},
        "build_id": manifest["data_build_id"],
        "strategy": manifest["strategy"],
        "kind": manifest.get("kind", "backtest"),
        "config": manifest["resolved_config"],
        "cost_calibration": manifest["cost_calibration"],
        "parts": str(parts),
    }
    deadline = time.time() + budget_seconds
    jobs = [{**base, "month": m, "sessions": months[m], "deadline": deadline} for m in pending]
    if workers <= 1:
        for job in jobs:
            _guarded(job)
    else:
        with ProcessPoolExecutor(
            max_workers=workers, mp_context=multiprocessing.get_context("spawn")
        ) as pool:
            list(pool.map(_guarded, jobs))
    if any(not (parts / f"{m}.json").exists() for m in months):
        return False
    finalize(run_dir, settings=settings)
    return True


def _guarded(job: dict) -> str | None:
    """Skip the month if the time budget is already used (it stays pending)."""
    if time.time() > job["deadline"]:
        return None
    return run_month_multi(job) if "runs" in job else run_month(job)


def continue_sweep(
    run_dirs: list[Path],
    *,
    settings: Settings | None = None,
    budget_seconds: float = float("inf"),
    workers: int = 1,
) -> bool:
    """Continue several runs of one strategy over the same sessions, sharing the data loading.
    Returns True when every run is complete."""
    settings = settings or load_settings()
    manifests = [json.loads((d / "manifest.json").read_text()) for d in run_dirs]
    head = manifests[0]
    for m in manifests:
        if (m["strategy"], m["sessions"], m["data_build_id"]) != (
            head["strategy"], head["sessions"], head["data_build_id"]
        ):  # fmt: skip
            raise ValueError("a sweep needs one strategy, one period and one data build")
    months: dict[str, list[str]] = {}
    for day in head["sessions"]:
        months.setdefault(day[:7], []).append(day)
    deadline = time.time() + budget_seconds
    jobs = []
    for month, sessions in months.items():
        todo = [
            {"config": m["resolved_config"], "parts": str(d / "parts"), "kind": m.get("kind")}
            for d, m in zip(run_dirs, manifests, strict=True)
            if not (d / "parts" / f"{month}.json").exists()
        ]
        if todo:
            jobs.append({
                "settings": {k: str(v) for k, v in dataclasses.asdict(settings).items()},
                "build_id": head["data_build_id"], "strategy": head["strategy"],
                "cost_calibration": head["cost_calibration"], "month": month,
                "sessions": sessions, "runs": todo, "deadline": deadline,
            })  # fmt: skip
    if workers <= 1:
        for job in jobs:
            _guarded(job)
    else:
        with ProcessPoolExecutor(
            max_workers=workers, mp_context=multiprocessing.get_context("spawn")
        ) as pool:
            list(pool.map(_guarded, jobs))
    done = True
    for run_dir, manifest in zip(run_dirs, manifests, strict=True):
        if any(not (run_dir / "parts" / f"{m}.json").exists() for m in months):
            done = False
        elif manifest["status"] != "complete":
            finalize(run_dir, settings=settings)
    return done


def finalize(run_dir: Path, *, settings: Settings) -> None:
    from kinn.reporting import study_report, tearsheet

    manifest = json.loads((run_dir / "manifest.json").read_text())
    parts = run_dir / "parts"
    counts = dict.fromkeys(COUNT_KEYS, 0)
    tables = []
    for path in sorted(parts.glob("*.parquet")):
        tables.append(pq.read_table(path))
        for key, value in json.loads(path.with_suffix(".json").read_text()).items():
            counts[key] += value
    if manifest.get("kind") == "event_study":
        events = pa.concat_tables(tables) if tables else event_study.SCHEMA.empty_table()
        pq.write_table(events, run_dir / "events.parquet")
        summary = event_study.summarize(events)
        summary.update(schema="study-1", counts=counts)
        registry.write_json(run_dir / "study.json", summary)
    else:
        trades = [Trade(**row) for table in tables for row in table.to_pylist()]
        sessions = [date.fromisoformat(d) for d in manifest["sessions"]]
        breaker = manifest["resolved_config"].get("breaker")
        if breaker:
            trades, counts["paused_sessions"] = overlay.circuit_breaker(
                sessions, trades, loss=float(breaker["loss"]),
                window=int(breaker.get("window", 20)), pause=int(breaker.get("pause", 10)),
            )  # fmt: skip
        equity = float(
            manifest["resolved_config"].get("risk", {}).get("equity", RiskConfig().equity)
        )
        pq.write_table(_trades_table(trades), run_dir / "trades.parquet")
        pq.write_table(
            pa.table(metrics_module.daily_table(trades, sessions)), run_dir / "equity.parquet"
        )
        summary = metrics_module.summarize(trades, sessions, equity=equity, counts=counts)
        summary["schema"] = registry.METRICS_SCHEMA
        registry.write_json(run_dir / "metrics.json", summary)
    manifest["status"] = "complete"
    manifest["finished_at"] = datetime.now(UTC).isoformat(timespec="seconds")
    registry.write_json(run_dir / "manifest.json", manifest)
    if manifest.get("kind") == "event_study":
        study_report.write(run_dir)
    else:
        tearsheet.write(run_dir)
