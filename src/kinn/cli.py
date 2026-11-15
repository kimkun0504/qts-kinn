"""The ``kinn`` command."""

from __future__ import annotations

import argparse
import time
from importlib.metadata import version

from kinn.core.settings import HOLDOUT_START, load_settings


def _paths(_args: argparse.Namespace) -> int:
    settings = load_settings()
    print(f"raw (read-only)  {settings.raw_dir}")
    print(f"derived data     {settings.data_dir}")
    print(f"runs             {settings.runs_dir}")
    print(f"holdout starts   {HOLDOUT_START.isoformat()} (sealed)")
    return 0


def _data_bars(args: argparse.Namespace) -> int:
    from kinn.data import build

    settings = load_settings()
    started = time.monotonic()
    done, pending = build.build_bars(settings, budget_seconds=args.budget, workers=args.workers)
    paths = build.paths(settings)
    took = time.monotonic() - started
    print(f"bars {paths.bars_id}: {done} steps done in {took:.0f}s, {pending} pending")
    return 0 if pending == 0 else 3


def _data_build(args: argparse.Namespace) -> int:
    from kinn.data import build

    build_id, pending = build.build_tables(load_settings(), budget_seconds=args.budget)
    print(f"build {build_id}: " + (f"pending: {', '.join(pending)}" if pending else "complete"))
    return 0 if not pending else 3


def _data_audit(_args: argparse.Namespace) -> int:
    from kinn.data import audit

    print(f"audit written to {audit.write(load_settings())}")
    return 0


def _run(args: argparse.Namespace) -> int:
    from pathlib import Path

    from kinn import run as runner
    from kinn.registry import runs as registry

    settings = load_settings()
    if args.resume:
        run_dir = settings.runs_dir / args.resume
    else:
        if not args.strategy or not args.config:
            raise SystemExit("kinn run needs <strategy> --config <name>, or --resume <run_id>")
        try:
            run_dir = runner.start_run(
                args.strategy,
                args.config,
                settings=settings,
                scratch=args.scratch,
                kind="event_study" if args.study else "backtest",
            )
        except registry.DirtyTreeError as error:
            raise SystemExit(f"refused: {error}") from error
    done = runner.continue_run(
        Path(run_dir), settings=settings, budget_seconds=args.budget, workers=args.workers
    )
    print(f"run {run_dir.name}: " + ("complete" if done else "paused; continue with --resume"))
    if done:
        report = run_dir / "tearsheet.md"
        print((report if report.exists() else run_dir / "study.md").read_text())
    return 0 if done else 3


def _book(args: argparse.Namespace) -> int:
    import json

    from kinn import book_run
    from kinn.registry import runs as registry

    settings = load_settings()
    if args.resume:
        run_dir = settings.runs_dir / args.resume
    else:
        if not args.config:
            raise SystemExit("kinn book needs <config> (a file in books/), or --resume <run_id>")
        try:
            run_dir = book_run.start_run(args.config, settings=settings, scratch=args.scratch)
        except registry.DirtyTreeError as error:
            raise SystemExit(f"refused: {error}") from error
    done = book_run.continue_run(run_dir, settings=settings, budget_seconds=args.budget)
    print(f"run {run_dir.name}: " + ("complete" if done else "paused; continue with --resume"))
    if done:
        m = json.loads((run_dir / "metrics.json").read_text())
        for label in ("slippage_1x", "slippage_2x"):
            s = m[label]
            print(
                f"{label}: total {s['total_return']:+.1%}, a year {s['annual_return']:+.1%}, "
                f"Sharpe {s['sharpe']:.2f}, t {s['t_stat_daily']:.2f}, "
                f"worst drawdown {s['max_drawdown_pct']:.1%}"
            )
    return 0 if done else 3


def _sweep(args: argparse.Namespace) -> int:
    import json
    from pathlib import Path

    from kinn import run as runner
    from kinn.registry import runs as registry

    settings = load_settings()
    folder = settings.runs_dir / "_sweeps"
    if args.resume:
        sweep_id = args.resume
        run_ids = json.loads((folder / f"{sweep_id}.json").read_text())["runs"]
    else:
        if not args.strategy:
            raise SystemExit("kinn sweep needs <strategy> --configs a,b,... or --resume <id>")
        configs_dir = runner.strategies_dir() / args.strategy / "configs"
        names = (
            args.configs.split(",")
            if args.configs
            else sorted(p.stem for p in configs_dir.glob("*.yaml"))
        )
        try:
            run_ids = [
                runner.start_run(args.strategy, name, settings=settings, scratch=args.scratch).name
                for name in names
            ]
        except registry.DirtyTreeError as error:
            raise SystemExit(f"refused: {error}") from error
        sweep_id = run_ids[0].split("_")[0] + f"_{args.strategy}_{len(run_ids)}"
        folder.mkdir(parents=True, exist_ok=True)
        registry.write_json(folder / f"{sweep_id}.json", {"runs": run_ids})
        print(f"sweep {sweep_id}: {len(run_ids)} runs, each a counted trial")
    done = runner.continue_sweep(
        [Path(settings.runs_dir / r) for r in run_ids], settings=settings,
        budget_seconds=args.budget, workers=args.workers,
    )  # fmt: skip
    print(f"sweep {sweep_id}: " + ("complete" if done else "paused; continue with --resume"))
    return 0 if done else 3


def _abandon(args: argparse.Namespace) -> int:
    from kinn.registry import runs as registry

    settings = load_settings()
    for run_id in args.run_ids:
        registry.abandon(settings.runs_dir, run_id, args.reason)
        print(f"abandoned (not a trial): {run_id}")
    return 0


def _runs(args: argparse.Namespace) -> int:
    import duckdb

    from kinn.registry import runs as registry

    settings = load_settings()
    index = registry.rebuild_index(settings.runs_dir)
    con = duckdb.connect(str(index), read_only=True)
    rows = con.execute(
        """select run_id, status, scratch, trades, round(100 * mean_return_1x, 3),
                  round(100 * mean_return_2x, 3) from runs order by started_at"""
    ).fetchall()
    print("run_id | status | scratch | trades | net/trade 1x % | net/trade 2x %")
    for row in rows:
        print(" | ".join("" if v is None else str(v) for v in row))
    families = con.execute(
        "select family, count(*) from runs where not scratch and status <> 'abandoned' "
        "group by 1 order by 1"
    ).fetchall()
    for family, count in families:
        print(f"family {family}: {count} counted runs (plus any declared prior looks)")
    return 0


def _quotes_plan(args: argparse.Namespace) -> int:
    from kinn.data import quotes

    settings = load_settings()
    events = settings.runs_dir / args.run / "events.parquet"
    out = settings.data_dir / "quotes_sample" / args.run
    path = quotes.plan(events, out, per_cell=args.per_cell)
    print(f"{len(quotes.read_windows(path))} events planned: {path}")
    print(f"The owner now runs: uv run python tools/owner/download_quotes.py {path}")
    return 0


def _quotes_report(args: argparse.Namespace) -> int:
    from kinn.costs import model as cost_model
    from kinn.data import quotes
    from kinn.registry import runs as registry

    settings = load_settings()
    folder = settings.data_dir / "quotes_sample" / args.run
    raw = settings.raw_dir / "massive" / "quotes_sample" / args.run
    result = quotes.measure(
        quotes.read_windows(folder / "windows.csv"),
        raw,
        cost_model.load(args.costs).half_spread_bps,
    )
    registry.write_json(folder / "report.json", result)
    text = quotes.render(result, args.run)
    (folder / "report.md").write_text(text)
    print(text)
    return 0


def _quotes_passive(args: argparse.Namespace) -> int:
    from kinn import tick_study
    from kinn.registry import runs as registry

    try:
        run_dir = tick_study.passive_entry(
            load_settings(), strategy=args.strategy, source_run=args.run, scratch=args.scratch
        )
    except registry.DirtyTreeError as error:
        raise SystemExit(f"refused: {error}") from error
    print((run_dir / "tick_study.md").read_text())
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="kinn", description=__doc__)
    parser.add_argument("--version", action="version", version=f"kinn {version('kinn')}")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("paths", help="show the folders Kinn uses and the holdout date").set_defaults(
        func=_paths
    )

    run = sub.add_parser("run", help="run a strategy: kinn run <strategy> --config <name>")
    run.add_argument("strategy", nargs="?")
    run.add_argument("--config")
    run.add_argument("--scratch", action="store_true", help="allow uncommitted code; not counted")
    run.add_argument("--study", action="store_true", help="event study instead of a backtest")
    run.add_argument("--resume", metavar="RUN_ID", help="continue a paused run")
    run.add_argument("--budget", type=float, default=float("inf"), help="seconds before pausing")
    run.add_argument("--workers", type=int, default=1)
    run.set_defaults(func=_run)
    book = sub.add_parser("book", help="run a multi-day book: kinn book <config in books/>")
    book.add_argument("config", nargs="?")
    book.add_argument("--scratch", action="store_true")
    book.add_argument("--resume", metavar="RUN_ID")
    book.add_argument("--budget", type=float, default=float("inf"), help="seconds, then pause")
    book.set_defaults(func=_book)
    sweep = sub.add_parser("sweep", help="run several configs of one strategy together")
    sweep.add_argument("strategy", nargs="?")
    sweep.add_argument("--configs", help="comma-separated config names (default: all)")
    sweep.add_argument("--scratch", action="store_true")
    sweep.add_argument("--resume", metavar="SWEEP_ID")
    sweep.add_argument("--budget", type=float, default=float("inf"))
    sweep.add_argument("--workers", type=int, default=1)
    sweep.set_defaults(func=_sweep)
    drop = sub.add_parser("abandon", help="mark unfinished runs as abandoned (never finished ones)")
    drop.add_argument("run_ids", nargs="+")
    drop.add_argument("--reason", required=True)
    drop.set_defaults(func=_abandon)
    sub.add_parser("runs", help="rebuild the run index and list runs").set_defaults(func=_runs)

    quote = sub.add_parser("quotes", help="quote sample around a study's events").add_subparsers(
        dest="quotes_command", required=True
    )
    q_plan = quote.add_parser("plan", help="choose the events and write the windows to fetch")
    q_plan.add_argument("--run", required=True, help="an event-study run id")
    q_plan.add_argument("--per-cell", type=int, default=70, help="events per bucket and period")
    q_plan.set_defaults(func=_quotes_plan)
    q_report = quote.add_parser("report", help="compare real spreads with the cost model")
    q_report.add_argument("--run", required=True)
    q_report.add_argument("--costs", default="ibkr_pro_tiered")
    q_report.set_defaults(func=_quotes_report)

    q_passive = quote.add_parser("passive", help="test a resting bid on the quote sample")
    q_passive.add_argument("--run", required=True, help="the event-study run the sample is from")
    q_passive.add_argument("--strategy", default="intraday_rebound_passive")
    q_passive.add_argument("--scratch", action="store_true")
    q_passive.set_defaults(func=_quotes_passive)

    data = sub.add_parser("data", help="build and audit processed data").add_subparsers(
        dest="data_command", required=True
    )
    bars = data.add_parser("bars", help="convert Massive bars to Parquet (resumable)")
    bars.add_argument(
        "--budget", type=float, default=3600.0, help="seconds to work before stopping"
    )
    bars.add_argument("--workers", type=int, default=4)
    bars.set_defaults(func=_data_bars)

    tables = data.add_parser("build", help="build the security master and daily panel (resumable)")
    tables.add_argument("--budget", type=float, default=3600.0)
    tables.set_defaults(func=_data_build)

    data.add_parser("audit", help="write the audit report for the current build").set_defaults(
        func=_data_audit
    )

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
