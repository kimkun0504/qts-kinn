"""strategies/holders13f/HYPOTHESIS.md: small companies whose number of 13F holders jumped.

    cd research/claude
    uv run python holders13f.py table
    uv run python holders13f.py search
    uv run python holders13f.py test rel small 60
"""

from __future__ import annotations

import sys
import tempfile

import duckdb
import numpy as np

from kinn.core.settings import load_settings
from kinn.data.store import DataStore

SIZES = {"small": (5e7, 3e8), "mid": (3e8, 2e9)}
SCORES = {"abs": "dabs", "rel": "drel"}
HOLDS = (20, 60)
BAR = {20: 0.01, 60: 0.02}
PERIODS = {"search": (2013, 2017), "late": (2018, 2022), "check": (2023, 2023)}
TOP = 20


def folder():
    return load_settings().data_dir / "research" / "holders13f"


def table() -> None:
    store = DataStore(load_settings())
    con = duckdb.connect()
    con.execute(f"set threads=3; set memory_limit='2000MB'; set temp_directory='{tempfile.mkdtemp()}'")
    con.execute(
        f"""copy (
            with h as (
                select date as q, ticker, shrholders as holders,
                       lag(shrholders) over (partition by ticker order by date) as prev,
                       lag(date) over (partition by ticker order by date) as qprev
                from '{folder()}/sf3a.parquet'),
            sig as (select q, ticker, holders - prev as dabs, (holders - prev) / prev as drel
                    from h where date_diff('day', qprev, q) between 85 and 95 and prev >= 3),
            days as (select distinct date from read_parquet('{store.root}/panel/*.parquet') where date <= DATE '2023-11-08'),
            sd as (select q, min(date) as s from (select distinct q from sig) x join days on date >= q + 60 group by q),
            p as (
                select permaticker, date, ticker, category, close, adv20_prev as adv, marketcap_prev as mcap,
                       open / close as oc, sum(ln(close / prev_close)) over w as c
                from read_parquet('{store.root}/panel/*.parquet')
                where date <= DATE '2023-11-08' and prev_close > 0 and close > 0 and open > 0
                window w as (partition by permaticker order by date)),
            r as (select *, lead(c, 19) over w as c20, lead(c, 59) over w as c60
                  from p window w as (partition by permaticker order by date))
            select sd.q, r.date as day, r.ticker, r.permaticker, r.mcap, r.adv, r.close, g.dabs, g.drel,
                   exp(r.c20 - r.c) / r.oc - 1 as g20, exp(r.c60 - r.c) / r.oc - 1 as g60,
                   2 * (least(0.01, greatest(0.000175, 0.0035 / r.close))
                        + case when r.adv < 1e6 then 0.0025 when r.adv < 1e7 then 0.0010
                               when r.adv < 1e8 then 0.0005 else 0.0002 end) as cost
            from sd join r on r.date = sd.s
            left join sig g on g.q = sd.q and g.ticker = r.ticker
            where r.category like '%Common Stock%' and r.mcap >= 5e7 and r.mcap < 2e9 and r.adv >= 250000
              and r.close >= 1 and r.c20 is not null
        ) to '{folder()}/rows.parquet' (format parquet)"""
    )
    print(con.sql(f"select count(*), count(dabs), count(g60), min(day), max(day), count(distinct q) from '{folder()}/rows.parquet'").fetchall())


def cohorts(score: str, size: str, hold: int) -> dict[str, np.ndarray]:
    small, big = SIZES[size]
    t = duckdb.sql(
        f"""with x as (select *, avg(g{hold}) over (partition by q) as everyone,
                              row_number() over (partition by q order by {SCORES[score]} desc nulls last) as rk
                       from '{folder()}/rows.parquet' where mcap >= {small} and mcap < {big} and g{hold} is not null)
            select q, year(q) as yr, avg(g{hold} - cost) as net, avg(g{hold} - everyone) as over, count(*) as n
            from x where rk <= {TOP} and {SCORES[score]} is not null group by q order by q"""
    ).to_arrow_table()
    return {n: t.column(n).to_numpy(zero_copy_only=False) for n in t.column_names}


def measure(d, keep) -> dict:
    over, net = d["over"][keep].astype(float), d["net"][keep].astype(float)
    if len(over) < 3:
        return {"n": len(over)}
    years = d["yr"][keep]
    return {"n": len(over), "trades": int(d["n"][keep].sum()), "over": over.mean(), "net": net.mean(),
            "t": over.mean() / (over.std(ddof=1) / len(over) ** 0.5),
            "pos": sum(over[years == y].mean() > 0 for y in set(years)), "years": len(set(years)),
            "yearly": {int(y): over[years == y].mean() for y in sorted(set(years))}}  # fmt: skip


def show(label, m) -> str:
    if m["n"] < 3:
        return f"{label:18} {m['n']}"
    return (f"{label:18} {m['n']:>3} quarters {m['trades']:>5} trades  over the average stock {100 * m['over']:>6.2f}%  "
            f"t {m['t']:>5.2f}  yrs {m['pos']} of {m['years']}  after costs {100 * m['net']:>6.2f}%")  # fmt: skip


def period(d, name):
    first, last = PERIODS[name]
    return (d["yr"] >= first) & (d["yr"] <= last)


def search() -> None:
    passed = []
    for score in SCORES:
        for size in SIZES:
            for hold in HOLDS:
                d = cohorts(score, size, hold)
                m = measure(d, period(d, "search"))
                label = f"{score} {size} {hold}"
                print(show(label, m))
                if m["n"] >= 3 and m["over"] >= BAR[hold] and m["t"] >= 3 and m["pos"] >= 4 and m["net"] > 0:
                    passed.append(label)
    print("\nMeet the search bar:", passed or "none")


def test(score, size, hold) -> None:
    d = cohorts(score, size, int(hold))
    m = measure(d, period(d, "late"))
    print(show(f"{score} {size} {hold} late", m))
    print("    " + "  ".join(f"{y} {100 * v:.2f}%" for y, v in m["yearly"].items()))


if __name__ == "__main__":
    if sys.argv[1] == "table":
        table()
    elif sys.argv[1] == "search":
        search()
    else:
        test(*sys.argv[2:5])
