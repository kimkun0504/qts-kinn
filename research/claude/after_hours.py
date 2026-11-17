"""strategies/after_hours/HYPOTHESIS.md: buying an earnings reaction outside the regular
session, at the worst price of the minute.

    cd research/claude
    uv run python after_hours.py events
    uv run python after_hours.py collect 2005 2023
    uv run python after_hours.py search
    uv run python after_hours.py test after small up15 open
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

import sec_times
from kinn.core.settings import load_settings
from kinn.data.store import DataStore

OPEN, CLOSE = 570, 960
MIN_DOLLARS = 50000.0
SIZES = {"small": (5e7, 3e8), "mid": (3e8, 2e9), "large": (2e9, 1e18)}
REACTIONS = {"up5": (0.05, 0.15), "up15": (0.15, 99.0)}
PATHS = {"down5": (-9.0, -0.05), "flat": (-0.05, 0.05), **REACTIONS}
EXITS = {"after": ("open", "close", "fifteen"), "before": ("close", "fifteen")}
PERIODS = {"search": (2010, 2017), "early": (2005, 2009), "late": (2018, 2022), "check": (2023, 2023)}


def folder():
    out = load_settings().data_dir / "research" / "after_hours"
    out.mkdir(parents=True, exist_ok=True)
    return out


def events() -> None:
    """(stock, D, timing, minute): an earnings 8-K accepted after the close or before the
    open of session D, with the daily figures the returns need."""
    settings = load_settings()
    store = DataStore(settings)
    stocks, days = sec_times.numbers(), set(sec_times.sessions())
    found: dict = {}
    for row in sec_times.filings("8k.jsonl.gz"):
        if row["form"] != "8-K" or row["cik"] not in stocks or "2.02" not in row["items"].split(","):
            continue
        when = sec_times.accepted(row)
        if not when or when[0] not in days:
            continue
        day, minute = when
        timing = "after" if 960 <= minute <= 1110 else "before" if 360 <= minute <= 510 else None
        if timing:
            for permaticker in stocks[row["cik"]]:
                key = (permaticker, day, timing)
                found[key] = min(found.get(key, minute), minute)
    table = pa.table({"permaticker": [k[0] for k in found], "day": [k[1] for k in found],
                      "timing": [k[2] for k in found], "minute": list(found.values())})  # fmt: skip
    con = duckdb.connect()
    con.execute(f"set threads=3; set memory_limit='1500MB'; set temp_directory='{tempfile.mkdtemp()}'")
    con.register("filings", table)
    con.execute(
        f"""copy (
            with p as (
                select permaticker, date, symbol, adv20_prev as adv, marketcap_prev as mcap,
                       open / close as oc, sum(ln(close / prev_close)) over w as c
                from read_parquet('{store.root}/panel/*.parquet')
                where prev_close > 0 and close > 0 and low > 0 and open > 0
                  and category like '%Common Stock%'
                window w as (partition by permaticker order by date)),
            q as (
                select *, lag(c) over w as c_prev, lead(c) over w as c_next, lead(oc) over w as oc_next,
                       last_value(c) over (partition by permaticker order by date
                                           rows between current row and 15 following) as c15,
                       last_value(c) over (partition by permaticker order by date
                                           rows between current row and 16 following) as c16
                from p window w as (partition by permaticker order by date))
            select q.date as day, q.symbol, f.timing, f.minute, q.adv, q.mcap, q.c, q.c_prev,
                   q.c_next, q.oc_next, q.c15, q.c16
            from q join filings f on f.permaticker = q.permaticker and f.day = q.date
            where q.date between DATE '2005-01-03' and DATE '2023-10-13'
              and q.mcap >= 5e7 and q.adv >= 250000 and q.c_prev is not null and q.c_next is not null
            qualify row_number() over (partition by q.symbol, q.date, f.timing order by q.adv desc) = 1
            order by day, symbol
        ) to '{folder()}/events.parquet' (format parquet)"""
    )
    print(con.sql(f"select timing, count(*) from '{folder()}/events.parquet' group by 1 order by 1").fetchall())


def collect(first: int, last: int) -> None:
    store = DataStore(load_settings())
    out = folder()
    by_day = defaultdict(list)
    for row in pq.read_table(out / "events.parquet").to_pylist():
        by_day[row["day"]].append(row)
    schema = pa.schema([("day", pa.date32()), ("symbol", pa.string()), ("timing", pa.string()),
                        ("reaction", pa.float64()), ("paid", pa.float64()), ("rel", pa.float64()),
                        ("dollars", pa.float64()), ("bar_dollars", pa.float64())])  # fmt: skip
    for year in range(first, last + 1):
        target = out / f"entries_{year}.parquet"
        if target.exists():
            continue
        found = []
        for day in sorted(d for d in by_day if d.year == year):
            rows = by_day[day]
            try:
                bars = store.minute(day, symbols=list({r["symbol"] for r in rows}),
                                    columns="symbol, minute_et, high, close, volume")  # fmt: skip
            except FileNotFoundError:
                continue
            symbol = bars.column("symbol").to_pylist()
            cols = {n: bars.column(n).to_numpy(zero_copy_only=False) for n in ("minute_et", "high", "close", "volume")}
            where: dict = {}
            for i, s in enumerate(symbol):
                where.setdefault(s, [i, i])[1] = i
            for r in rows:
                span = where.get(r["symbol"])
                if not span:
                    continue
                minute, high, price, volume = (cols[n][span[0] : span[1] + 1].astype(float) for n in ("minute_et", "high", "close", "volume"))
                regular = np.flatnonzero((minute >= OPEN) & (minute <= CLOSE))
                if not len(regular):
                    continue
                last_price = price[regular[-1]]
                if r["timing"] == "after":
                    at = min(max(r["minute"] + 30, 990), 1170)
                    base, session = last_price, minute > CLOSE
                else:
                    at = 540
                    base, session = last_price / float(np.exp(r["c"] - r["c_prev"])), minute < OPEN
                k = int(np.searchsorted(minute, at)) - 1  # the last bar before the reading
                e = k + 1
                if k < 0 or not session[k] or e >= len(minute) or not session[e] or minute[e] > at + 20:
                    continue
                traded = float(np.dot(price[: k + 1] * session[: k + 1], volume[: k + 1]))
                if traded < MIN_DOLLARS or high[e] < 1:
                    continue
                found.append({"day": day, "symbol": r["symbol"], "timing": r["timing"],
                              "reaction": price[k] / base - 1, "paid": float(high[e]),
                              "rel": float(high[e] / last_price), "dollars": traded,
                              "bar_dollars": float(price[e] * volume[e])})  # fmt: skip
        pq.write_table(pa.Table.from_pylist(found, schema=schema), target)
        print(f"{year}: {len(found)} entries", flush=True)


def collect_lows(first: int, last: int) -> None:
    """The low of each entry minute (what a short seller would have received), for the
    entries already collected."""
    store = DataStore(load_settings())
    out = folder()
    events_by = {(r["day"], r["symbol"], r["timing"]): r for r in pq.read_table(out / "events.parquet").to_pylist()}
    for year in range(first, last + 1):
        target = out / f"lows_{year}.parquet"
        if target.exists():
            continue
        entries = [e for e in pq.read_table(out / f"entries_{year}.parquet").to_pylist() if e["timing"] == "after"]
        by_day = defaultdict(list)
        for e in entries:
            by_day[e["day"]].append(e)
        found = []
        for day, rows in sorted(by_day.items()):
            bars = store.minute(day, symbols=list({r["symbol"] for r in rows}), columns="symbol, minute_et, low, close")
            symbol = bars.column("symbol").to_pylist()
            cols = {n: bars.column(n).to_numpy(zero_copy_only=False) for n in ("minute_et", "low", "close")}
            where: dict = {}
            for i, s in enumerate(symbol):
                where.setdefault(s, [i, i])[1] = i
            for r in rows:
                span = where[r["symbol"]]
                minute, low, price = (cols[n][span[0] : span[1] + 1].astype(float) for n in ("minute_et", "low", "close"))
                regular = np.flatnonzero((minute >= OPEN) & (minute <= CLOSE))
                at = min(max(events_by[(day, r["symbol"], "after")]["minute"] + 30, 990), 1170)
                e = int(np.searchsorted(minute, at))
                found.append({"day": day, "symbol": r["symbol"], "rel_low": float(low[e] / price[regular[-1]])})
        pq.write_table(pa.Table.from_pylist(found, schema=pa.schema([("day", pa.date32()), ("symbol", pa.string()), ("rel_low", pa.float64())])), target)
        print(f"{year}: {len(found)}", flush=True)


SHORT_REACTIONS = {"down5": (-0.15, -0.05), "down15": (-9.0, -0.15)}
BORROW_NIGHT = 0.10 / 252


def load_short() -> dict[str, np.ndarray]:
    out = folder()
    table = duckdb.sql(
        f"""select n.day, year(n.day) as yr, (date_diff('day', DATE '2003-12-29', n.day) // 7) as week,
                   v.mcap, n.reaction, n.bar_dollars,
                   1 - exp(v.c_next - v.c) * v.oc_next / w.rel_low as g_open,
                   1 - exp(v.c_next - v.c) / w.rel_low as g_close,
                   case when v.adv < 1e6 then 0.0025 when v.adv < 1e7 then 0.0010
                        when v.adv < 1e8 then 0.0005 else 0.0002 end
                   + 2 * least(0.01, greatest(0.000175, 0.0035 / n.paid)) + {BORROW_NIGHT} as cost
            from read_parquet('{out}/entries_*.parquet') n
            join read_parquet('{out}/lows_*.parquet') w on w.day = n.day and w.symbol = n.symbol
            join '{out}/events.parquet' v on v.day = n.day and v.symbol = n.symbol and v.timing = n.timing
            where n.timing = 'after'"""
    ).to_arrow_table()
    d = {n: table.column(n).to_numpy(zero_copy_only=False) for n in table.column_names}
    d["timing"] = np.array(["after"] * len(d["day"]))
    return d


def tail(d, keep, exit_) -> str:
    net = np.sort(d[f"g_{exit_}"][keep].astype(float) - d["cost"][keep])
    return f"worst {100 * net[0]:.0f}%, worst 1% {100 * net[: max(1, len(net) // 100)].mean():.0f}%"


def search_short() -> None:
    d = load_short()
    print(f"{len(d['day'])} entries after the close. Sold short at the minute's low. Search years 2010 to 2017.")
    passed = []
    for size in SIZES:
        for reaction in SHORT_REACTIONS:
            keep = pick(d, "after", size, reaction, "search", SHORT_REACTIONS)
            for exit_ in ("open", "close"):
                m = measure(d, keep, exit_)
                label = f"short {size} {reaction} {exit_}"
                print(show(label, m) + (f"  {tail(d, keep, exit_)}" if m["n"] >= 3 else ""))
                if m["n"] >= 150 and m["net"] >= 0.01 and m["t"] >= 3 and m["pos"] >= 6:
                    passed.append(label)
    print("\nMeet the search bar:", passed or "none")


def test_short(size, reaction, exit_) -> None:
    d = load_short()
    for period in ("early", "late"):
        keep = pick(d, "after", size, reaction, period, SHORT_REACTIONS)
        print(show(f"short {size} {reaction} {exit_} {period}", measure(d, keep, exit_)) + f"  {tail(d, keep, exit_)}")
        net = d[f"g_{exit_}"].astype(float) - d["cost"]
        for year in sorted(set(d["yr"][keep])):
            mine = keep & (d["yr"] == year)
            print(f"    {year}: {mine.sum():>5}  {100 * net[mine].mean():>6.2f}%")


def load() -> dict[str, np.ndarray]:
    out = folder()
    table = duckdb.sql(
        f"""select n.day, year(n.day) as yr, (date_diff('day', DATE '2003-12-29', n.day) // 7) as week,
                   n.timing, v.mcap, n.reaction, n.bar_dollars,
                   case when n.timing = 'after' then exp(v.c_next - v.c) * v.oc_next / n.rel - 1 end as g_open,
                   case when n.timing = 'after' then exp(v.c_next - v.c) / n.rel - 1
                        else 1 / n.rel - 1 end as g_close,
                   case when n.timing = 'after' then exp(v.c16 - v.c) / n.rel - 1
                        else exp(v.c15 - v.c) / n.rel - 1 end as g_fifteen,
                   case when v.adv < 1e6 then 0.0025 when v.adv < 1e7 then 0.0010
                        when v.adv < 1e8 then 0.0005 else 0.0002 end
                   + 2 * least(0.01, greatest(0.000175, 0.0035 / n.paid)) as cost
            from read_parquet('{out}/entries_*.parquet') n
            join '{out}/events.parquet' v on v.day = n.day and v.symbol = n.symbol and v.timing = n.timing"""
    ).to_arrow_table()
    return {n: table.column(n).to_numpy(zero_copy_only=False) for n in table.column_names}


def pick(d, timing, size, reaction, period, groups=REACTIONS):
    lo, hi = groups[reaction]
    small, big = SIZES[size]
    first, last = PERIODS[period]
    return ((d["timing"] == timing) & (d["reaction"] >= lo) & (d["reaction"] < hi)
            & (d["mcap"] >= small) & (d["mcap"] < big) & (d["yr"] >= first) & (d["yr"] <= last))  # fmt: skip


def measure(d, keep, exit_) -> dict:
    n = int(keep.sum())
    if n < 3:
        return {"n": n}
    gross = d[f"g_{exit_}"][keep].astype(float)
    net = gross - d["cost"][keep]
    _, t, _ = weekly(net, d["week"][keep])
    years = d["yr"][keep]
    positive = sum(net[years == y].mean() > 0 for y in set(years))
    return {"n": n, "gross": gross.mean(), "net": net.mean(), "t": t, "pos": positive,
            "years": len(set(years)), "wins": (net > 0).mean(), "median": np.median(net),
            "thin": (d["bar_dollars"][keep] < 5000).mean()}  # fmt: skip


def show(label, m) -> str:
    if m["n"] < 3:
        return f"{label:30} {m['n']:>6}"
    return (f"{label:30} {m['n']:>6}  gross {100 * m['gross']:>6.2f}%  net {100 * m['net']:>6.2f}%  "
            f"median {100 * m['median']:>6.2f}%  t {m['t']:>5.2f}  yrs {m['pos']} of {m['years']}  "
            f"wins {100 * m['wins']:>3.0f}%  thin minute {100 * m['thin']:>3.0f}%")  # fmt: skip


def search() -> None:
    d = load()
    print(f"{len(d['day'])} entries. Search years 2010 to 2017. Bought at the minute's high.\n")
    print("The path by reaction, every size (mean before exit costs, from the minute's high):")
    for timing in EXITS:
        for reaction in PATHS:
            keep = np.zeros(len(d["day"]), bool)
            for size in SIZES:
                keep |= pick(d, timing, size, reaction, "search", PATHS)
            cells = []
            for exit_ in EXITS[timing]:
                m = measure(d, keep, exit_)
                cells.append(f"{exit_} {100 * m['gross']:>6.2f}%" if m["n"] >= 3 else exit_)
            print(f"  {timing:6} {reaction:6} {int(keep.sum()):>6}  " + "   ".join(cells))
    print()
    passed = []
    for timing, exits in EXITS.items():
        for size in SIZES:
            for reaction in REACTIONS:
                keep = pick(d, timing, size, reaction, "search")
                for exit_ in exits:
                    m = measure(d, keep, exit_)
                    label = f"{timing} {size} {reaction} {exit_}"
                    print(show(label, m))
                    if m["n"] >= 150 and m["net"] >= 0.01 and m["t"] >= 3 and m["pos"] >= 6:
                        passed.append(label)
    print("\nMeet the search bar:", passed or "none")


def test(timing, size, reaction, exit_) -> None:
    d = load()
    for period in ("early", "late"):
        keep = pick(d, timing, size, reaction, period)
        print(show(f"{timing} {size} {reaction} {exit_} {period}", measure(d, keep, exit_)))
        net = d[f"g_{exit_}"].astype(float) - d["cost"]
        for year in sorted(set(d["yr"][keep])):
            mine = keep & (d["yr"] == year)
            print(f"    {year}: {mine.sum():>5}  {100 * net[mine].mean():>6.2f}%")


if __name__ == "__main__":
    command = sys.argv[1]
    if command == "events":
        events()
    elif command == "collect":
        collect(int(sys.argv[2]), int(sys.argv[3]))
    elif command == "lows":
        collect_lows(int(sys.argv[2]), int(sys.argv[3]))
    elif command == "search_short":
        search_short()
    elif command == "test_short":
        test_short(*sys.argv[2:5])
    elif command == "search":
        search()
    else:
        test(*sys.argv[2:6])
