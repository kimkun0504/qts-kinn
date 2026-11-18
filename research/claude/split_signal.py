"""strategies/dividend_signal/HYPOTHESIS.md, addendum "forward splits".

    cd research/claude
    uv run python split_signal.py table
    uv run python split_signal.py search
"""

from __future__ import annotations

import sys
import tempfile

import duckdb
import numpy as np

from dividend_signal import BAR, HOLDS, PERIODS, folder, measure, show
from kinn.core.settings import load_settings
from kinn.data.store import DataStore

SIZES = {"mid": (3e8, 2e9), "large": (2e9, 1e18)}


def table() -> None:
    store = DataStore(load_settings())
    con = duckdb.connect()
    con.execute(f"set threads=3; set memory_limit='2000MB'; set temp_directory='{tempfile.mkdtemp()}'")
    con.execute(
        f"""copy (
            with ev as (select ticker, date as ex from '{folder()}/splits.parquet'
                        where value >= 1.5 and date between DATE '2005-01-03' and DATE '2023-10-13'),
            p as (
                select permaticker, date, ticker, category, close, prev_close, adv20_prev as adv,
                       marketcap_prev as mcap, open / close as oc, sum(ln(close / prev_close)) over w as c
                from read_parquet('{store.root}/panel/*.parquet')
                where date <= DATE '2023-11-08' and prev_close > 0 and close > 0 and open > 0
                window w as (partition by permaticker order by date)),
            q as (select *, lead(c, 19) over w as c20, lead(c, 59) over w as c60
                  from p window w as (partition by permaticker order by date)),
            u as (select date, case when mcap < 2e9 then 'mid' else 'large' end as size,
                         exp(c20 - c) / oc - 1 as g20, exp(c60 - c) / oc - 1 as g60
                  from q where category like '%Common Stock%' and mcap >= 3e8 and adv >= 250000 and prev_close >= 1),
            avgs as (select date, size, avg(g20) as all20, avg(g60) as all60 from u group by 1, 2),
            hits as (select q.*, row_number() over (partition by q.permaticker, ev.ex order by q.date) as k
                     from ev join q on q.ticker = ev.ticker and q.date >= ev.ex and q.date <= ev.ex + 4)
            select 'split' as kind, h.date as day, h.permaticker, h.ticker, h.mcap, h.adv, h.prev_close,
                   case when h.mcap < 2e9 then 'mid' else 'large' end as size,
                   exp(h.c20 - h.c) / h.oc - 1 as g20, exp(h.c60 - h.c) / h.oc - 1 as g60, a.all20, a.all60,
                   2 * (least(0.01, greatest(0.000175, 0.0035 / h.close))
                        + case when h.adv < 1e6 then 0.0025 when h.adv < 1e7 then 0.0010
                               when h.adv < 1e8 then 0.0005 else 0.0002 end) as cost
            from hits h left join avgs a on a.date = h.date and a.size = case when h.mcap < 2e9 then 'mid' else 'large' end
            where h.k = 1 and h.category like '%Common Stock%' and h.mcap >= 3e8 and h.adv >= 250000
              and h.prev_close >= 1 and h.c20 is not null
        ) to '{folder()}/split_events.parquet' (format parquet)"""
    )
    print(con.sql(f"select size, count(*), min(day), max(day) from '{folder()}/split_events.parquet' group by 1").fetchall())


def search() -> None:
    t = duckdb.sql(f"select *, year(day) as yr, (date_diff('day', DATE '2003-12-29', day) // 7) as week from '{folder()}/split_events.parquet'").to_arrow_table()
    d = {n: t.column(n).to_numpy(zero_copy_only=False) for n in t.column_names}
    for size in SIZES:
        for hold in HOLDS:
            first, last = PERIODS["search"]
            keep = (d["size"] == size) & (d["yr"] >= first) & (d["yr"] <= last)
            m = measure(d, keep, hold)
            ok = m["n"] >= 3 and m["over"] >= BAR[hold] and m["t"] >= 3 and m["pos"] >= 6 and m["net"] > 0
            print(show(f"split {size} {hold}", m) + ("  MEETS THE BAR" if ok else ""))
    _ = np


if __name__ == "__main__":
    table() if sys.argv[1] == "table" else search()
