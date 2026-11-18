"""strategies/overnight_hold/HYPOTHESIS.md: hold only at night (closing auction to opening
auction) the stocks whose gains have come at night, or only by day the ones whose gains have
come in the session.

    cd research/claude
    uv run python night_bids.py filings        # results nights, shared
    uv run python overnight_hold.py table
    uv run python overnight_hold.py search
    uv run python overnight_hold.py test night 20 large
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
COST = """2 * (least(0.01, greatest(0.000175, 0.0035 / close))
               + case when adv < 1e6 then 0.0025 when adv < 1e7 then 0.0010
                      when adv < 1e8 then 0.0005 else 0.0002 end)"""


def folder():
    out = load_settings().data_dir / "research" / "overnight_hold"
    out.mkdir(parents=True, exist_ok=True)
    return out


def connect():
    con = duckdb.connect()
    con.execute(f"set threads=3; set memory_limit='2000MB'; set temp_directory='{tempfile.mkdtemp()}'")
    return con


def table() -> None:
    store = DataStore(load_settings())
    connect().execute(
        f"""copy (
            with q as (
                select permaticker, date, category, open, close, adv20_prev as adv, marketcap_prev as mcap,
                       ln(open / prev_close) as n, ln(close / open) as d,
                       coalesce(date - prev_date <= 5, false) as fresh
                from read_parquet('{store.root}/panel/*.parquet')
                where date <= DATE '2023-11-08' and prev_close > 0 and open > 0 and close > 0),
            r as (
                select *, sum(n) over (w rows 19 preceding) as n20, sum(n) over (w rows 59 preceding) as n60,
                       sum(d) over (w rows 19 preceding) as d20, sum(d) over (w rows 59 preceding) as d60,
                       count(*) over (w rows 59 preceding) as h60, bool_and(fresh) over (w rows 59 preceding) as steady,
                       lead(exp(n)) over w as next_night, lead(exp(d)) over w as next_day,
                       lead(fresh) over w as next_fresh
                from q window w as (partition by permaticker order by date))
            select date as day, permaticker, mcap, adv, close, n20, n60, d20, d60,
                   next_night - 1 as night, next_day - 1 as session, {COST} as cost
            from r
            where date between DATE '2005-01-03' and DATE '2023-10-13' and category like '%Common Stock%'
              and mcap >= 5e7 and adv >= 250000 and close >= 5 and fresh and next_fresh and steady and h60 = 60
              and next_night between 0.5 and 1.5 and next_day between 0.5 and 1.5
              and not exists (select 1 from '{shared()}/results_due.parquet' x
                              where x.permaticker = r.permaticker and x.day = r.date)
        ) to '{folder()}/stocks.parquet' (format parquet)"""
    )
    print(duckdb.sql(f"select count(*), min(day), max(day) from '{folder()}/stocks.parquet'").fetchall())


def books(score: str, ret: str, size: str) -> dict[str, np.ndarray]:
    """The book's return each session: the top BOOK stocks by score in the size group."""
    small, big = SIZES[size]
    t = duckdb.sql(
        f"""with s as (
                select day, {ret} - cost as net, {ret} as gross,
                       row_number() over (partition by day order by {score} desc) as rk
                from '{folder()}/stocks.parquet' where mcap >= {small} and mcap < {big})
            select day, year(day) as yr, (date_diff('day', DATE '2003-12-29', day) // 7) as week,
                   avg(net) as net, avg(gross) as gross, count(*) as n
            from s where rk <= {BOOK} group by day order by day"""
    ).to_arrow_table()
    return {n: t.column(n).to_numpy(zero_copy_only=False) for n in t.column_names}


def measure(b, keep) -> dict:
    net = b["net"][keep].astype(float)
    if len(net) < 3:
        return {"n": len(net)}
    _, t, _ = weekly(net, b["week"][keep])
    years = b["yr"][keep]
    wealth = np.cumsum(np.log1p(net))
    drawdown = float(np.exp((wealth - np.maximum.accumulate(wealth)).min()) - 1)
    yearly = {int(y): float(np.expm1(np.log1p(net[years == y]).sum())) for y in sorted(set(years))}
    return {"n": len(net), "net": net.mean(), "gross": b["gross"][keep].mean(), "t": t,
            "pos": sum(v > 0 for v in yearly.values()), "years": len(yearly), "dd": drawdown, "yearly": yearly}  # fmt: skip


def show(label, m) -> str:
    if m["n"] < 3:
        return f"{label:20} {m['n']}"
    return (f"{label:20} {m['n']:>5} sessions  gross {100 * m['gross']:>6.3f}%  net {100 * m['net']:>6.3f}%  "
            f"t {m['t']:>5.2f}  yrs {m['pos']} of {m['years']}  worst drawdown {100 * m['dd']:>4.0f}%")  # fmt: skip


CELLS = {("night", w): (f"n{w}", "night") for w in (20, 60)} | {("day", w): (f"d{w}", "session") for w in (20, 60)}


def period(b, name):
    first, last = PERIODS[name]
    return (b["yr"] >= first) & (b["yr"] <= last)


def search() -> None:
    passed = []
    for (book, window), (score, ret) in CELLS.items():
        for size in SIZES:
            b = books(score, ret, size)
            m = measure(b, period(b, "search"))
            label = f"{book} {window} {size}"
            print(show(label, m))
            if m["n"] >= 3 and m["net"] >= 0.0008 and m["t"] >= 3 and m["pos"] >= 6:
                passed.append(label)
    print("\nMeet the search bar:", passed or "none")


def test(book, window, size) -> None:
    score, ret = CELLS[(book, int(window))]
    b = books(score, ret, size)
    for name in ("early", "late"):
        m = measure(b, period(b, name))
        print(show(f"{book} {window} {size} {name}", m))
        print("    " + "  ".join(f"{y} {100 * v:.1f}%" for y, v in m["yearly"].items()))


if __name__ == "__main__":
    if sys.argv[1] == "table":
        table()
    elif sys.argv[1] == "search":
        search()
    else:
        test(*sys.argv[2:5])
