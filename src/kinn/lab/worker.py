"""The Lab's worker process: ``python -m kinn.lab.worker <run folder>``. Started by the
Workbench for each run (decision 0023); it can also be run by hand to repeat a run.

``KINN_LAB_TIME_LIMIT`` sets the run's time limit in minutes (default 30; 0 for none)."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from kinn.lab.runner import run

DEFAULT_MINUTES = 30.0


def time_limit() -> float | None:
    try:
        minutes = float(os.environ.get("KINN_LAB_TIME_LIMIT", DEFAULT_MINUTES))
    except ValueError:
        minutes = DEFAULT_MINUTES
    return minutes * 60 if minutes > 0 else None


if __name__ == "__main__":
    if len(sys.argv) != 2 or not (Path(sys.argv[1]) / "request.json").exists():
        raise SystemExit("usage: python -m kinn.lab.worker <run folder with request.json>")
    run(Path(sys.argv[1]), time_limit=time_limit())
