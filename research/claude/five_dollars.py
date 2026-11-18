"""strategies/five_dollars/HYPOTHESIS.md: a small company back over $5 after months under it.

    cd research/claude
    uv run python five_dollars.py table
    uv run python five_dollars.py search
"""

from __future__ import annotations

import sys
import tempfile

import duckdb
import numpy as np

from dividend_signal import BAR, PERIODS, measure, show
from kinn.core.settings import load_settings
from kinn.data.store import DataStore

SIZES = {"small": (5e7, 3e8), "larger": (3e8, 1e18)}


def folder():
    out = load_settings().data_dir / "research" / "five_dollars"
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
                select permaticker, date, category, close, adv20_prev as adv, marketcap_prev as mcap,
                       open / close as oc, sum(ln(close / prev_close)) over w as c, row_number() over w as rn,
                       coalesce(split_ratio, 1) <> 1 as split
                from read_parquet('{store.root}/panel/*.parquet')
                where date <= DATE '2023-11-08' and prev_close > 0 and close > 0 and open > 0
                window w as (partition by permaticker order by date)),
            q as (
                select *,
                       sum((close < 5)::int) over (w rows between 60 preceding and 1 preceding) as under60,
                       sum((close < 5)::int) over (w rows between 64 preceding and 5 preceding) as under60_before5,
                       sum((close >= 5)::int) over (w rows between 4 preceding and current row) as over5,
                       bool_or(split) over (w rows between 65 preceding and current row) as split_near,
                       lead(c, 1) over w as c1, lead(oc, 1) over w as oc1, lead(date, 1) over w as next_date, lead(c, 20) over w as c20, lead(c, 60) over w as c60
                from p window w as (partition by permaticker order by date)),
            earn as (select permaticker, day from '{swing}/earn.parquet'
                     union select permaticker, day from '{swing}/earn_early.parquet'),
            u as (select next_date as date, case when mcap < 3e8 then 'small' else 'larger' end as size,
                         exp(c20 - c1) / oc1 - 1 as g20, exp(c60 - c1) / oc1 - 1 as g60
                  from q where category like '%Common Stock%' and mcap >= 5e7 and adv >= 250000 and close >= 1
                    and c20 is not null),
            avgs as (select date, size, avg(g20) as all20, avg(g60) as all60 from u group by 1, 2),
            ev as (
                select q.*, case when close >= 5 and under60 = 60 then 'first'
                                 when over5 = 5 and under60_before5 = 60 then 'five' end as kind
                from q
                where category like '%Common Stock%' and mcap >= 5e7 and adv >= 250000
                  and date between DATE '2005-01-03' and DATE '2023-10-13' and not split_near and c20 is not null
                  and not exists (select 1 from earn e where e.permaticker = q.permaticker
                                  and e.day between q.date - 4 and q.date)),
            once as (select * from ev where kind is not null
                     qualify coalesce(rn - lag(rn) over (partition by permaticker, kind order by rn), 999) >= 120)
            select o.kind, o.date as day, o.permaticker, o.mcap, o.adv, o.close as prev_close,
                   case when o.mcap < 3e8 then 'small' else 'larger' end as size,
                   exp(o.c20 - o.c1) / o.oc1 - 1 as g20, exp(o.c60 - o.c1) / o.oc1 - 1 as g60, a.all20, a.all60,
                   2 * (least(0.01, greatest(0.000175, 0.0035 / o.close))
                        + case when o.adv < 1e6 then 0.0025 when o.adv < 1e7 then 0.0010
                               when o.adv < 1e8 then 0.0005 else 0.0002 end) as cost
            from once o left join avgs a on a.date = o.next_date
                and a.size = case when o.mcap < 3e8 then 'small' else 'larger' end
        ) to '{folder()}/events.parquet' (format parquet)"""
    )
    print(con.sql(f"select kind, size, count(*) from '{folder()}/events.parquet' group by 1, 2 order by 1, 2").fetchall())


def search() -> None:
    t = duckdb.sql(f"select *, year(day) as yr, (date_diff('day', DATE '2003-12-29', day) // 7) as week from '{folder()}/events.parquet'").to_arrow_table()
    d = {n: t.column(n).to_numpy(zero_copy_only=False) for n in t.column_names}
    first, last = PERIODS["search"]
    for kind in ("first", "five"):
        for size in SIZES:
            for hold in (20, 60):
                keep = (d["kind"] == kind) & (d["size"] == size) & (d["yr"] >= first) & (d["yr"] <= last)
                m = measure(d, keep, hold)
                ok = m["n"] >= 3 and m["over"] >= BAR[hold] and m["t"] >= 3 and m["pos"] >= 6 and m["net"] > 0
                print(show(f"{kind} {size} {hold}", m) + ("  MEETS THE BAR" if ok else ""))
    _ = np


if __name__ == "__main__":
    table() if sys.argv[1] == "table" else search()
