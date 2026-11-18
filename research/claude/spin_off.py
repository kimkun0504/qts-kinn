"""strategies/spin_off/HYPOTHESIS.md: the new company after a spin-off, and its parent.

    cd research/claude
    uv run python spin_off.py table
    uv run python spin_off.py search
    uv run python spin_off.py test <cell>
"""

from __future__ import annotations

import glob
import os
import sys
import tempfile
import zipfile

import duckdb

from dividend_signal import PERIODS, measure, show
from kinn.core.settings import load_settings
from kinn.data.store import DataStore

CELLS = ("early", "late", "parent")


def folder():
    out = load_settings().data_dir / "research" / "spin_off"
    out.mkdir(parents=True, exist_ok=True)
    return out


def table() -> None:
    settings = load_settings()
    store = DataStore(settings)
    raw = max((settings.raw_dir / "sharadar").iterdir())
    tmp = tempfile.mkdtemp()
    with zipfile.ZipFile(glob.glob(f"{raw}/SHARADAR_ACTIONS_*.zip")[0]) as z:
        name = z.namelist()[0]
        z.extract(name, tmp)
    path = os.path.join(tmp, name)
    con = duckdb.connect()
    con.execute(f"set threads=3; set memory_limit='2000MB'; set temp_directory='{tmp}'")
    con.execute(f"""create table spins as select distinct date, ticker as parent, contraticker as child
                    from read_csv_auto('{path}')
                    where action = 'spinoff' and date between DATE '2005-01-01' and DATE '2023-10-13'
                      and contraticker is not null""")
    os.remove(path)
    con.execute(
        f"""create table q as
            with p as (select permaticker, date, ticker, category, open, close, dollar_volume, adv20_prev as adv,
                              marketcap_prev as mcap, open / close as oc, sum(ln(close / prev_close)) over w as c,
                              min(date) over (partition by permaticker) as first_date,
                              row_number() over w as s
                       from read_parquet('{store.root}/panel/*.parquet')
                       where date <= DATE '2023-11-08' and prev_close > 0 and close > 0 and open > 0
                       window w as (partition by permaticker order by date))
            select *, lead(c, 59) over w as c60 from p window w as (partition by permaticker order by date)"""
    )
    con.execute(
        """create table avgs as
           select date, avg(exp(c60 - c) / oc - 1) as all60 from q
           where category like '%Common Stock%' and mcap >= 3e8 and adv >= 1e6 and c60 is not null group by 1"""
    )

    def cost(price, adv):
        return (f"2 * (least(0.01, greatest(0.000175, 0.0035 / {price})) + case when {adv} < 1e6 then 0.0025 "
                f"when {adv} < 1e7 then 0.0010 when {adv} < 1e8 then 0.0005 else 0.0002 end)")  # fmt: skip

    con.execute(
        f"""create table events as
            with child as (
                select s.date as spun, s.child as ticker, q.permaticker, q.first_date, q.close as first_close,
                       q.dollar_volume as first_dv, q.category,
                       row_number() over (partition by s.child, s.date order by q.date) as k
                from spins s join q on q.ticker = s.child and q.date >= s.date - 7 and q.date <= s.date + 7),
            c1 as (select * from child where k = 1 and first_date >= spun - 7 and category like '%Common Stock%'
                   and first_close >= 3 and first_dv >= 1e6)
            select 'early' as kind, q.date as day, q.permaticker, q.ticker, q.close as prev_close, c1.first_dv as adv,
                   exp(q.c60 - q.c) / q.oc - 1 as g60, {cost('q.open', 'c1.first_dv')} as cost
            from c1 join q on q.permaticker = c1.permaticker and q.s = 2
            union all
            select 'late', q.date, q.permaticker, q.ticker, q.close, q.adv,
                   exp(q.c60 - q.c) / q.oc - 1, {cost('q.open', 'coalesce(q.adv, c1.first_dv)')}
            from c1 join q on q.permaticker = c1.permaticker and q.s = 11
            union all
            select 'parent', day, permaticker, ticker, prev_close, adv, g60, cost from (
                select q.date as day, q.permaticker, q.ticker, q.close as prev_close, q.adv,
                       exp(q.c60 - q.c) / q.oc - 1 as g60, {cost('q.open', 'q.adv')} as cost, q.category, q.mcap,
                       row_number() over (partition by s.parent, s.date order by q.date) as k
                from spins s join q on q.ticker = s.parent and q.date > s.date and q.date <= s.date + 7)
            where k = 1 and category like '%Common Stock%' and mcap >= 3e8"""
    )
    con.execute(
        f"""copy (select e.*, a.all60 from events e left join avgs a on a.date = e.day where e.g60 is not null)
            to '{folder()}/events.parquet' (format parquet)"""
    )
    print(con.sql(f"select kind, count(*), min(day), max(day) from '{folder()}/events.parquet' group by 1").fetchall())


def load():
    t = duckdb.sql(
        f"select *, year(day) as yr, (date_diff('day', DATE '2003-12-29', day) // 7) as week from '{folder()}/events.parquet'"
    ).to_arrow_table()
    return {n: t.column(n).to_numpy(zero_copy_only=False) for n in t.column_names}


def run(period, cells) -> None:
    d = load()
    first, last = PERIODS[period]
    for kind in cells:
        keep = (d["kind"] == kind) & (d["yr"] >= first) & (d["yr"] <= last)
        m = measure(d, keep, 60)
        ok = m["n"] >= 3 and m["over"] >= 0.02 and m["t"] >= 3 and m["pos"] >= 6 and m["net"] > 0
        print(show(f"{kind} 60 {period}", m) + ("  MEETS THE BAR" if ok and period == "search" else ""))
        if period != "search" and m["n"] >= 3:
            print("    " + "  ".join(f"{y} {100 * v:.2f}%" for y, v in m["yearly"].items()))


if __name__ == "__main__":
    if sys.argv[1] == "table":
        table()
    elif sys.argv[1] == "search":
        run("search", CELLS)
    else:
        run(sys.argv[2], sys.argv[3:])
