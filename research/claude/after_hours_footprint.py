"""strategies/after_hours/HYPOTHESIS.md, addendum "who sells after hours": the short cell split
by the after-hours footprint.

    cd research/claude
    uv run python after_hours_footprint.py
"""

from __future__ import annotations

from collections import defaultdict

import duckdb
import numpy as np

from after_hours import CLOSE, folder, load, load_short
from kinn.core.settings import load_settings
from kinn.data.store import DataStore
from swing_earnings import weekly


def main(side: str = "short") -> None:
    store = DataStore(load_settings())
    if side == "short":
        d = load_short()
        keep = (d["mcap"] >= 3e8) & (d["mcap"] < 2e9) & (d["reaction"] <= -0.15)
    elif side == "long":
        d = load()
        keep = (d["timing"] == "after") & (d["mcap"] >= 2e9) & (d["reaction"] >= 0.05) & (d["reaction"] < 0.15)
    else:  # "small" or "small_open": the small-company long
        d = load()
        keep = (d["timing"] == "after") & (d["mcap"] >= 5e7) & (d["mcap"] < 3e8) & (d["reaction"] >= 0.05)
    rows = duckdb.sql(
        f"""select n.day, n.symbol, v.minute from read_parquet('{folder()}/entries_*.parquet') n
            join '{folder()}/events.parquet' v on v.day = n.day and v.symbol = n.symbol and v.timing = n.timing
            where n.timing = 'after'"""
    ).fetchall()
    minute_of = {(r[0], r[1]): r[2] for r in rows}
    if side == "short":
        names = duckdb.sql(
            f"""select n.day, n.symbol from read_parquet('{folder()}/entries_*.parquet') n
                join read_parquet('{folder()}/lows_*.parquet') w on w.day = n.day and w.symbol = n.symbol
                join '{folder()}/events.parquet' v on v.day = n.day and v.symbol = n.symbol and v.timing = n.timing
                where n.timing = 'after'
                order by n.day, n.symbol, n.timing"""
        ).fetchall()
    else:
        names = duckdb.sql(
            f"""select n.day, n.symbol from read_parquet('{folder()}/entries_*.parquet') n
                join '{folder()}/events.parquet' v on v.day = n.day and v.symbol = n.symbol and v.timing = n.timing
                order by n.day, n.symbol, n.timing"""
        ).fetchall()
    assert len(names) == len(d["day"])
    picked = [(i, names[i][0], names[i][1]) for i in np.flatnonzero(keep)]
    by_day = defaultdict(list)
    for i, day, symbol in picked:
        by_day[day].append((i, symbol))
    after = {}
    for day, group in by_day.items():
        bars = store.minute(day, symbols=[g[1] for g in group], columns="symbol, minute_et, volume, transactions")
        sym = np.array(bars.column("symbol").to_pylist())
        minute = bars.column("minute_et").to_numpy()
        volume = bars.column("volume").to_numpy().astype(float)
        trades = bars.column("transactions").to_numpy().astype(float)
        for i, symbol in group:
            at = min(max(minute_of[(day, symbol)] + 30, 990), 1170)
            k = (sym == symbol) & (minute > CLOSE) & (minute < at)
            if trades[k].sum() > 0:
                after[i] = volume[k].sum() / trades[k].sum()
    bars_daily = store.bars_roots[0] / "daily"
    con = duckdb.connect()
    con.execute("set threads=3; set memory_limit='1500MB'")
    import pyarrow as pa

    con.register("ev", pa.table({"i": [p[0] for p in picked], "day": [p[1] for p in picked],
                                 "symbol": [p[2] for p in picked]}))  # fmt: skip
    normal = dict(con.sql(
        f"""with j as (select ev.i, b.volume, b.transactions,
                              row_number() over (partition by ev.i order by b.date desc) as k
                       from ev join read_parquet('{bars_daily}/*.parquet') b
                       on b.symbol = ev.symbol and b.date < ev.day and b.date >= ev.day - 120
                       where b.transactions > 0 and b.volume > 0)
            select i, exp(avg(ln(volume / transactions))) from j where k <= 60 group by i having count(*) = 60"""
    ).fetchall())
    fp = np.full(len(d["day"]), np.nan)
    for i, _, _ in picked:
        if i in after and normal.get(i):
            fp[i] = after[i] / normal[i]
    net = (d["g_open"] if side == "short" else d["g_fifteen"]) - d["cost"]
    if side == "small_open":
        paid = d["paid"].astype(float)
        net = d["g_open15"] - d["cost_auction"] - 2 * np.minimum(0.01, np.maximum(0.000175, 0.0035 / paid))
    years = d["yr"]
    base = keep & ~np.isnan(fp)
    cut = np.median(fp[base & (years >= 2010) & (years <= 2017)])
    print(f"events {keep.sum()}, with a footprint {base.sum()}, the 2010-2017 median footprint {cut:.2f}")
    for name, (a, b) in {"2005-2009": (2005, 2009), "2010-2017": (2010, 2017), "2018-2022": (2018, 2022),
                         "2023": (2023, 2023)}.items():  # fmt: skip
        k = base & (years >= a) & (years <= b)
        out = []
        for label, m in ((side, k), ("large pieces", k & (fp >= cut)), ("small pieces", k & (fp < cut))):
            _, t, _ = weekly(net[m], d["week"][m])
            out.append(f"{label} {m.sum()} {100 * net[m].mean():+.2f}% (t {t:.2f})")
        print(f"{name}: " + "; ".join(out))
        if side == "small":  # fills of the after-hours entry
            m = k & (fp >= cut)
            thin = np.mean(d["bar_dollars"][m] < 5000) if m.any() else float("nan")
            thick = m & (d["bar_dollars"] >= 5000)
            _, t2, _ = weekly(net[thick], d["week"][thick])
            print(f"    large pieces, entry minute $5,000+: {thick.sum()} {100 * net[thick].mean():+.2f}% (t {t2:.2f}), "
                  f"median {100 * np.median(net[thick]):+.2f}%")
            print(f"    large pieces: median {100 * np.median(net[m]):+.2f}%, share of entry minutes under $5,000 "
                  f"{100 * thin:.0f}%, worst {100 * net[m].min():+.1f}%, best {100 * net[m].max():+.1f}%")


if __name__ == "__main__":
    import sys

    main(sys.argv[1] if len(sys.argv) > 1 else "short")
