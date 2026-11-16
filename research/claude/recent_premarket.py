"""Premarket states for family 9 of the search (strategies/recent_search/HYPOTHESIS.md): at
07:00, 08:00 and 09:00, the last price, dollar volume and trades so far, and the first print
at or after that time. Resumable by month.

    uv run python research/claude/recent_premarket.py --budget 95 --workers 4
"""

from __future__ import annotations

import argparse
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import duckdb

from kinn.core.settings import load_settings
from kinn.data.store import DataStore
from recent_features import END, START

TIMES = (420, 480, 540)


def month_job(job: dict) -> str | None:
    if time.time() > job["deadline"]:
        return None
    out = Path(job["out"])
    out.mkdir(parents=True, exist_ok=True)
    files = ", ".join(f"'{f}'" for f in job["files"])
    parts = []
    for t in TIMES:
        parts += [
            f"arg_max(close, m) filter (m < {t}) as c{t}",
            f"sum(close * volume) filter (m < {t}) as dv{t}",
            f"sum(transactions) filter (m < {t}) as n{t}",
            f"arg_min(open, m) filter (m >= {t}) as e{t}",
            f"min(m) filter (m >= {t}) as em{t}",
        ]
    con = duckdb.connect()
    con.execute("set threads=1; set memory_limit='800MB'")
    tmp = out / f"{job['month']}.tmp"
    con.execute(
        f"""copy (select cast(bar_start as date) as day, symbol, {", ".join(parts)}
                  from (select bar_start, symbol, minute_et as m, open, close, volume,
                               transactions
                        from read_parquet([{files}]) where minute_et < 570)
                  group by 1, 2 having count(*) >= 3 order by 1, 2)
            to '{tmp}' (format parquet, compression zstd)"""
    )
    tmp.replace(out / f"{job['month']}.parquet")
    return job["month"]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--budget", type=float, default=95.0)
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()
    settings = load_settings()
    store = DataStore(settings)
    months: dict[str, list[str]] = {}
    for row in store.calendar(START, END).to_pylist():
        d = row["date"]
        if row["close_minute_et"] == 960:
            path = store.bars_root / "minute" / f"year={d.year}" / f"{d.isoformat()}.parquet"
            months.setdefault(d.isoformat()[:7], []).append(str(path))
    out = settings.data_dir / "research" / "recent" / "premarket"
    pending = [m for m in months if not (out / f"{m}.parquet").exists()]
    deadline = time.time() + args.budget
    jobs = [{"month": m, "files": months[m], "out": str(out), "deadline": deadline}
            for m in pending]  # fmt: skip
    with ProcessPoolExecutor(args.workers) as pool:
        done = sum(r is not None for r in pool.map(month_job, jobs))
    print(f"months {len(months)}, done now {done}, pending {len(pending) - done}")


if __name__ == "__main__":
    main()
