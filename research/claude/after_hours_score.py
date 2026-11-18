"""strategies/after_hours/HYPOTHESIS.md, addendum "two indicators of our own": pressure
(after-hours dollars as a share of a normal day) and hold (how much of the after-hours peak
is left at the reading).

    cd research/claude
    uv run python after_hours_score.py peaks 2005 2023
    uv run python after_hours_score.py search
    uv run python after_hours_score.py test pressure high open
"""

from __future__ import annotations

import sys
from collections import defaultdict

import duckdb
import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq

from after_hours import CLOSE, OPEN, PERIODS, folder, measure, show
from kinn.core.settings import load_settings
from kinn.data.store import DataStore

PRESSURE = {"low": (0.0, 0.06), "middle": (0.06, 0.22), "high": (0.22, 1e9)}
EXITS = ("open", "close", "fifteen")


def peaks(first: int, last: int) -> None:
    """The highest after-hours price up to the reading, relative to the regular close."""
    store = DataStore(load_settings())
    out = folder()
    minute_of = {(r["day"], r["symbol"]): r["minute"] for r in pq.read_table(out / "events.parquet").to_pylist()
                 if r["timing"] == "after"}  # fmt: skip
    schema = pa.schema([("day", pa.date32()), ("symbol", pa.string()), ("peak", pa.float64())])
    for year in range(first, last + 1):
        target = out / f"peaks_{year}.parquet"
        if target.exists():
            continue
        by_day = defaultdict(list)
        for e in pq.read_table(out / f"entries_{year}.parquet").to_pylist():
            if e["timing"] == "after":
                by_day[e["day"]].append(e["symbol"])
        found = []
        for day, symbols in sorted(by_day.items()):
            bars = store.minute(day, symbols=symbols, columns="symbol, minute_et, high, close")
            symbol = bars.column("symbol").to_pylist()
            cols = {n: bars.column(n).to_numpy(zero_copy_only=False) for n in ("minute_et", "high", "close")}
            where: dict = {}
            for i, s in enumerate(symbol):
                where.setdefault(s, [i, i])[1] = i
            for s in symbols:
                a, b = where[s]
                minute, high, price = (cols[n][a : b + 1].astype(float) for n in ("minute_et", "high", "close"))
                regular = np.flatnonzero((minute >= OPEN) & (minute <= CLOSE))
                at = min(max(minute_of[(day, s)] + 30, 990), 1170)
                k = int(np.searchsorted(minute, at)) - 1
                span = (minute > CLOSE) & (np.arange(len(minute)) <= k)
                found.append({"day": day, "symbol": s, "peak": float(high[span].max() / price[regular[-1]])})
        pq.write_table(pa.Table.from_pylist(found, schema=schema), target)
        print(f"{year}: {len(found)}", flush=True)


def limits(first: int, last: int) -> None:
    """Whether a buy order resting at the reading price for 15 minutes was traded through."""
    store = DataStore(load_settings())
    out = folder()
    minute_of = {(r["day"], r["symbol"]): r["minute"] for r in pq.read_table(out / "events.parquet").to_pylist()
                 if r["timing"] == "after"}  # fmt: skip
    schema = pa.schema([("day", pa.date32()), ("symbol", pa.string()), ("filled", pa.bool_()),
                        ("limit_rel", pa.float64()), ("fill_dollars", pa.float64())])  # fmt: skip
    for year in range(first, last + 1):
        target = out / f"limits_{year}.parquet"
        if target.exists():
            continue
        by_day = defaultdict(list)
        for e in pq.read_table(out / f"entries_{year}.parquet").to_pylist():
            if e["timing"] == "after":
                by_day[e["day"]].append(e["symbol"])
        found = []
        for day, symbols in sorted(by_day.items()):
            bars = store.minute(day, symbols=symbols, columns="symbol, minute_et, low, close, volume")
            symbol = bars.column("symbol").to_pylist()
            cols = {n: bars.column(n).to_numpy(zero_copy_only=False) for n in ("minute_et", "low", "close", "volume")}
            where: dict = {}
            for i, s in enumerate(symbol):
                where.setdefault(s, [i, i])[1] = i
            for s in symbols:
                a, b = where[s]
                minute, low, price, volume = (cols[n][a : b + 1].astype(float) for n in ("minute_et", "low", "close", "volume"))
                regular = np.flatnonzero((minute >= OPEN) & (minute <= CLOSE))
                at = min(max(minute_of[(day, s)] + 30, 990), 1170)
                k = int(np.searchsorted(minute, at)) - 1
                later = (np.arange(len(minute)) > k) & (minute <= at + 15)
                through = later & (low < price[k])
                found.append({"day": day, "symbol": s, "filled": bool(through.any()),
                              "limit_rel": float(price[k] / price[regular[-1]]),
                              "fill_dollars": float((price * volume)[through].sum())})  # fmt: skip
        pq.write_table(pa.Table.from_pylist(found, schema=schema), target)
        print(f"{year}: {len(found)} orders, {sum(f['filled'] for f in found)} filled", flush=True)


def load() -> dict[str, np.ndarray]:
    out = folder()
    table = duckdb.sql(
        f"""select n.day, year(n.day) as yr, (date_diff('day', DATE '2003-12-29', n.day) // 7) as week,
                   v.mcap, n.reaction, n.bar_dollars, n.dollars / v.adv as pressure,
                   n.reaction / (p.peak - 1) as hold,
                   exp(v.c_next - v.c) * v.oc_next / n.rel - 1 as g_open,
                   exp(v.c_next - v.c) / n.rel - 1 as g_close,
                   exp(v.c16 - v.c) / n.rel - 1 as g_fifteen,
                   case when v.adv < 1e6 then 0.0025 when v.adv < 1e7 then 0.0010
                        when v.adv < 1e8 then 0.0005 else 0.0002 end
                   + 2 * least(0.01, greatest(0.000175, 0.0035 / n.paid)) as cost
            from read_parquet('{out}/entries_*.parquet') n
            join read_parquet('{out}/peaks_*.parquet') p on p.day = n.day and p.symbol = n.symbol
            join '{out}/events.parquet' v on v.day = n.day and v.symbol = n.symbol and v.timing = n.timing
            where n.timing = 'after' and v.mcap >= 3e8 and n.reaction >= 0.05"""
    ).to_arrow_table()
    return {n: table.column(n).to_numpy(zero_copy_only=False) for n in table.column_names}


def years(d, period):
    first, last = PERIODS[period]
    return (d["yr"] >= first) & (d["yr"] <= last)


def groups(d) -> dict[str, np.ndarray]:
    cut = float(np.median(d["hold"][years(d, "search")]))
    found = {f"pressure {name}": (d["pressure"] >= lo) & (d["pressure"] < hi) for name, (lo, hi) in PRESSURE.items()}
    found["hold kept"] = d["hold"] >= cut
    found["hold faded"] = d["hold"] < cut
    return found, cut


def search() -> None:
    d = load()
    found, cut = groups(d)
    print(f"{int(years(d, 'search').sum())} entries in the search years. Hold median {cut:.3f}.")
    passed = []
    for name, mask in found.items():
        for exit_ in EXITS:
            m = measure(d, mask & years(d, "search"), exit_)
            print(show(f"{name} {exit_}", m))
            if m["n"] >= 150 and m["net"] >= 0.01 and m["t"] >= 3 and m["pos"] >= 6:
                passed.append(f"{name} {exit_}")
    print("\nMeet the search bar:", passed or "none")


def test(kind, name, exit_) -> None:
    d = load()
    found, _ = groups(d)
    mask = found[f"{kind} {name}"]
    net = d[f"g_{exit_}"].astype(float) - d["cost"]
    for period in ("early", "late"):
        keep = mask & years(d, period)
        print(show(f"{kind} {name} {exit_} {period}", measure(d, keep, exit_)))
        for year in sorted(set(d["yr"][keep])):
            mine = keep & (d["yr"] == year)
            print(f"    {year}: {mine.sum():>5}  {100 * net[mine].mean():>6.2f}%")


LIMIT_SIZES = {"small": (5e7, 3e8), "mid": (3e8, 2e9), "large": (2e9, 1e18)}
LIMIT_REACTIONS = {"up5": (0.05, 0.15), "up15": (0.15, 99.0)}


def load_limits() -> dict[str, np.ndarray]:
    out = folder()
    table = duckdb.sql(
        f"""select n.day, year(n.day) as yr, (date_diff('day', DATE '2003-12-29', n.day) // 7) as week,
                   v.mcap, n.reaction, l.fill_dollars as bar_dollars, l.filled,
                   exp(v.c_next - v.c) * v.oc_next / l.limit_rel - 1 as g_open,
                   exp(v.c_next - v.c) / l.limit_rel - 1 as g_close,
                   exp(v.c16 - v.c) / l.limit_rel - 1 as g_fifteen,
                   case when v.adv < 1e6 then 0.0025 when v.adv < 1e7 then 0.0010
                        when v.adv < 1e8 then 0.0005 else 0.0002 end
                   + 2 * least(0.01, greatest(0.000175, 0.0035 / n.paid)) as cost
            from read_parquet('{out}/entries_*.parquet') n
            join read_parquet('{out}/limits_*.parquet') l on l.day = n.day and l.symbol = n.symbol
            join '{out}/events.parquet' v on v.day = n.day and v.symbol = n.symbol and v.timing = n.timing
            where n.timing = 'after' and n.reaction >= 0.05"""
    ).to_arrow_table()
    return {n: table.column(n).to_numpy(zero_copy_only=False) for n in table.column_names}


def limit_cell(d, size, reaction, period):
    small, big = LIMIT_SIZES[size]
    lo, hi = LIMIT_REACTIONS[reaction]
    return ((d["mcap"] >= small) & (d["mcap"] < big) & (d["reaction"] >= lo) & (d["reaction"] < hi)
            & years(d, period))  # fmt: skip


def limit_search() -> None:
    d = load_limits()
    passed = []
    for size in LIMIT_SIZES:
        for reaction in LIMIT_REACTIONS:
            orders = limit_cell(d, size, reaction, "search")
            keep = orders & d["filled"]
            for exit_ in EXITS:
                m = measure(d, keep, exit_)
                label = f"limit {size} {reaction} {exit_}"
                print(show(label, m) + f"  filled {100 * keep.sum() / max(1, orders.sum()):.0f}%")
                if m["n"] >= 150 and m["net"] >= 0.01 and m["t"] >= 3 and m["pos"] >= 6:
                    passed.append(label)
    print("\nMeet the search bar:", passed or "none")


def limit_test(size, reaction, exit_) -> None:
    d = load_limits()
    net = d[f"g_{exit_}"].astype(float) - d["cost"]
    for period in ("early", "late"):
        keep = limit_cell(d, size, reaction, period) & d["filled"]
        print(show(f"limit {size} {reaction} {exit_} {period}", measure(d, keep, exit_)))
        for year in sorted(set(d["yr"][keep])):
            mine = keep & (d["yr"] == year)
            print(f"    {year}: {mine.sum():>5}  {100 * net[mine].mean():>6.2f}%")


def hedged() -> None:
    """The large-company cell with SPY sold short over the same sessions."""
    store = DataStore(load_settings())
    spy = duckdb.sql(
        f"""select date, lead(close, 16) over (order by date) / close - 1 as r
            from read_parquet('{store.bars_roots[0]}/daily/*.parquet') where symbol = 'SPY'"""
    ).fetchall()
    market = {day: r for day, r in spy if r is not None}
    for name, d in (("high", load()), ("limit", load_limits())):
        fund = np.array([market.get(day, np.nan) for day in d["day"].astype(object)])
        d["g_hedged"] = d["g_fifteen"].astype(float) - fund - 0.0003
        base = (d["mcap"] >= 2e9) & (d["reaction"] < 0.15) & ~np.isnan(fund)
        if name == "limit":
            base &= d["filled"]
        net = d["g_hedged"] - d["cost"]
        for period in sys.argv[2:]:
            keep = base & years(d, period)
            print(show(f"{name} large up5 hedged {period}", measure(d, keep, "hedged")))
            for year in sorted(set(d["yr"][keep])):
                mine = keep & (d["yr"] == year)
                print(f"    {year}: {mine.sum():>5}  {100 * net[mine].mean():>6.2f}%")


if __name__ == "__main__":
    if sys.argv[1] == "limits":
        limits(int(sys.argv[2]), int(sys.argv[3]))
    elif sys.argv[1] == "peaks":
        peaks(int(sys.argv[2]), int(sys.argv[3]))
    elif sys.argv[1] == "search":
        search()
    elif sys.argv[1] == "hedged":
        hedged()
    elif sys.argv[1] == "limit_search":
        limit_search()
    elif sys.argv[1] == "limit_test":
        limit_test(*sys.argv[2:5])
    else:
        test(*sys.argv[2:5])
