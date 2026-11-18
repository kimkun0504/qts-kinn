"""strategies/dividend_signal/HYPOTHESIS.md: dividend initiations and raises.

    cd research/claude
    uv run python dividend_signal.py table
    uv run python dividend_signal.py search
    uv run python dividend_signal.py test initiation small 60
"""

from __future__ import annotations

import sys
import tempfile

import duckdb
import numpy as np
from swing_earnings import weekly

from kinn.core.settings import load_settings
from kinn.data.store import DataStore

SIZES = {"small": (5e7, 3e8), "mid": (3e8, 2e9)}
HOLDS = (20, 60)
BAR = {20: 0.01, 60: 0.02}
PERIODS = {"search": (2010, 2017), "early": (2005, 2009), "late": (2018, 2022), "check": (2023, 2023)}


def folder():
    return load_settings().data_dir / "research" / "dividend_signal"


def table() -> None:
    store = DataStore(load_settings())
    con = duckdb.connect()
    con.execute(f"set threads=3; set memory_limit='2000MB'; set temp_directory='{tempfile.mkdtemp()}'")
    con.execute(
        f"""copy (
            with v as (
                select ticker, date, value, lag(date) over w as prev_date, lag(value) over w as prev_value
                from (select ticker, date, sum(value) as value from '{folder()}/dividends.parquet'
                      where value > 0 group by 1, 2)
                window w as (partition by ticker order by date)),
            ev as (
                select v.ticker, v.date as ex,
                       case when v.prev_date is null or date_diff('day', v.prev_date, v.date) > 730 then 'initiation'
                            when v.value / v.prev_value between 1.25 and 3
                                 and date_diff('day', v.prev_date, v.date) between 60 and 120
                                 and not exists (select 1 from '{folder()}/splits.parquet' s
                                                 where s.ticker = v.ticker and s.date > v.prev_date and s.date <= v.date)
                            then 'raise' end as kind
                from v where v.date between DATE '2005-01-03' and DATE '2023-10-13'),
            p as (
                select permaticker, date, ticker, category, close, prev_close, adv20_prev as adv,
                       marketcap_prev as mcap, open / close as oc, sum(ln(close / prev_close)) over w as c,
                       min(date) over (partition by permaticker) as first_date
                from read_parquet('{store.root}/panel/*.parquet')
                where date <= DATE '2023-11-08' and prev_close > 0 and close > 0 and open > 0
                window w as (partition by permaticker order by date)),
            q as (select *, lead(c, 19) over w as c20, lead(c, 59) over w as c60
                  from p window w as (partition by permaticker order by date)),
            u as (select date, case when mcap < 3e8 then 'small' else 'mid' end as size,
                         exp(c20 - c) / oc - 1 as g20, exp(c60 - c) / oc - 1 as g60
                  from q where category like '%Common Stock%' and mcap >= 5e7 and mcap < 2e9 and adv >= 250000
                    and prev_close >= 1),
            avgs as (select date, size, avg(g20) as all20, avg(g60) as all60 from u group by 1, 2),
            hits as (
                select ev.kind, q.*, row_number() over (partition by q.permaticker, ev.ex order by q.date) as k
                from ev join q on q.ticker = ev.ticker and q.date >= ev.ex and q.date <= ev.ex + 4
                where ev.kind is not null)
            select h.kind, h.date as day, h.permaticker, h.ticker, h.mcap, h.adv, h.prev_close,
                   case when h.mcap < 3e8 then 'small' else 'mid' end as size,
                   exp(h.c20 - h.c) / h.oc - 1 as g20, exp(h.c60 - h.c) / h.oc - 1 as g60, a.all20, a.all60,
                   2 * (least(0.01, greatest(0.000175, 0.0035 / h.prev_close))
                        + case when h.adv < 1e6 then 0.0025 when h.adv < 1e7 then 0.0010
                               when h.adv < 1e8 then 0.0005 else 0.0002 end) as cost
            from hits h left join avgs a on a.date = h.date
                and a.size = case when h.mcap < 3e8 then 'small' else 'mid' end
            where h.k = 1 and h.category like '%Common Stock%' and h.mcap >= 5e7 and h.mcap < 2e9
              and h.adv >= 250000 and h.prev_close >= 1 and h.c20 is not null
              and (h.kind = 'raise' or h.date >= h.first_date + 730)
        ) to '{folder()}/events.parquet' (format parquet)"""
    )
    print(con.sql(f"select kind, size, count(*), min(day), max(day) from '{folder()}/events.parquet' group by 1, 2 order by 1, 2").fetchall())


def load():
    t = duckdb.sql(
        f"select *, year(day) as yr, (date_diff('day', DATE '2003-12-29', day) // 7) as week from '{folder()}/events.parquet' order by day"
    ).to_arrow_table()
    return {n: t.column(n).to_numpy(zero_copy_only=False) for n in t.column_names}


def measure(d, keep, hold) -> dict:
    g = d[f"g{hold}"].astype(float)
    keep = keep & ~np.isnan(g) & ~np.isnan(d[f"all{hold}"].astype(float))
    n = int(keep.sum())
    if n < 3:
        return {"n": n}
    net = g[keep] - d["cost"][keep]
    over = g[keep] - d[f"all{hold}"][keep].astype(float)
    _, t, _ = weekly(over, d["week"][keep])
    years = d["yr"][keep]
    return {"n": n, "net": net.mean(), "over": over.mean(), "t": t,
            "pos": sum(over[years == y].mean() > 0 for y in set(years)), "years": len(set(years)),
            "yearly": {int(y): over[years == y].mean() for y in sorted(set(years))}}  # fmt: skip


def show(label, m) -> str:
    if m["n"] < 3:
        return f"{label:24} {m['n']}"
    return (f"{label:24} {m['n']:>5} trades  over the average stock {100 * m['over']:>6.2f}%  t {m['t']:>5.2f}  "
            f"yrs {m['pos']} of {m['years']}  after costs {100 * m['net']:>6.2f}%")  # fmt: skip


def pick(d, kind, size, period):
    first, last = PERIODS[period]
    return (d["kind"] == kind) & (d["size"] == size) & (d["yr"] >= first) & (d["yr"] <= last)


def search() -> None:
    d = load()
    passed = []
    for kind in ("initiation", "raise"):
        for size in SIZES:
            for hold in HOLDS:
                m = measure(d, pick(d, kind, size, "search"), hold)
                label = f"{kind} {size} {hold}"
                print(show(label, m))
                if m["n"] >= 3 and m["over"] >= BAR[hold] and m["t"] >= 3 and m["pos"] >= 6 and m["net"] > 0:
                    passed.append(label)
    print("\nMeet the search bar:", passed or "none")


def test(kind, size, hold) -> None:
    d = load()
    for period in ("early", "late"):
        m = measure(d, pick(d, kind, size, period), int(hold))
        print(show(f"{kind} {size} {hold} {period}", m))
        if m["n"] >= 3:
            print("    " + "  ".join(f"{y} {100 * v:.2f}%" for y, v in m["yearly"].items()))


if __name__ == "__main__":
    if sys.argv[1] == "table":
        table()
    elif sys.argv[1] == "search":
        search()
    else:
        test(*sys.argv[2:5])
