"""strategies/uplisting/HYPOTHESIS.md: a company that moves up to Nasdaq or the NYSE.

    cd research/claude
    uv run python uplisting.py table
    uv run python uplisting.py search
"""

from __future__ import annotations

import sys
import tempfile

import duckdb
import numpy as np

from dividend_signal import BAR, PERIODS, measure, show
from kinn.core.settings import load_settings
from kinn.data.store import DataStore

SIZES = {"small": (5e7, 3e8), "mid": (3e8, 2e9)}


def folder():
    return load_settings().data_dir / "research" / "dividend_signal"


def table() -> None:
    store = DataStore(load_settings())
    con = duckdb.connect()
    con.execute(f"set threads=3; set memory_limit='2000MB'; set temp_directory='{tempfile.mkdtemp()}'")
    con.execute(
        f"""copy (
            with f as (select date, ticker, contraname as old from '{folder()}/exchanges.parquet' where action = 'exchangefrom'),
            t as (select date, ticker, contraname as new from '{folder()}/exchanges.parquet' where action = 'exchangeto'),
            ev as (select t.date as moved, t.ticker from t join f using (date, ticker)
                   where f.old in ('OTC', 'NYSEMKT') and t.new in ('NASDAQ', 'NYSE')
                     and t.date between DATE '2005-01-01' and DATE '2023-10-13'),
            p as (select permaticker, date, ticker, category, close, dollar_volume as dv, marketcap_prev as mcap,
                         adv20_prev as adv, open / close as oc, sum(ln(close / prev_close)) over w as c
                  from read_parquet('{store.root}/panel/*.parquet')
                  where date <= DATE '2023-11-08' and prev_close > 0 and close > 0 and open > 0
                  window w as (partition by permaticker order by date)),
            q as (select *, lead(c, 1) over w as c1, lead(oc, 1) over w as oc1, lead(date, 1) over w as next_date,
                         lead(c, 20) over w as c20, lead(c, 60) over w as c60
                  from p window w as (partition by permaticker order by date)),
            u as (select next_date as date, case when mcap < 3e8 then 'small' else 'mid' end as size,
                         exp(c20 - c1) / oc1 - 1 as g20, exp(c60 - c1) / oc1 - 1 as g60
                  from q where category like '%Common Stock%' and mcap >= 5e7 and mcap < 2e9 and adv >= 250000
                    and close >= 1 and c20 is not null),
            avgs as (select date, size, avg(g20) as all20, avg(g60) as all60 from u group by 1, 2),
            hits as (select ev.moved, q.*, row_number() over (partition by ev.ticker, ev.moved order by q.date) as k
                     from ev join q on q.ticker = ev.ticker and q.date >= ev.moved and q.date <= ev.moved + 7)
            select 'uplist' as kind, h.date as day, h.permaticker, h.ticker, coalesce(h.mcap, 0) as mcap, h.dv as adv,
                   h.close as prev_close, case when h.mcap < 3e8 then 'small' else 'mid' end as size,
                   exp(h.c20 - h.c1) / h.oc1 - 1 as g20, exp(h.c60 - h.c1) / h.oc1 - 1 as g60, a.all20, a.all60,
                   2 * (least(0.01, greatest(0.000175, 0.0035 / h.close))
                        + case when h.dv < 1e6 then 0.0025 when h.dv < 1e7 then 0.0010
                               when h.dv < 1e8 then 0.0005 else 0.0002 end) as cost
            from hits h left join avgs a on a.date = h.next_date and a.size = case when h.mcap < 3e8 then 'small' else 'mid' end
            where h.k = 1 and h.category like '%Common Stock%' and h.mcap >= 5e7 and h.mcap < 2e9
              and h.dv >= 250000 and h.close >= 1 and h.c20 is not null
        ) to '{folder()}/uplist_events.parquet' (format parquet)"""
    )
    print(con.sql(f"select size, count(*), min(day), max(day) from '{folder()}/uplist_events.parquet' group by 1").fetchall())


def search() -> None:
    t = duckdb.sql(f"select *, year(day) as yr, (date_diff('day', DATE '2003-12-29', day) // 7) as week from '{folder()}/uplist_events.parquet'").to_arrow_table()
    d = {n: t.column(n).to_numpy(zero_copy_only=False) for n in t.column_names}
    first, last = PERIODS["search"]
    for size in SIZES:
        for hold in (20, 60):
            keep = (d["size"] == size) & (d["yr"] >= first) & (d["yr"] <= last)
            m = measure(d, keep, hold)
            ok = m["n"] >= 3 and m["over"] >= BAR[hold] and m["t"] >= 3 and m["pos"] >= 6 and m["net"] > 0
            print(show(f"uplist {size} {hold}", m) + ("  MEETS THE BAR" if ok else ""))
    _ = np


if __name__ == "__main__":
    table() if sys.argv[1] == "table" else search()
