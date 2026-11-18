"""strategies/index_deletion/HYPOTHESIS.md: companies dropped from the S&P 500 that stay listed.

    cd research/claude
    uv run python index_deletion.py table
    uv run python index_deletion.py search
"""

from __future__ import annotations

import glob
import os
import sys
import tempfile
import zipfile

import duckdb
import numpy as np

from dividend_signal import BAR, PERIODS, measure, show
from kinn.core.settings import load_settings
from kinn.data.store import DataStore


def folder():
    out = load_settings().data_dir / "research" / "index_deletion"
    out.mkdir(parents=True, exist_ok=True)
    return out


def table() -> None:
    settings = load_settings()
    store = DataStore(settings)
    raw = max((settings.raw_dir / "sharadar").iterdir())
    with zipfile.ZipFile(glob.glob(f"{raw}/SHARADAR_SP500_*.zip")[0]) as z:
        data = z.read(z.namelist()[0])
    tmp = tempfile.mkdtemp()
    path = os.path.join(tmp, "sp.csv")
    with open(path, "wb") as handle:
        handle.write(data)
    con = duckdb.connect()
    con.execute(f"set threads=3; set memory_limit='2000MB'; set temp_directory='{tmp}'")
    con.execute(f"""create table removed as select date, ticker from read_csv_auto('{path}')
                    where action = 'removed' and date between DATE '2005-01-01' and DATE '2023-10-13'""")
    os.remove(path)
    con.execute(
        f"""copy (
            with p as (select permaticker, date, ticker, category, close, adv20_prev as adv, marketcap_prev as mcap,
                              open / close as oc, sum(ln(close / prev_close)) over w as c
                       from read_parquet('{store.root}/panel/*.parquet')
                       where date <= DATE '2023-11-08' and prev_close > 0 and close > 0 and open > 0
                       window w as (partition by permaticker order by date)),
            q as (select *, lead(c, 1) over w as c1, lead(oc, 1) over w as oc1, lead(date, 1) over w as next_date,
                         lead(c, 20) over w as c20, lead(c, 60) over w as c60
                  from p window w as (partition by permaticker order by date)),
            u as (select next_date as date, exp(c20 - c1) / oc1 - 1 as g20, exp(c60 - c1) / oc1 - 1 as g60
                  from q where category like '%Common Stock%' and mcap >= 2e9 and adv >= 1e6 and c20 is not null),
            avgs as (select date, avg(g20) as all20, avg(g60) as all60 from u group by 1),
            hits as (select r.date as changed, q.*, row_number() over (partition by r.ticker, r.date order by q.date) as k
                     from removed r join q on q.ticker = r.ticker and q.date >= r.date and q.date <= r.date + 7)
            select 'deleted' as kind, h.date as day, h.permaticker, h.ticker, h.mcap, h.adv, h.close as prev_close,
                   'all' as size, exp(h.c20 - h.c1) / h.oc1 - 1 as g20, exp(h.c60 - h.c1) / h.oc1 - 1 as g60, a.all20, a.all60,
                   2 * (least(0.01, greatest(0.000175, 0.0035 / h.close))
                        + case when h.adv < 1e6 then 0.0025 when h.adv < 1e7 then 0.0010
                               when h.adv < 1e8 then 0.0005 else 0.0002 end) as cost
            from hits h left join avgs a on a.date = h.next_date
            where h.k = 1 and h.category like '%Common Stock%' and h.c20 is not null
        ) to '{folder()}/events.parquet' (format parquet)"""
    )
    print(con.sql(f"select count(*), min(day), max(day) from '{folder()}/events.parquet'").fetchall())


def search(period="search") -> None:
    t = duckdb.sql(f"select *, year(day) as yr, (date_diff('day', DATE '2003-12-29', day) // 7) as week from '{folder()}/events.parquet'").to_arrow_table()
    d = {n: t.column(n).to_numpy(zero_copy_only=False) for n in t.column_names}
    first, last = PERIODS[period]
    for hold in (20, 60):
        keep = (d["yr"] >= first) & (d["yr"] <= last)
        m = measure(d, keep, hold)
        ok = m["n"] >= 3 and m["over"] >= BAR[hold] and m["t"] >= 3 and m["pos"] >= 6 and m["net"] > 0
        print(show(f"deleted {hold} {period}", m) + ("  MEETS THE BAR" if ok and period == "search" else ""))
        if period != "search" and m["n"] >= 3:
            print("    " + "  ".join(f"{y} {100 * v:.2f}%" for y, v in m["yearly"].items()))
    _ = np


if __name__ == "__main__":
    if sys.argv[1] == "table":
        table()
    else:
        search(*sys.argv[2:])
