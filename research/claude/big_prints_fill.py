"""strategies/big_prints, check 7: the passed cell bought at the first 30 minutes' VWAP of D+1,
and its largest winners.

    cd research/claude
    uv run python big_prints_fill.py fills 2010 2014     # by years, resumable
    uv run python big_prints_fill.py read
    uv run python big_prints_fill.py winners
"""

from __future__ import annotations

import sys

import duckdb
import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq

from big_prints import folder
from kinn.core.settings import load_settings
from kinn.data.store import DataStore
from swing_earnings import weekly

CELL = "ret >= 0 and size = 'small' and fp >= 3 and quiet and signal_day <= DATE '2023-10-13'"


def signals():
    store = DataStore(load_settings())
    return duckdb.sql(
        f"""with e as (select * from '{folder()}/events_v8.parquet' where {CELL}),
            p as (select permaticker, date, symbol, open, lead(date) over w as next_day, lead(symbol) over w as next_symbol,
                         lead(open) over w as next_open
                  from read_parquet('{store.root}/panel/*.parquet')
                  where date <= DATE '2023-11-08' and permaticker in (select permaticker from e)
                  window w as (partition by permaticker order by date))
            select e.signal_day, e.permaticker, p.next_day, p.next_symbol, p.next_open, e.g20, e.all20, e.cost
            from e join p on p.permaticker = e.permaticker and p.date = e.signal_day"""
    ).fetchall()


def fills(first: int, last: int) -> None:
    store = DataStore(load_settings())
    rows = [r for r in signals() if r[2] and first <= r[2].year <= last]
    by_day: dict = {}
    for r in rows:
        by_day.setdefault(r[2], []).append(r)
    out = []
    for day, group in sorted(by_day.items()):
        try:
            bars = store.minute(day, symbols=[g[3] for g in group], columns="symbol, minute_et, close, volume")
        except FileNotFoundError:
            continue
        sym = bars.column("symbol").to_pylist()
        minute = bars.column("minute_et").to_numpy()
        price = bars.column("close").to_numpy()
        volume = bars.column("volume").to_numpy().astype(float)
        for g in group:
            k = np.array([s == g[3] for s in sym], dtype=bool) & (minute >= 570) & (minute < 600)
            if volume[k].sum() > 0:
                out.append({"signal_day": g[0], "permaticker": g[1], "vwap30": float(np.dot(price[k], volume[k]) / volume[k].sum()),
                            "next_open": g[4]})  # fmt: skip
    pq.write_table(pa.Table.from_pylist(out), folder() / f"fills_{first}_{last}.parquet")
    print(f"{first}-{last}: {len(out)} of {len(rows)} signals priced")


def read() -> None:
    t = duckdb.sql(
        f"""select e.signal_day, year(e.signal_day) as yr, (date_diff('day', DATE '2003-12-29', e.signal_day) // 7) as week,
                   e.g20, e.all20, e.cost, f.vwap30, f.next_open
            from '{folder()}/events_v8.parquet' e join read_parquet('{folder()}/fills_*.parquet') f
            using (signal_day, permaticker) where {CELL.replace('signal_day', 'e.signal_day')}"""
    ).fetchnumpy()
    exit_ = (1 + t["g20"]) * t["next_open"]
    g30 = exit_ / t["vwap30"] - 1
    for name, (a, b) in {"2010-2017": (2010, 2017), "2018-2022": (2018, 2022), "2023": (2023, 2023)}.items():
        k = (t["yr"] >= a) & (t["yr"] <= b)
        over_open = t["g20"][k] - t["all20"][k]
        over_30 = g30[k] - t["all20"][k]
        _, tt, _ = weekly(over_30, t["week"][k])
        gap = np.median(t["vwap30"][k] / t["next_open"][k] - 1)
        print(f"{name}: {k.sum()} priced; over the average from the open {100 * over_open.mean():+.2f}%, "
              f"from the 30-minute VWAP {100 * over_30.mean():+.2f}% (t {tt:.2f}); median VWAP above the open "
              f"{100 * gap:+.2f}%")


def winners() -> None:
    store = DataStore(load_settings())
    print(duckdb.sql(
        f"""with e as (select * from '{folder()}/events_v8.parquet' where {CELL} order by g20 desc limit 10)
            select e.signal_day, p.symbol, round(e.fp, 1), round(100 * e.g20) as pct,
                   (select string_agg(round(q.close, 2)::varchar, ' ' order by q.date) from read_parquet('{store.root}/panel/*.parquet') q
                    where q.permaticker = e.permaticker and q.date between e.signal_day and e.signal_day + 30) as closes
            from e join read_parquet('{store.root}/panel/*.parquet') p on p.permaticker = e.permaticker and p.date = e.signal_day
            order by pct desc"""
    ).fetchall())


if __name__ == "__main__":
    if sys.argv[1] == "fills":
        fills(int(sys.argv[2]), int(sys.argv[3]))
    elif sys.argv[1] == "read":
        read()
    else:
        winners()
