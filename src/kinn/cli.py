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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="kinn", description=__doc__)
    parser.add_argument("--version", action="version", version=f"kinn {version('kinn')}")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("paths", help="show the folders Kinn uses and the holdout date").set_defaults(
        func=_paths
    )

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
