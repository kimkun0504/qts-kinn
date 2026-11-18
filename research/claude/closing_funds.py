"""strategies/closing_bids/HYPOTHESIS.md, addendum "the market itself after a late sell-off":
SPY, QQQ and IWM bought in the last minute after a fall from 15:49, sold at the next open.

    cd research/claude
    uv run python closing_funds.py collect
    uv run python closing_funds.py measure
"""

from __future__ import annotations

import sys

import duckdb
import numpy as np
from swing_earnings import weekly

from closing_bids import folder
from kinn.core.settings import load_settings
from kinn.data.store import DataStore
from night_bids import connect

FUNDS = {"SPY": ("SPY",), "QQQ": ("QQQ", "QQQQ"), "IWM": ("IWM",)}
DEPTHS = (0.5, 1.0)
SPANS = {"2005-2009": (2005, 2009), "2010-2017": (2010, 2017), "2018-2022": (2018, 2022)}
COST = 0.0003 + 2 * 0.0001


def collect() -> None:
    store = DataStore(load_settings())
    root = store.bars_roots[0]
    names = [n for group in FUNDS.values() for n in group]
    con = connect()
    con.execute(
        f"""copy (
            with b as (
                select symbol, cast(regexp_extract(filename, '(\\d{{4}}-\\d{{2}}-\\d{{2}})\\.parquet', 1) as date) as day,
                       arg_max(close, minute_et) filter (where minute_et between 940 and 949) as before,
                       arg_max(close, minute_et) filter (where minute_et between 950 and 958) as seen,
                       max(high) filter (where minute_et = 959) as paid
                from read_parquet('{root}/minute/year=*/*.parquet', filename = true)
                where symbol in ({", ".join(repr(n) for n in names)}) and minute_et between 940 and 959
                group by 1, 2),
            d as (select symbol, date, close, lead(open) over (partition by symbol order by date) as next_open,
                         lead(date) over (partition by symbol order by date) as next_day
                  from read_parquet('{root}/daily/*.parquet') where symbol in ({", ".join(repr(n) for n in names)}))
            select b.day, b.symbol, b.before, b.seen, b.paid, d.close, d.next_open, d.next_day
            from b join d on d.symbol = b.symbol and d.date = b.day
            where b.day between DATE '2005-01-03' and DATE '2023-10-13' and d.next_open is not null
            order by 1, 2
        ) to '{folder()}/funds.parquet' (format parquet)"""
    )
    print(con.sql(f"select symbol, count(*), min(day), max(day) from '{folder()}/funds.parquet' group by 1 order by 1").fetchall())


def measure(spans=SPANS) -> None:
    rows = duckdb.sql(
        f"""select day, symbol, year(day) as yr, (date_diff('day', DATE '2003-12-29', day) // 7) as week,
                   seen / before - 1 as late, next_open / paid - 1 as g
            from '{folder()}/funds.parquet'
            where before is not null and seen is not null and paid is not null
              and abs(next_open / close - 1) <= 0.15"""
    ).to_arrow_table()
    d = {n: rows.column(n).to_numpy(zero_copy_only=False) for n in rows.column_names}
    for fund, names in FUNDS.items():
        mine = np.isin(d["symbol"], names)
        for depth in DEPTHS:
            keep = mine & (d["late"] <= -depth / 100)
            parts = []
            for label, (first, last) in spans.items():
                m = keep & (d["yr"] >= first) & (d["yr"] <= last)
                net = d["g"][m].astype(float) - COST
                parts.append(f"{label}: {m.sum():>3} {100 * net.mean():>6.2f}%" if m.sum() else f"{label}:   0")
            if len(spans) > 1:
                m = keep & (d["yr"] >= 2005) & (d["yr"] <= 2022)
                net = d["g"][m].astype(float) - COST
                _, t, _ = weekly(net, d["week"][m])
                years = d["yr"][m]
                positive = sum(net[years == y].mean() > 0 for y in set(years))
                parts.insert(0, f"2005-2022: {m.sum():>3} trades {100 * net.mean():>6.2f}%  median {100 * np.median(net):>6.2f}%  "
                                f"t {t:>5.2f}  wins {100 * (net > 0).mean():>3.0f}%  yrs {positive} of {len(set(years))}  "
                                f"worst {100 * net.min():>5.1f}%")  # fmt: skip
            print(f"{fund} down {depth}%:  " + "   ".join(parts))


if __name__ == "__main__":
    if sys.argv[1] == "collect":
        collect()
    else:
        measure()
