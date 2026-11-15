"""The ``kinn`` command. ``kinn run`` arrives in Phase 2; for now it only reports its settings."""

from __future__ import annotations

import argparse
from importlib.metadata import version

from kinn.core.settings import HOLDOUT_START, load_settings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="kinn", description=__doc__)
    parser.add_argument("--version", action="version", version=f"kinn {version('kinn')}")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("paths", help="show the folders Kinn reads and writes, and the holdout date")
    parser.parse_args(argv)

    settings = load_settings()
    print(f"raw (read-only)  {settings.raw_dir}")
    print(f"derived data     {settings.data_dir}")
    print(f"runs             {settings.runs_dir}")
    print(f"holdout starts   {HOLDOUT_START.isoformat()} (sealed)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
