"""strategies/intraday_shape/HYPOTHESIS.md: first and last half-hour returns from minute bars.

    cd research/claude
    uv run python night_bids.py daily                 # shared daily table
    uv run python intraday_shape.py collect 2005 2023
    uv run python intraday_shape.py table
    uv run python intraday_shape.py search
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

SIZES = {"small": (5e7, 3e8), "mid": (3e8, 2e9), "large": (2e9, 1e18)}
PERIODS = {"search": (2010, 2017), "early": (2005, 2009), "late": (2018, 2022), "check": (2023, 2023)}
BOOK = 10


def folder():
    out = load_settings().data_dir / "research" / "intraday_shape"
    out.mkdir(parents=True, exist_ok=True)
    return out


def connect():
    con = duckdb.connect()
    con.execute(f"set threads=3; set memory_limit='2000MB'; set temp_directory='{tempfile.mkdtemp()}'")
    return con


def collect(first: int, last: int) -> None:
    store = DataStore(load_settings())
    con = connect()
    for year in range(first, last + 1):
        target = folder() / f"segments_{year}.parquet"
        if target.exists():
            continue
        files = str(store.bars_roots[0] / "minute" / f"year={year}" / "*.parquet")
        con.execute(
            f"""copy (
                select symbol, cast(regexp_extract(filename, '(\\d{{4}}-\\d{{2}}-\\d{{2}})\\.parquet', 1) as date) as day,
                       arg_max(close, minute_et) filter (where minute_et between 570 and 599) as p1000,
                       arg_max(close, minute_et) filter (where minute_et between 900 and 929) as p1530,
                       sum(close * volume) filter (where minute_et between 930 and 959) as d_last30,
                       sum(close * volume) filter (where minute_et between 570 and 599) as d_first30
                from read_parquet('{files}', filename = true)
                where minute_et between 570 and 959
                group by 1, 2
            ) to '{target}' (format parquet)"""
        )
        print(year, con.sql(f"select count(*) from '{target}'").fetchall()[0][0], flush=True)


def table() -> None:
    """The scores and the trade returns, one row per stock-day."""
    store = DataStore(load_settings())
    connect().execute(
        f"""copy (
            with p as (
                select permaticker, date, symbol, open, close, adv20_prev as adv, marketcap_prev as mcap,
                       sum(ln(close / prev_close)) over w as c, open / close as oc
                from read_parquet('{store.root}/panel/*.parquet')
                where date <= DATE '2023-11-08' and prev_close > 0 and close > 0 and open > 0
                window w as (partition by permaticker order by date)),
            q as (select p.*, ln(s.p1000 / p.open) as first30, ln(p.close / s.p1530) as last30
                  from p left join read_parquet('{folder()}/segments_*.parquet') s on s.symbol = p.symbol and s.day = p.date),
            r as (select *, sum(first30) over (w rows 9 preceding) as f10, sum(last30) over (w rows 9 preceding) as l10,
                         count(first30) over (w rows 9 preceding) as nf, count(last30) over (w rows 9 preceding) as nl,
                         lead(c, 1) over w as c1, lead(oc, 1) over w as oc1, lead(c, 5) over w as c5, lead(c, 10) over w as c10
                  from q window w as (partition by permaticker order by date))
            select r.date as day, r.permaticker, r.mcap, r.adv, r.close, r.f10, r.l10,
                   exp(r.c5 - r.c1) / r.oc1 - 1 as g5, exp(r.c10 - r.c1) / r.oc1 - 1 as g10,
                   2 * (least(0.01, greatest(0.000175, 0.0035 / r.close))
                        + case when r.adv < 1e6 then 0.0025 when r.adv < 1e7 then 0.0010
                               when r.adv < 1e8 then 0.0005 else 0.0002 end) as cost
            from r join '{shared()}/daily.parquet' d on d.permaticker = r.permaticker and d.day = r.date
            where r.nf = 10 and r.nl = 10 and r.c10 is not null and r.close >= 1
        ) to '{folder()}/scores.parquet' (format parquet)"""
    )
    print(duckdb.sql(f"select count(*), min(day), max(day) from '{folder()}/scores.parquet'").fetchall())


def cells(score: str, hold: int, size: str, order: str = "desc") -> dict[str, np.ndarray]:
    small, big = SIZES[size]
    t = duckdb.sql(
        f"""with s as (
                select *, row_number() over (partition by day order by {score} {order}) as rk,
                       avg(g{hold}) over (partition by day) as everyone
                from '{folder()}/scores.parquet' where mcap >= {small} and mcap < {big})
            select day, year(day) as yr, (date_diff('day', DATE '2003-12-29', day) // 7) as week,
                   g{hold} - cost as net, g{hold} - everyone as over
            from s where rk <= {BOOK} order by day"""
    ).to_arrow_table()
    return {n: t.column(n).to_numpy(zero_copy_only=False) for n in t.column_names}


def measure(d, keep) -> dict:
    net = d["net"][keep].astype(float)
    if len(net) < 3:
        return {"n": len(net)}
    _, t, _ = weekly(net, d["week"][keep])
    _, xt, _ = weekly(d["over"][keep].astype(float), d["week"][keep])
    years = d["yr"][keep]
    return {"n": len(net), "net": net.mean(), "t": t, "over": d["over"][keep].mean(), "xt": xt,
            "pos": sum(net[years == y].mean() > 0 for y in set(years)), "years": len(set(years)),
            "yearly": {int(y): net[years == y].mean() for y in sorted(set(years))}}  # fmt: skip


def show(label, m) -> str:
    if m["n"] < 3:
        return f"{label:22} {m['n']}"
    return (f"{label:22} {m['n']:>6}  net {100 * m['net']:>6.2f}%  t {m['t']:>5.2f}  yrs {m['pos']} of {m['years']}  "
            f"over the average stock {100 * m['over']:>6.2f}% (t {m['xt']:>5.2f})")  # fmt: skip


CELLS = [(score, hold, size) for score in ("f10", "l10") for hold in (5, 10) for size in SIZES]


def period(d, name):
    first, last = PERIODS[name]
    return (d["yr"] >= first) & (d["yr"] <= last)


def search() -> None:
    passed = []
    for score, hold, size in CELLS:
        d = cells(score, hold, size)
        m = measure(d, period(d, "search"))
        label = f"{score} {hold} {size}"
        print(show(label, m))
        if m["n"] >= 150 and m["net"] >= 0.01 and m["t"] >= 3 and m["pos"] >= 6:
            passed.append(label)
    print("\nMeet the search bar:", passed or "none")


def search_low() -> None:
    passed = []
    for score, hold, size in CELLS:
        d = cells(score, hold, size, "asc")
        m = measure(d, period(d, "search"))
        label = f"low {score} {hold} {size}"
        print(show(label, m))
        if m["n"] >= 150 and m["net"] >= 0.01 and m["t"] >= 3 and m["pos"] >= 6:
            passed.append(label)
    print("\nMeet the search bar:", passed or "none")


def test(score, hold, size, order="desc") -> None:
    d = cells(score, int(hold), size, order)
    for name in ("early", "late"):
        m = measure(d, period(d, name))
        print(show(f"{score} {hold} {size} {name}", m))
        print("    " + "  ".join(f"{y} {100 * v:.2f}%" for y, v in m["yearly"].items()))


if __name__ == "__main__":
    if sys.argv[1] == "collect":
        collect(int(sys.argv[2]), int(sys.argv[3]))
    elif sys.argv[1] == "table":
        table()
    elif sys.argv[1] == "search":
        search()
    elif sys.argv[1] == "search_low":
        search_low()
    else:
        test(*sys.argv[2:5])
