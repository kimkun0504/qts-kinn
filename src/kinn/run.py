"""The one entry point for runs: ``kinn run <strategy> --config <name>``.

A run is resumable: sessions are simulated a month at a time into ``parts/`` and a run that
stops (time budget, crash) continues with ``--resume <run_id>``. Sessions are independent
(fixed-dollar sizing, flat every night), so the months can run in parallel.
"""

from __future__ import annotations

import dataclasses
import hashlib
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

from kinn.core.settings import HOLDOUT_START, Settings, load_settings
from kinn.core.types import Trade
from kinn.costs import model as cost_model
from kinn.data import holdout, inputs, seal
from kinn.data.inputs import info as input_info
from kinn.data.store import DataStore
from kinn.engine.intraday.data import load_day
from kinn.engine.intraday.extended import OPEN_PROXY_ASSUMPTIONS
from kinn.engine.intraday.simulator import FillConfig, UnresolvedPosition, simulate_day
from kinn.engine.intraday.strategy import (
    Strategy,
    check_no_lookahead,
    compute_features,
    day_signals,
    form4_sessions,
    form8k_sessions,
    form8k_timed_sessions,
    nbbo_replenishment_sessions,
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
    "unresolved_positions",
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


def check_nbbo_price_definition(source: dict, *, repo: Path = REPO_ROOT) -> str:
    """A quote acquisition population is valid only for the frozen price kernel."""
    commit = source["source_git"]["commit"]
    path = "strategies/bid_replenishment_reversal/strategy.py"
    original = registry._git(repo, "show", f"{commit}:{path}")
    current = (strategies_dir() / "bid_replenishment_reversal/strategy.py").read_text().strip()
    if not original or current != original:
        raise ValueError("NBBO price definition changed from the registered control commit")
    return hashlib.sha256(current.encode()).hexdigest()


def prepare_nbbo_plan(
    source_run: str,
    start: date,
    end: date,
    output: Path,
    *,
    settings: Settings | None = None,
    repo: Path = REPO_ROOT,
) -> Path:
    """Enumerate frozen price triggers for acquisition, without forward measurements.

    Only use for validation after the preregistered development gates pass. It is a data
    acquisition step; the one validation performance trial remains a separate kinn run.
    """
    settings = settings or load_settings()
    seal.check_range(start, end, source="NBBO price-only planning")
    if not source_run or any(x in source_run for x in ("/", "\\", "..")):
        raise ValueError("invalid NBBO reference run")
    manifest = json.loads((settings.runs_dir / source_run / "manifest.json").read_text())
    check_nbbo_price_definition({"source_git": manifest["git"]}, repo=repo)
    registry.check_clean(registry.git_state(repo), scratch=False)
    strategy = load_strategy("bid_replenishment_reversal", {"use_quotes": False})
    if getattr(strategy, "inputs", {}):
        raise ValueError("price-only planning must not read quote inputs")
    store = DataStore(settings, build_id=manifest["data_build_id"])
    candidates = []
    for day in store.sessions(start, end):
        view = load_day(store, day, strategy.universe).view
        signals = day_signals(strategy, view)
        check_no_lookahead(strategy, view, signals, sorted({s.minute for s in signals}))
        for signal in signals:
            bars = view.symbols[signal.symbol]
            candidates.append(
                {
                    "day": day,
                    "symbol": signal.symbol,
                    "permaticker": int(bars.permaticker),
                    "signal_minute": signal.minute,
                    "prev_close": bars.prior["prev_close"],
                    "adv20_prev": bars.prior["adv20_prev"],
                }
            )
    return inputs.write_nbbo_price_plan(
        settings,
        source_run,
        candidates,
        {"start": start.isoformat(), "end": end.isoformat()},
        output,
    )


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
    store = DataStore(
        settings, build_id=job["build_id"], unseal=job.get("unseal", False),
        inputs=job.get("inputs"),
    )  # fmt: skip
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
            "trades": [], "events": [], "unresolved": [], "counts": dict.fromkeys(COUNT_KEYS, 0),
        })  # fmt: skip
    first = runs[0]["strategy"]
    if any(nbbo_replenishment_sessions(r["strategy"]) for r in runs):
        source = (strategies_dir() / job["strategy"] / "strategy.py").read_text().strip()
        if hashlib.sha256(source.encode()).hexdigest() != job.get("nbbo_price_definition_sha256"):
            raise ValueError("NBBO price definition changed after run creation")
    if any(r["strategy"].universe.where() != first.universe.where() for r in runs):
        raise ValueError("configs run together must share one universe")
    share_features = all(
        [f.name for f in r["strategy"].features] == [f.name for f in first.features] for r in runs
    )
    insider_sessions = max(form4_sessions(r["strategy"]) for r in runs)
    report_sessions = max(form8k_sessions(r["strategy"]) for r in runs)
    timed_sessions = max(form8k_timed_sessions(r["strategy"]) for r in runs)
    nbbo_sessions = max(nbbo_replenishment_sessions(r["strategy"]) for r in runs)
    for day in (date.fromisoformat(d) for d in job["sessions"]):
        data = load_day(
            store, day, first.universe,
            form4_sessions=insider_sessions, form8k_sessions=report_sessions,
            form8k_timed_sessions=timed_sessions,
            nbbo_replenishment_sessions=nbbo_sessions,
        )  # fmt: skip
        shared = compute_features(first, data.view) if share_features and len(runs) > 1 else None
        for r in runs:
            strategy, counts = r["strategy"], r["counts"]
            if shared is None:
                signals = day_signals(strategy, data.view)
            else:
                signals = strategy.signals(data.view, shared)
            rng = random.Random(f"{r['seed']}:{day.isoformat()}")
            if signals and rng.random() < r["rate"]:
                bounds = r["fills"].replay_bounds(data.view.open_minute, data.view.close_minute)
                cuts = [rng.randrange(*bounds)]
                if r["fills"].session == "extended_v1":
                    cuts.extend(c for s in signals for c in (s.minute - 1, s.minute))
                check_no_lookahead(strategy, data.view, signals, sorted(set(cuts)))
                counts["lookahead_checks"] += 1
            if r["study"]:
                counts["signals"] += len(signals)
                for signal in signals:
                    if r["fills"].session == "extended_v1":
                        row = event_study.measure_extended(
                            day,
                            data.view.symbols[signal.symbol],
                            signal,
                            config=r["fills"],
                            costs=costs,
                            position_dollars=r["risk"].position_dollars * signal.weight,
                        )
                    else:
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
                        counts["unresolved_positions"] += int(row.get("held", 0) > 0)
                continue
            result = simulate_day(data, signals, risk=r["risk"], config=r["fills"], costs=costs)
            r["trades"].extend(result.trades)
            r["unresolved"].extend(dataclasses.asdict(p) for p in result.unresolved)
            counts["unresolved_positions"] += len(result.unresolved)
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
            schema = (
                event_study.EXTENDED_SCHEMA
                if r["fills"].session == "extended_v1"
                else event_study.SCHEMA
            )
            table = pa.Table.from_pylist(r["events"], schema=schema)
        else:
            table = _trades_table(r["trades"])
            if r["fills"].session == "extended_v1":
                exposure_parts = r["parts"] / "unresolved"
                exposure_parts.mkdir(exist_ok=True)
                exposure_tmp = exposure_parts / f"{job['month']}.parquet.tmp"
                pq.write_table(_unresolved_table(r["unresolved"]), exposure_tmp)
                os.replace(exposure_tmp, exposure_parts / f"{job['month']}.parquet")
        pq.write_table(table, tmp)
        os.replace(tmp, r["parts"] / f"{job['month']}.parquet")
        registry.write_json(r["parts"] / f"{job['month']}.json", r["counts"])
    return job["month"]


def _unresolved_table(rows: list[dict]) -> pa.Table:
    floats = {
        "notional",
        "mark_price",
        "marked_gross",
        "commission",
        "fees",
        "slippage",
        "marked_net",
        "marked_net_2x",
    }
    schema = pa.schema(
        [
            (
                f.name,
                pa.date32()
                if f.name == "day"
                else pa.string()
                if f.name == "symbol"
                else pa.float64()
                if f.name in floats
                else pa.int64(),
            )
            for f in dataclasses.fields(UnresolvedPosition)
        ]
    )
    return pa.Table.from_pylist(rows, schema=schema)


def start_run(
    strategy: str,
    config: str,
    *,
    settings: Settings | None = None,
    scratch: bool = False,
    agent: str | None = None,
    repo: Path = REPO_ROOT,
    kind: str = "backtest",
    unseal: bool = False,
) -> Path:
    """Create the run folder and manifest. Refuses uncommitted code unless ``scratch``.

    ``unseal=True`` runs on the owner's unsealed build: the one run on the holdout. It needs
    the owner's token (the data layer refuses otherwise) and is marked in the manifest."""
    settings = settings or load_settings()
    meta, cfg = load_config(strategy, config)
    fills = FillConfig(**cfg.get("fills", {}))
    execution = dataclasses.asdict(fills) if fills.session == "extended_v1" else None
    if execution and cfg.get("breaker"):
        raise ValueError("extended_v1 does not support a post-hoc circuit breaker")
    git = registry.git_state(repo)
    registry.check_clean(git, scratch=scratch)
    store = DataStore(settings, unseal=unseal)
    period = cfg.get("period", {})
    start = date.fromisoformat(str(period.get("start", "2003-09-10")))
    end = date.fromisoformat(str(period.get("end", "2023-11-08")))
    sessions = store.sessions(start, end)  # raises if the period reaches the holdout
    agent = agent or os.environ.get("KINN_AGENT", "human")
    # Versioned inputs the strategy declares: the run is pinned to today's version of each.
    used = {}
    declared = load_strategy(strategy, cfg.get("params", {}))
    if form4_sessions(declared):
        found = input_info(settings, "form4")
        used["form4"] = {k: found[k] for k in ("input_id", "version", "last_filed", "rows")}
    if form8k_sessions(declared):  # read from the data build this run is pinned to
        found = store.form8k_info()
        used["form8k"] = {k: found[k] for k in ("input_id", "version", "last_filed", "rows")}
    if form8k_timed_sessions(declared):
        found = store.check_timed_coverage(start, end)
        used["form8k_timed"] = {
            k: found[k]
            for k in (
                "input_id",
                "version",
                "last_filed",
                "rows",
                "data_build_id",
                "coverage_start",
                "coverage_end",
                "coverage_basis",
                "first_accepted_day",
                "last_accepted_day",
            )
        }
    if nbbo_replenishment_sessions(declared):
        found = store.check_nbbo_coverage(start, end)
        definition_hash = check_nbbo_price_definition(found, repo=repo)
        used["nbbo_replenishment"] = {**found, "price_definition_sha256": definition_hash}
    short = registry.config_hash(
        {
            "meta": meta,
            "config": cfg,
            "commit": git["commit"],
            "build": store.build_id,
            "kind": kind,
            **({"execution": execution} if execution else {}),
            **({"execution_assumptions": OPEN_PROXY_ASSUMPTIONS} if execution else {}),
            **({"inputs": {k: v["input_id"] for k, v in used.items()}} if used else {}),
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
    if used:
        manifest["inputs"] = used
    if execution:
        manifest["execution"] = execution
        manifest["execution_assumptions"] = dict(OPEN_PROXY_ASSUMPTIONS)
    if unseal:
        manifest["unsealed"] = True
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
        "unseal": bool(manifest.get("unsealed", False)),
        "inputs": {k: v["input_id"] for k, v in manifest.get("inputs", {}).items()},
        "nbbo_price_definition_sha256": manifest.get("inputs", {})
        .get("nbbo_replenishment", {})
        .get("price_definition_sha256"),
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


def rehearse(
    settings: Settings, strategy: str, config: str, *, workers: int = 4, against: str | None = None
) -> dict:
    """Run a config whose period is before the seal through the unsealed build, as a scratch
    run (not a trial), and compare its trades with the research run of the same config. The
    one holdout run uses this same path, so equal trades here mean the path is sound."""
    _, cfg = load_config(strategy, config)
    if date.fromisoformat(str(cfg["period"]["end"])) >= HOLDOUT_START:
        raise ValueError("a rehearsal uses a period that ends before the seal")
    if against is None:
        earlier = [
            m["run_id"]
            for m in registry.read_manifests(settings.runs_dir)
            if m.get("strategy") == strategy and m.get("config") == config
            and m.get("status") == "complete" and not m.get("scratch") and not m.get("unsealed")
        ]  # fmt: skip
        if not earlier:
            raise ValueError(f"no finished research run of {strategy} {config} to compare with")
        against = earlier[-1]
    run_dir = start_run(strategy, config, settings=settings, scratch=True, unseal=True)
    continue_run(run_dir, settings=settings, workers=workers)
    return {"run": run_dir.name, "against": against,
            **holdout.compare_trades(settings.runs_dir / against, run_dir,
                                    explained=holdout.explained_additions(settings))}  # fmt: skip


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
        if m.get("inputs", {}) != head.get("inputs", {}):
            raise ValueError("a sweep needs one pinned input set")
    if any(m.get("unsealed") for m in manifests):
        raise ValueError("the holdout takes one run of one frozen variant, never a sweep")
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
                "inputs": {k: v["input_id"] for k, v in head.get("inputs", {}).items()},
                "nbbo_price_definition_sha256": head.get("inputs", {}).get(
                    "nbbo_replenishment", {}
                ).get("price_definition_sha256"),
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
        if manifest.get("execution"):
            summary["execution_assumptions"] = manifest.get(
                "execution_assumptions", dict(OPEN_PROXY_ASSUMPTIONS)
            )
            expected = [parts / "unresolved" / p.name for p in sorted(parts.glob("*.parquet"))]
            if any(not p.exists() for p in expected):
                raise ValueError("extended run is missing unresolved-exposure part files")
            exposure = [row for p in expected for row in pq.read_table(p).to_pylist()]
            if len(exposure) != counts["unresolved_positions"]:
                raise ValueError("unresolved exposure count does not match the part files")
            pq.write_table(_unresolved_table(exposure), run_dir / "unresolved.parquet")
            summary["execution_risk"] = {
                "eligible": not exposure,
                "unresolved_positions": len(exposure),
                "held_shares": sum(p["held"] for p in exposure),
                "sum_last_marked_exposure": sum(p["held"] * p["mark_price"] for p in exposure),
                "unresolved_marked_net_1x": sum(p["marked_net"] for p in exposure),
                "unresolved_marked_net_2x": sum(p["marked_net_2x"] for p in exposure),
                "statistics_scope": (
                    "completed trades only; unresolved exposure invalidates the portfolio"
                ),
            }
            marked = metrics_module.daily_table(trades, sessions)
            marked.update(unresolved_positions=[], held_shares=[], marked_exposure=[])
            for i, day in enumerate(sessions):
                positions = [p for p in exposure if p["day"] == day]
                marked["unresolved_positions"].append(len(positions))
                marked["held_shares"].append(sum(p["held"] for p in positions))
                marked["marked_exposure"].append(
                    sum(p["held"] * p["mark_price"] for p in positions)
                )
                marked["gross"][i] += sum(p["marked_gross"] for p in positions)
                marked["notional"][i] += sum(p["notional"] for p in positions)
                marked["net"][i] += sum(p["marked_net"] for p in positions)
                marked["net_2x"][i] += sum(p["marked_net_2x"] for p in positions)
            import numpy as np

            marked["cum_net"] = np.cumsum(marked["net"]).tolist()
            marked["cum_net_2x"] = np.cumsum(marked["net_2x"]).tolist()
            pq.write_table(pa.table(marked), run_dir / "marked_equity.parquet")
        summary["schema"] = registry.METRICS_SCHEMA
        registry.write_json(run_dir / "metrics.json", summary)
    manifest["status"] = "complete"
    manifest["finished_at"] = datetime.now(UTC).isoformat(timespec="seconds")
    registry.write_json(run_dir / "manifest.json", manifest)
    if manifest.get("kind") == "event_study":
        study_report.write(run_dir)
    else:
        tearsheet.write(run_dir)
