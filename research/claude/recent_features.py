"""Stock-day features for the search on recent years (strategies/recent_search/HYPOTHESIS.md):
what was known before the open, the premarket, and the state at ten times of day, with the
first print after each time and the official close. Full sessions only. Resumable by month.

    uv run python research/claude/recent_features.py --budget 150 --workers 3
"""

from __future__ import annotations

import argparse
import time
from concurrent.futures import ProcessPoolExecutor
from datetime import date
from pathlib import Path

import duckdb

from kinn.core.settings import load_settings
from kinn.data.store import DataStore

START, END = date(2018, 1, 2), date(2023, 11, 8)
TIMES = (575, 585, 600, 630, 660, 720, 780, 840, 900, 930)


def columns() -> str:
    parts = [
        "sum(volume) filter (m < 570) as pm_volume",
        "sum(close * volume) filter (m < 570) as pm_dollar",
        "sum(transactions) filter (m < 570) as pm_trades",
        "max(high) filter (m < 570) as pm_high",
        "min(low) filter (m < 570) as pm_low",
        "arg_max(close, m) filter (m < 570) as pm_last",
        "arg_min(open, m) filter (m >= 570) as open_px",
        "min(m) filter (m >= 570) as first_minute",
        "sum(volume) filter (m >= 570) as day_volume",
        "sum(transactions) filter (m >= 570) as day_trades",
    ]
    for t in TIMES:
        before, after = f"filter (m >= 570 and m < {t})", f"filter (m >= {t})"
        parts += [
            f"arg_max(close, m) {before} as c{t}",
            f"sum(volume) {before} as v{t}",
            f"sum(transactions) {before} as n{t}",
            f"sum(volume * (high + low + close) / 3) {before} as pv{t}",
            f"max(high) {before} as hi{t}",
            f"min(low) {before} as lo{t}",
            f"arg_min(open, m) {after} as e{t}",
            f"min(m) {after} as em{t}",
            f"max(high) {after} as hia{t}",
            f"min(low) {after} as loa{t}",
        ]
    return ",\n".join(parts)


def month_job(job: dict) -> str | None:
    if time.time() > job["deadline"]:
        return None
    out = Path(job["out"])
    out.mkdir(parents=True, exist_ok=True)
    files = ", ".join(f"'{f}'" for f in job["files"])
    days = ", ".join(f"DATE '{d}'" for d in job["days"])
    con = duckdb.connect()
    con.execute("set threads=1; set memory_limit='1000MB'")
    tmp = out / f"{job['month']}.tmp"
    con.execute(
        f"""copy (
            with bars as (
                select cast(bar_start as date) as day, symbol, minute_et as m, open, high, low,
                       close, volume, transactions
                from read_parquet([{files}]) where minute_et < 960),
            agg as (select day, symbol, {columns()} from bars group by 1, 2)
            select p.date as day, p.symbol, p.permaticker, p.category, p.exchange,
                   p.close as official_close, p.prev_close, p.prev_date, p.split_ratio,
                   p.adv20_prev, p.sessions_prior, p.marketcap_prev, p.filings_prev,
                   p.ret60_prev, p.high as d_high, p.low as d_low, p.volume as d_volume,
                   a.* exclude (day, symbol)
            from read_parquet('{job["panel"]}/panel/*.parquet') p
            join agg a on a.day = p.date and a.symbol = p.symbol
            where p.date in ({days}) and p.prev_close >= 1 and p.adv20_prev >= 250000
              and p.category like '%Common Stock%'
            order by 1, 2) to '{tmp}' (format parquet, compression zstd)"""
    )
    tmp.replace(out / f"{job['month']}.parquet")
    return job["month"]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--budget", type=float, default=150.0)
    parser.add_argument("--workers", type=int, default=3)
    args = parser.parse_args()
    settings = load_settings()
    store = DataStore(settings)
    months: dict[str, dict] = {}
    for row in store.calendar(START, END).to_pylist():
        d = row["date"]
        if row["close_minute_et"] != 960:
            continue
        path = store.bars_root / "minute" / f"year={d.year}" / f"{d.isoformat()}.parquet"
        month = months.setdefault(d.isoformat()[:7], {"files": [], "days": []})
        month["files"].append(str(path))
        month["days"].append(d.isoformat())
    out = settings.data_dir / "research" / "recent" / "features"
    pending = [m for m in months if not (out / f"{m}.parquet").exists()]
    deadline = time.time() + args.budget
    jobs = [{"month": m, **months[m], "out": str(out), "panel": str(store.root),
             "deadline": deadline} for m in pending]  # fmt: skip
    with ProcessPoolExecutor(args.workers) as pool:
        done = sum(r is not None for r in pool.map(month_job, jobs))
    print(f"months {len(months)}, done now {done}, pending {len(pending) - done}")


if __name__ == "__main__":
    main()
