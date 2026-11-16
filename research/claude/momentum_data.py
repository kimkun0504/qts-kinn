"""Data for the intraday momentum study (strategies/intraday_momentum/HYPOTHESIS.md): for every
development session, each symbol's opening range (first 5 and first 15 minutes) and the
regular-session one-minute bars of QQQ and SPY. Resumable, one file pair per month.

    uv run python research/claude/momentum_data.py --budget 150 --workers 3
"""

from __future__ import annotations

import argparse
import time
from concurrent.futures import ProcessPoolExecutor
from datetime import date
from pathlib import Path

import duckdb

from kinn.core.settings import Settings, load_settings
from kinn.data.store import DataStore
from kinn.validation.targets import DEVELOPMENT_END

START = date(2003, 9, 10)
ETFS = ("SPY", "QQQ", "QQQQ")  # QQQ traded as QQQQ from 2004-12 to 2011-03


def out_dir(settings: Settings) -> Path:
    return settings.data_dir / "research" / "momentum"


def _range(prefix: str, last: int) -> str:
    inside = f"filter (minute_et between 570 and {last})"
    return (f"sum(volume) {inside} as {prefix}_volume, max(high) {inside} as {prefix}_high, "
            f"min(low) {inside} as {prefix}_low, "
            f"arg_max(close, minute_et) {inside} as {prefix}_close")  # fmt: skip


def month_job(job: dict) -> str | None:
    if time.time() > job["deadline"]:
        return None
    base = Path(job["out"])
    base.mkdir(parents=True, exist_ok=True)
    files = ", ".join(f"'{f}'" for f in job["files"])
    con = duckdb.connect()
    con.execute("set threads=1; set memory_limit='900MB'")
    day = "cast(bar_start as date) as day"
    tmp = base / f"{job['month']}.etf.tmp"
    con.execute(
        f"""copy (select {day}, symbol, minute_et as minute, open, high, low, close, volume
                  from read_parquet([{files}])
                  where symbol in {ETFS} and minute_et between 570 and 959
                  order by 1, 2, 3) to '{tmp}' (format parquet)"""
    )
    tmp.replace(base / f"{job['month']}.etf.parquet")
    tmp = base / f"{job['month']}.or.tmp"
    con.execute(
        f"""copy (select cast(bar_start as date) as day, symbol,
                         arg_min(open, minute_et) as or_open, min(minute_et) as first_minute,
                         {_range("or5", 574)}, {_range("or15", 584)}
                  from read_parquet([{files}]) where minute_et between 570 and 584
                  group by 1, 2 order by 1, 2) to '{tmp}' (format parquet)"""
    )
    tmp.replace(base / f"{job['month']}.or.parquet")  # written last: marks the month done
    return job["month"]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--budget", type=float, default=150.0)
    parser.add_argument("--workers", type=int, default=3)
    args = parser.parse_args()
    settings = load_settings()
    store = DataStore(settings)
    months: dict[str, list[str]] = {}
    for row in store.calendar(START, DEVELOPMENT_END).to_pylist():
        d = row["date"]
        path = store.bars_root / "minute" / f"year={d.year}" / f"{d.isoformat()}.parquet"
        months.setdefault(d.isoformat()[:7], []).append(str(path))
    base = out_dir(settings)
    pending = [m for m in months if not (base / f"{m}.or.parquet").exists()]
    deadline = time.time() + args.budget
    jobs = [{"month": m, "files": months[m], "out": str(base), "deadline": deadline}
            for m in pending]  # fmt: skip
    with ProcessPoolExecutor(args.workers) as pool:
        done = sum(r is not None for r in pool.map(month_job, jobs))
    print(f"months {len(months)}, done now {done}, pending {len(pending) - done}")


if __name__ == "__main__":
    main()
