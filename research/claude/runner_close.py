"""strategies/runner_close/HYPOTHESIS.md: a stock that has run 30% or more on the day, read
at 15:00, into the close and overnight.

    cd research/claude
    uv run python runner_close.py events
    uv run python runner_close.py collect 2005 2023
    uv run python runner_close.py search
    uv run python runner_close.py test fading run60 short_close
"""

from __future__ import annotations

import sys
import tempfile
from collections import defaultdict

import duckdb
import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
from swing_earnings import weekly

from kinn.core.settings import load_settings
from kinn.data.store import DataStore

OPEN, CLOSE, READ = 570, 960, 900
RUNS = {"run30": (0.30, 0.60), "run60": (0.60, 99.0)}
TRADES = {"holding": ("buy_close", "buy_open", "buy_next", "night_short"),
          "fading": ("short_close", "short_open", "bounce", "night_short")}  # fmt: skip
PERIODS = {"search": (2010, 2017), "early": (2005, 2009), "late": (2018, 2022), "check": (2023, 2023)}


def folder():
    out = load_settings().data_dir / "research" / "runner_close"
    out.mkdir(parents=True, exist_ok=True)
    return out


def events() -> None:
    """Sessions whose high reached 30% over the previous close on heavy volume (the reading
    at 15:00 comes from the minute bars), with the daily figures the returns need."""
    store = DataStore(load_settings())
    con = duckdb.connect()
    con.execute(f"set threads=3; set memory_limit='1500MB'; set temp_directory='{tempfile.mkdtemp()}'")
    con.execute(
        f"""copy (
            with p as (
                select permaticker, date, symbol, adv20_prev as adv, marketcap_prev as mcap, high,
                       prev_close, dollar_volume as dv, open / close as oc,
                       sum(ln(close / prev_close)) over w as c
                from read_parquet('{store.root}/panel/*.parquet')
                where prev_close > 0 and close > 0 and low > 0 and open > 0
                  and category like '%Common Stock%'
                window w as (partition by permaticker order by date)),
            q as (select *, lag(c) over w as c_prev, lead(c) over w as c_next, lead(oc) over w as oc_next
                  from p window w as (partition by permaticker order by date))
            select date as day, symbol, adv, mcap, c, c_prev, c_next, oc_next
            from q
            where date between DATE '2005-01-03' and DATE '2023-10-13' and mcap >= 5e7 and adv >= 250000
              and high >= 1.3 * prev_close and dv >= 3 * adv and c_prev is not null and c_next is not null
            order by day, symbol
        ) to '{folder()}/events.parquet' (format parquet)"""
    )
    print(con.sql(f"select count(*), count(distinct day) from '{folder()}/events.parquet'").fetchall())


def collect(first: int, last: int) -> None:
    store = DataStore(load_settings())
    out = folder()
    by_day = defaultdict(list)
    for row in pq.read_table(out / "events.parquet").to_pylist():
        by_day[row["day"]].append(row)
    names = ("day", "symbol", "run", "off_high", "buy", "sell", "last", "volume_x")
    for year in range(first, last + 1):
        target = out / f"entries_{year}.parquet"
        if target.exists():
            continue
        found = []
        for day in sorted(d for d in by_day if d.year == year):
            rows = by_day[day]
            try:
                bars = store.minute(day, symbols=[r["symbol"] for r in rows],
                                    columns="symbol, minute_et, high, low, close, volume")  # fmt: skip
            except FileNotFoundError:
                continue
            symbol = bars.column("symbol").to_pylist()
            cols = {n: bars.column(n).to_numpy(zero_copy_only=False) for n in ("minute_et", "high", "low", "close", "volume")}
            where: dict = {}
            for i, s in enumerate(symbol):
                where.setdefault(s, [i, i])[1] = i
            for r in rows:
                span = where.get(r["symbol"])
                if not span:
                    continue
                minute, high, low, price, volume = (cols[n][span[0] : span[1] + 1].astype(float) for n in ("minute_et", "high", "low", "close", "volume"))
                regular = np.flatnonzero((minute >= OPEN) & (minute <= CLOSE))
                before = np.flatnonzero((minute >= OPEN) & (minute < READ))
                e = int(np.searchsorted(minute, READ))
                if not len(regular) or not len(before) or e >= len(minute) or minute[e] > READ + 5:
                    continue
                last_price = price[regular[-1]]
                previous = last_price / float(np.exp(r["c"] - r["c_prev"]))  # yesterday's close, in today's prices
                top = high[before].max()
                dollars = float(np.dot(price[: before[-1] + 1], volume[: before[-1] + 1]))
                if low[e] < 1:
                    continue
                found.append((day, r["symbol"], top / previous - 1, 1 - price[before[-1]] / top,
                              float(high[e] / last_price), float(low[e] / last_price), float(last_price),
                              dollars / r["adv"]))  # fmt: skip
        table = pa.table({n: [f[i] for f in found] for i, n in enumerate(names)}) if found else pa.table({n: [] for n in names})
        pq.write_table(table, target)
        print(f"{year}: {len(found)} readings", flush=True)


def load() -> dict[str, np.ndarray]:
    """Every runner at 15:00 with each trade's return to its taker after costs."""
    out = folder()
    cost = """(case when v.adv < 1e6 then 0.0025 when v.adv < 1e7 then 0.0010
                    when v.adv < 1e8 then 0.0005 else 0.0002 end)"""
    fee = "least(0.01, greatest(0.000175, 0.0035 / n.last))"
    table = duckdb.sql(
        f"""select n.day, year(n.day) as yr, (date_diff('day', DATE '2003-12-29', n.day) // 7) as week,
                   n.run, n.off_high, n.volume_x,
                   1 / n.buy - 1 - {cost} - 2 * {fee} as buy_close,
                   exp(v.c_next - v.c) * v.oc_next / n.buy - 1 - {cost} - 2 * {fee} as buy_open,
                   exp(v.c_next - v.c) / n.buy - 1 - {cost} - 2 * {fee} as buy_next,
                   1 - 1 / n.sell - {cost} - 2 * {fee} as short_close,
                   1 - exp(v.c_next - v.c) * v.oc_next / n.sell - {cost} - 2 * {fee} as short_open,
                   exp(v.c_next - v.c) * v.oc_next - 1 - 2 * {cost} - 2 * {fee} as bounce,
                   1 - exp(v.c_next - v.c) * v.oc_next - 2 * {cost} - 2 * {fee} as night_short
            from read_parquet('{out}/entries_*.parquet') n
            join '{out}/events.parquet' v on v.day = n.day and v.symbol = n.symbol
            where n.run >= 0.30 and n.volume_x >= 5"""
    ).to_arrow_table()
    return {n: table.column(n).to_numpy(zero_copy_only=False) for n in table.column_names}


def pick(d, state, run, period):
    lo, hi = RUNS[run]
    first, last = PERIODS[period]
    where = d["off_high"] <= 0.10 if state == "holding" else d["off_high"] >= 0.25
    return where & (d["run"] >= lo) & (d["run"] < hi) & (d["yr"] >= first) & (d["yr"] <= last)


def measure(d, keep, trade) -> dict:
    n = int(keep.sum())
    if n < 3:
        return {"n": n}
    net = d[trade][keep].astype(float)
    _, t, _ = weekly(net, d["week"][keep])
    years = d["yr"][keep]
    positive = sum(net[years == y].mean() > 0 for y in set(years))
    return {"n": n, "net": net.mean(), "median": np.median(net), "t": t, "pos": positive,
            "years": len(set(years)), "wins": (net > 0).mean(), "worst": net.min(),
            "worst1": np.sort(net)[: max(1, n // 100)].mean()}  # fmt: skip


def show(label, m) -> str:
    if m["n"] < 3:
        return f"{label:30} {m['n']:>5}"
    return (f"{label:30} {m['n']:>5}  net {100 * m['net']:>6.2f}%  median {100 * m['median']:>6.2f}%  "
            f"t {m['t']:>5.2f}  yrs {m['pos']} of {m['years']}  wins {100 * m['wins']:>3.0f}%  "
            f"worst {100 * m['worst']:>5.0f}%  worst 1% {100 * m['worst1']:>5.0f}%")  # fmt: skip


def search() -> None:
    d = load()
    between = (d["off_high"] > 0.10) & (d["off_high"] < 0.25)
    print(f"{len(d['day'])} runners at 15:00 ({int(between.sum())} between the two states). Search years 2010 to 2017.")
    passed = []
    for state, trades in TRADES.items():
        for run in RUNS:
            keep = pick(d, state, run, "search")
            for trade in trades:
                m = measure(d, keep, trade)
                label = f"{state} {run} {trade}"
                print(show(label, m))
                if m["n"] >= 150 and m["net"] >= 0.01 and m["t"] >= 3 and m["pos"] >= 6:
                    passed.append(label)
    print("\nMeet the search bar:", passed or "none")


def test(state, run, trade) -> None:
    d = load()
    for period in ("early", "late"):
        keep = pick(d, state, run, period)
        print(show(f"{state} {run} {trade} {period}", measure(d, keep, trade)))
        for year in sorted(set(d["yr"][keep])):
            mine = keep & (d["yr"] == year)
            print(f"    {year}: {mine.sum():>5}  {100 * d[trade][mine].astype(float).mean():>6.2f}%")


if __name__ == "__main__":
    command = sys.argv[1]
    if command == "events":
        events()
    elif command == "collect":
        collect(int(sys.argv[2]), int(sys.argv[3]))
    elif command == "search":
        search()
    else:
        test(*sys.argv[2:5])
