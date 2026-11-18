"""strategies/quarter_turn/HYPOTHESIS.md: losers bought at the last close of a quarter.

    cd research/claude
    uv run python quarter_turn.py table
    uv run python quarter_turn.py search
    uv run python quarter_turn.py test <period> <turn> <size>
"""

from __future__ import annotations

import sys
import tempfile

import duckdb
import numpy as np

from dividend_signal import PERIODS
from kinn.core.settings import load_settings
from kinn.data.store import DataStore
from swing_earnings import weekly


def folder():
    out = load_settings().data_dir / "research" / "quarter_turn"
    out.mkdir(parents=True, exist_ok=True)
    return out


def table() -> None:
    store = DataStore(load_settings())
    con = duckdb.connect()
    con.execute(f"set threads=3; set memory_limit='2000MB'; set temp_directory='{tempfile.mkdtemp()}'")
    con.execute(
        f"""create table q as
            with p as (select permaticker, date, category, close, prev_close, adv20_prev as adv,
                              marketcap_prev as mcap, sum(ln(close / prev_close)) over w as c
                       from read_parquet('{store.root}/panel/*.parquet')
                       where date between DATE '2004-01-01' and DATE '2023-11-08' and prev_close > 0 and close > 0
                       window w as (partition by permaticker order by date))
            select *, lag(c, 1) over w as c_prev, lag(c, 121) over w as c_back, lead(c, 10) over w as c10
            from p window w as (partition by permaticker order by date)"""
    )
    con.execute(
        """create table ends as select max(date) as date from q
           where date between DATE '2005-01-01' and DATE '2023-09-30' group by year(date), quarter(date)"""
    )
    con.execute(
        f"""copy (
            with u as (select q.*, case when q.mcap < 3e8 then 'small' else 'mid' end as size,
                              q.c_prev - q.c_back as past, exp(q.c10 - q.c) - 1 as g
                       from q join ends e on e.date = q.date
                       where q.category like '%Common Stock%' and q.mcap >= 5e7 and q.mcap < 2e9
                         and q.adv >= 250000 and q.prev_close >= 2 and q.c_back is not null and q.c10 is not null),
            r as (select *, ntile(10) over (partition by date, size order by past) as decile,
                         avg(g) over (partition by date, size) as all_g from u)
            select date as day, permaticker, size, past, g, all_g, adv, close,
                   case when month(date) = 12 then 'december' else 'other' end as turn,
                   2 * (least(0.01, greatest(0.000175, 0.0035 / close))
                        + case when adv < 1e6 then 0.0025 when adv < 1e7 then 0.0010
                               when adv < 1e8 then 0.0005 else 0.0002 end) as cost
            from r where decile = 1
        ) to '{folder()}/events.parquet' (format parquet)"""
    )
    print(con.sql(f"select turn, size, count(*) from '{folder()}/events.parquet' group by 1, 2 order by 1, 2").fetchall())


def run(period, cells) -> None:
    t = duckdb.sql(
        f"select *, year(day) as yr, (date_diff('day', DATE '2003-12-29', day) // 7) as week from '{folder()}/events.parquet'"
    ).to_arrow_table()
    d = {n: t.column(n).to_numpy(zero_copy_only=False) for n in t.column_names}
    first, last = PERIODS[period]
    for turn, size in cells:
        keep = (d["turn"] == turn) & (d["size"] == size) & (d["yr"] >= first) & (d["yr"] <= last)
        over = d["g"][keep] - d["all_g"][keep]
        net = d["g"][keep] - d["cost"][keep]
        _, tt, _ = weekly(over, d["week"][keep])
        years = d["yr"][keep]
        yearly = {int(y): over[years == y].mean() for y in sorted(set(years))}
        pos = sum(v > 0 for v in yearly.values())
        bar = (150, 0.01, 3, 6) if period == "search" else (0, 0.005, 2.5, 4)
        ok = len(over) >= bar[0] and over.mean() >= bar[1] and tt >= bar[2] and pos >= bar[3] and net.mean() > 0
        print(f"{turn:8} {size:5} {period:7} {len(over):>5} trades  over the average {100 * over.mean():>6.2f}%  "
              f"t {tt:>5.2f}  yrs {pos} of {len(yearly)}  after costs {100 * net.mean():>6.2f}%"
              + ("  MEETS THE BAR" if ok else ""))  # fmt: skip
        if period != "search":
            print("    " + "  ".join(f"{y} {100 * v:.2f}%" for y, v in yearly.items()))
    _ = np


if __name__ == "__main__":
    if sys.argv[1] == "table":
        table()
    elif sys.argv[1] == "search":
        run("search", [(t, s) for t in ("december", "other") for s in ("small", "mid")])
    else:
        run(sys.argv[2], [(sys.argv[3], sys.argv[4])])
