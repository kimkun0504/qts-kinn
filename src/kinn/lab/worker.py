"""The Lab's worker process: ``python -m kinn.lab.worker <run folder>``. Started by the
Workbench for each run (decision 0023); it can also be run by hand to repeat a run."""

from __future__ import annotations

import sys
from pathlib import Path

from kinn.lab.runner import run

if __name__ == "__main__":
    if len(sys.argv) != 2 or not (Path(sys.argv[1]) / "request.json").exists():
        raise SystemExit("usage: python -m kinn.lab.worker <run folder with request.json>")
    run(Path(sys.argv[1]))
