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
        "select family, count(*) from runs where not scratch group by 1 order by 1"
    ).fetchall()
    for family, count in families:
        print(f"family {family}: {count} counted runs (plus any declared prior looks)")
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
    sub.add_parser("runs", help="rebuild the run index and list runs").set_defaults(func=_runs)

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
