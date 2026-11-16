"""The daily table for the swing search (strategies/swing_search/HYPOTHESIS.md): one row per
stock per session from 2010, with features known at the close and the return of buying at the
next open and selling 5, 10 or 15 sessions after the signal day. Built in four parts.

    uv run python research/claude/swing_table.py
"""

from __future__ import annotations

import tempfile

import duckdb

from kinn.core.settings import load_settings
from kinn.data.store import DataStore

PARTS = 4
HOLDS = (5, 10, 15)


def select() -> str:
    cols = [
        "day",
        "year(day) as yr",
        "symbol",
        "permaticker",
        "category",
        "sector",
        "close",
        "mcap",
        "adv",
        "age",
        "filings_prev",
        "filings_today",
        "dvr",
        "gap",
        "loc",
        "exp(lr) - 1 as ret1",
        "sum((lr < 0)::int) over (partition by permaticker order by day "
        "rows between 4 preceding and current row) as down5",
        "stddev_samp(lr) over (partition by permaticker order by day "
        "rows between 19 preceding and current row) as vol20",
        "c - max(c) over (partition by permaticker order by day "
        "rows between 250 preceding and 1 preceding) as high250",
        "c - min(c) over (partition by permaticker order by day "
        "rows between 250 preceding and 1 preceding) as low250",
        "count(*) over (partition by permaticker order by day "
        "rows between 250 preceding and 1 preceding) as history",
        "lead(open) over w as next_open",
        "ln(lead(close) over w / lead(open) over w) as first_day",
        "lead(c) over w as c_next",
        "count(*) over (partition by permaticker order by day "
        "rows between 1 following and 15 following) as ahead",
        """case when adv < 1e6 then 0.0100 when adv < 1e7 then 0.0043
                when adv < 1e8 then 0.0018 else 0.0005 end as half_spread""",
        "least(0.01, greatest(0.000175, 0.0035 / close)) as commission",
    ]
    for n in (5, 20, 60, 120, 250):
        cols.append(f"exp(c - lag(c, {n}) over w) - 1 as ret{n}")
    for h in HOLDS:
        frame = (
            f"(partition by permaticker order by day rows between 1 following and {h} following)"
        )
        cols.append(f"last_value(c) over {frame} as c_exit{h}")
        cols.append(f"min(c - ln(close / low)) over {frame} as c_low{h}")
    return ",\n".join(cols)


def main() -> None:
    settings = load_settings()
    store = DataStore(settings)
    out = settings.data_dir / "research" / "swing"
    out.mkdir(parents=True, exist_ok=True)
    scratch = tempfile.mkdtemp()
    for part in range(PARTS):
        target = out / f"daily_{part}.parquet"
        if target.exists():
            continue
        con = duckdb.connect()
        con.execute(f"set threads=2; set memory_limit='2200MB'; set temp_directory='{scratch}'")
        con.execute("set preserve_insertion_order=false")
        tmp = out / f"daily_{part}.tmp"
        con.execute(
            f"""copy (
                with p as (
                    select p.date as day, p.symbol, p.permaticker, p.category, s.sector,
                           p.open, p.high, p.low, p.close, p.prev_close, p.marketcap_prev as mcap,
                           p.adv20_prev as adv, p.sessions_prior as age, p.filings_prev,
                           p.filings_today, p.dollar_volume / nullif(p.adv20_prev, 0) as dvr,
                           p.open / p.prev_close - 1 as gap,
                           (p.close - p.low) / nullif(p.high - p.low, 0) as loc,
                           ln(p.close / p.prev_close) as lr
                    from read_parquet('{store.root}/panel/*.parquet') p
                    left join '{store.root}/master/security_master.parquet' s using (permaticker)
                    where p.date >= DATE '2008-06-01' and p.permaticker % {PARTS} = {part}
                      and p.prev_close > 0 and p.close > 0 and p.low > 0
                      and p.category like '%Common Stock%'),
                q as (select *, sum(lr) over (partition by permaticker order by day) as c from p),
                r as (select {select()} from q
                      window w as (partition by permaticker order by day))
                select * from r where day >= DATE '2010-01-04' and close >= 1 and adv >= 250000
            ) to '{tmp}' (format parquet, compression zstd)"""
        )
        tmp.replace(target)
        con.close()
        print("part", part, "done", flush=True)


if __name__ == "__main__":
    main()
