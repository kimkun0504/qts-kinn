"""strategies/ssr_day/HYPOTHESIS.md: the session after the short-sale circuit breaker trips.

    cd research/claude
    uv run python ssr_day.py table
    uv run python ssr_day.py search
"""

from __future__ import annotations

import sys
import tempfile

import duckdb
import numpy as np
from swing_earnings import weekly

from kinn.core.settings import load_settings
from kinn.data.store import DataStore
from night_bids import folder as shared

SIZES = {"mid": (3e8, 2e9), "large": (2e9, 1e18)}
SPANS = {"placebo 2005-2010": (2005, 2010), "search 2011-2017": (2011, 2017), "test 2018-2022": (2018, 2022)}


def folder():
    out = load_settings().data_dir / "research" / "ssr_day"
    out.mkdir(parents=True, exist_ok=True)
    return out


def table() -> None:
    settings = load_settings()
    store = DataStore(settings)
    swing = settings.data_dir / "research" / "swing"
    con = duckdb.connect()
    con.execute(f"set threads=3; set memory_limit='2000MB'; set temp_directory='{tempfile.mkdtemp()}'")
    con.execute(
        f"""copy (
            with p as (
                select permaticker, date, category, low, close, prev_close, adv20_prev as adv, marketcap_prev as mcap,
                       lag(close) over w as close_before, sum(ln(close / prev_close)) over w as c
                from read_parquet('{store.root}/panel/*.parquet')
                where date <= DATE '2023-11-08' and prev_close > 0 and close > 0 and low > 0
                  and permaticker in (select permaticker from read_parquet('{store.root}/panel/*.parquet')
                                      where date >= DATE '2005-01-01' and marketcap_prev >= 3e8 and low <= 0.92 * prev_close)
                window w as (partition by permaticker order by date)),
            q as (select *, lead(c) over w as c1, lead(date) over w as next_date
                  from p window w as (partition by permaticker order by date)),
            earn as (select permaticker, day from '{swing}/earn.parquet' union select permaticker, day from '{swing}/earn_early.parquet')
            select date as day, permaticker, mcap, adv, close, low / prev_close - 1 as low_move, close / prev_close - 1 as close_move,
                   exp(c1 - c) - 1 as g,
                   2 * (least(0.01, greatest(0.000175, 0.0035 / close))
                        + case when adv < 1e6 then 0.0025 when adv < 1e7 then 0.0010
                               when adv < 1e8 then 0.0005 else 0.0002 end) as cost
            from q
            where date between DATE '2005-01-03' and DATE '2023-10-13' and category like '%Common Stock%'
              and mcap >= 3e8 and adv >= 1e6 and prev_close >= 5 and low <= 0.92 * prev_close and c1 is not null
              and not exists (select 1 from earn e where e.permaticker = q.permaticker and e.day between q.date - 4 and q.next_date)
              and not exists (select 1 from '{shared()}/results_due.parquet' x where x.permaticker = q.permaticker
                              and x.day between q.date - 4 and q.date)
        ) to '{folder()}/events.parquet' (format parquet)"""
    )
    print(con.sql(f"""select low_move <= -0.10 as tripped, count(*) from '{folder()}/events.parquet' group by 1""").fetchall())


def search(spans=("placebo 2005-2010", "search 2011-2017")) -> None:
    t = duckdb.sql(f"select *, year(day) as yr, (date_diff('day', DATE '2003-12-29', day) // 7) as week from '{folder()}/events.parquet'").to_arrow_table()
    d = {n: t.column(n).to_numpy(zero_copy_only=False) for n in t.column_names}
    net = d["g"].astype(float) - d["cost"]
    tripped = d["low_move"] <= -0.10
    near = (d["low_move"] > -0.10) & (d["low_move"] <= -0.08)
    groups = {"recovered": d["close_move"] > -0.10, "stayed down": d["close_move"] <= -0.10}
    for size, (lo, hi) in SIZES.items():
        inside = (d["mcap"] >= lo) & (d["mcap"] < hi)
        for gname, gmask in groups.items():
            for span, (a, b) in ((s, SPANS[s]) for s in spans):
                yrs = (d["yr"] >= a) & (d["yr"] <= b)
                k = inside & gmask & yrs & tripped
                c = inside & gmask & yrs & near
                if k.sum() < 3:
                    print(f"{size} {gname} {span}: {k.sum()}")
                    continue
                _, tt, _ = weekly(net[k], d["week"][k])
                years = d["yr"][k]
                pos = sum(net[k][years == y].mean() > 0 for y in set(years))
                ctrl = f"near misses {100 * net[c].mean():6.2f}% ({c.sum()})" if c.sum() else "near misses: none"
                print(f"{size:5} {gname:11} {span:18} tripped {k.sum():>5}  net {100 * net[k].mean():6.2f}%  t {tt:5.2f}  "
                      f"yrs {pos} of {len(set(years))}   {ctrl}")  # fmt: skip


if __name__ == "__main__":
    if sys.argv[1] == "table":
        table()
    elif sys.argv[1] == "search":
        search()
    else:
        search(("test 2018-2022",))
