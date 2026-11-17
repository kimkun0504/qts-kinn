"""Family news_hours (strategies/news_hours/HYPOTHESIS.md): what a stock does in the hours
and days after an 8-K becomes public, by the SEC's acceptance time.

    cd research/claude
    uv run python news_hours.py events
    uv run python news_hours.py collect 2005 2023     # by year, resumable
    uv run python news_hours.py search                # the 360 cells on 2010 to 2017
    uv run python news_hours.py test during_A up5 results small close
"""

from __future__ import annotations

import bisect
import csv
import gzip
import io
import json
import re
import sys
import tempfile
import zipfile
from collections import defaultdict
from datetime import UTC, datetime
from zoneinfo import ZoneInfo

import duckdb
import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
from swing_earnings import weekly

from kinn.core.settings import load_settings
from kinn.data.store import DataStore

FIRST, LAST = "2005-01-03", "2023-10-13"
OPEN, CLOSE = 570, 960
NEW_YORK = ZoneInfo("America/New_York")
KINDS = ("results", "agreements", "announcements", "other")
SIZES = {"small": (5e7, 3e8), "mid": (3e8, 2e9), "large": (2e9, 1e18)}
REACTIONS = {"down5": (-9, -0.05), "down2": (-0.05, -0.02), "flat": (-0.02, 0.02),
             "up2": (0.02, 0.05), "up5": (0.05, 99)}  # fmt: skip
READINGS = ("during_A", "during_B", "before_B")
EXITS = ("close", "five")
PERIODS = {"search": (2010, 2017), "early": (2005, 2009), "late": (2018, 2022), "check": (2023, 2023)}


def folder(settings):
    out = settings.data_dir / "research" / "news_hours"
    out.mkdir(parents=True, exist_ok=True)
    return out


def kind_of(items: str) -> int:
    found = set(items.split(","))
    if "2.02" in found:
        return 0
    if "1.01" in found:
        return 1
    return 2 if found & {"7.01", "8.01"} else 3


def events() -> None:
    """One event a stock a session: the first chance to act on an 8-K, with the daily figures
    the returns need (prices as log levels, so splits do not matter)."""
    settings = load_settings()
    store = DataStore(settings)
    sessions = store.sessions(datetime(2004, 12, 1).date(), datetime(2023, 11, 8).date())
    is_session = set(sessions)
    # The SEC number of each stock, from Sharadar's ticker table.
    raw = max((settings.raw_dir / "sharadar").iterdir())
    archive = next(raw.glob("SHARADAR_TICKERS_*.zip"))
    numbers = defaultdict(set)
    with zipfile.ZipFile(archive) as z, z.open(z.namelist()[0]) as handle:
        for row in csv.DictReader(io.TextIOWrapper(handle, "utf-8")):
            match = re.search(r"CIK=0*(\d+)", row.get("secfilings") or "")
            if match and row["table"] == "SEP":
                numbers[int(match.group(1))].add(int(row["permaticker"]))
    found: dict = {}
    with gzip.open(settings.raw_dir / "sec" / "filing_times" / "8k.jsonl.gz", "rt") as handle:
        for line in handle:
            row = json.loads(line)
            if row["form"] != "8-K" or row["cik"] not in numbers or not row["accepted"]:
                continue
            when = datetime.strptime(row["accepted"][:19], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=UTC)
            local = when.astimezone(NEW_YORK)
            day, minute = local.date(), local.hour * 60 + local.minute
            if day in is_session and OPEN <= minute <= 925:
                timing, session = "during", day
            elif day in is_session and 925 < minute or day not in is_session or minute < 565:
                at = bisect.bisect_left(sessions, day) if day in is_session and minute < 565 else bisect.bisect_right(sessions, day)
                if at >= len(sessions) or (sessions[at] - day).days > 5:
                    continue
                timing, session, minute = "before", sessions[at], 0
            else:
                continue  # 09:25 to 09:30: neither
            for permaticker in numbers[row["cik"]]:
                key = (permaticker, session)
                kind = kind_of(row["items"])
                old = found.get(key)
                if old is None:
                    found[key] = [timing, minute, kind]
                else:  # the first chance to act wins; the kind is the most specific seen
                    if (timing, minute) < (old[0], old[1]):
                        old[0], old[1] = timing, minute
                    old[2] = min(old[2], kind)
    table = pa.table({
        "permaticker": [k[0] for k in found], "day": [k[1] for k in found],
        "timing": [v[0] for v in found.values()], "minute": [v[1] for v in found.values()],
        "kind": [KINDS[v[2]] for v in found.values()],
    })  # fmt: skip
    con = duckdb.connect()
    con.execute(f"set threads=3; set memory_limit='1500MB'; set temp_directory='{tempfile.mkdtemp()}'")
    con.register("filings", table)
    con.execute(
        f"""copy (
            with p as (
                select permaticker, date, symbol, adv20_prev as adv, marketcap_prev as mcap,
                       sum(ln(close / prev_close)) over w as c
                from read_parquet('{store.root}/panel/*.parquet')
                where prev_close > 0 and close > 0 and low > 0 and open > 0
                  and category like '%Common Stock%'
                window w as (partition by permaticker order by date)),
            q as (
                select *, lag(c) over w as c1,
                       last_value(c) over (partition by permaticker order by date
                                           rows between current row and 5 following) as c5
                from p window w as (partition by permaticker order by date))
            select q.date as day, q.symbol, q.permaticker, f.timing, f.minute, f.kind,
                   q.adv, q.mcap, q.c, q.c1, q.c5
            from q join filings f on f.permaticker = q.permaticker and f.day = q.date
            where q.date between DATE '{FIRST}' and DATE '{LAST}'
              and q.mcap >= 5e7 and q.adv >= 250000 and q.c1 is not null
            qualify row_number() over (partition by q.symbol, q.date order by q.adv desc) = 1
            order by day, symbol
        ) to '{folder(settings)}/events.parquet' (format parquet)"""
    )
    print(con.sql(f"select timing, kind, count(*) from '{folder(settings)}/events.parquet' group by all order by all").fetchall())


def collect(first: int, last: int) -> None:
    settings = load_settings()
    store = DataStore(settings)
    out = folder(settings)
    by_day = defaultdict(list)
    for row in pq.read_table(out / "events.parquet").to_pylist():
        by_day[row["day"]].append(row)
    for year in range(first, last + 1):
        target = out / f"entries_{year}.parquet"
        if target.exists():
            continue
        found = []
        for day in sorted(d for d in by_day if d.year == year):
            rows = by_day[day]
            try:
                bars = store.minute(day, symbols=[r["symbol"] for r in rows],
                                    columns="symbol, minute_et, open, close")  # fmt: skip
            except FileNotFoundError:
                continue
            symbol = bars.column("symbol").to_pylist()
            cols = {n: bars.column(n).to_numpy(zero_copy_only=False) for n in ("minute_et", "open", "close")}
            where: dict = {}
            for i, s in enumerate(symbol):
                where.setdefault(s, [i, i])[1] = i
            for r in rows:
                span = where.get(r["symbol"])
                if not span:
                    continue
                minute, opens, price = (cols[n][span[0] : span[1] + 1].astype(float) for n in ("minute_et", "open", "close"))
                regular = np.flatnonzero((minute >= OPEN) & (minute <= CLOSE))
                if not len(regular):
                    continue
                last_price = price[regular[-1]]
                previous = last_price / float(np.exp(r["c"] - r["c1"]))  # yesterday's close, in today's prices
                at = r["minute"] + 5 if r["timing"] == "during" else OPEN + 5
                k = int(np.searchsorted(minute, at)) - 1  # the last bar before the reading
                e = k + 1
                if k < 0 or minute[k] < OPEN or e >= len(minute) or minute[e] > at + 10 or minute[e] >= CLOSE - 5:
                    continue
                since_filing = None
                if r["timing"] == "during":
                    b = int(np.searchsorted(minute, r["minute"])) - 1  # the last bar before the filing
                    if b >= 0 and minute[b] >= max(OPEN, r["minute"] - 30):
                        since_filing = price[k] / price[b] - 1
                if opens[e] < 1:
                    continue
                found.append({"day": day, "symbol": r["symbol"], "since_filing": since_filing,
                              "since_close": price[k] / previous - 1, "paid": float(opens[e]),
                              "rel": float(opens[e] / last_price)})  # fmt: skip
        pq.write_table(pa.Table.from_pylist(found, schema=pa.schema([
            ("day", pa.date32()), ("symbol", pa.string()), ("since_filing", pa.float64()),
            ("since_close", pa.float64()), ("paid", pa.float64()), ("rel", pa.float64())])), target)  # fmt: skip
        print(f"{year}: {len(found)} entries", flush=True)


def load() -> dict[str, np.ndarray]:
    """Every entry with its two returns after costs, as arrays."""
    out = folder(load_settings())
    table = duckdb.sql(
        f"""select n.day, year(n.day) as yr, (date_diff('day', DATE '2003-12-29', n.day) // 7) as week,
                   v.timing, v.kind, v.mcap, n.since_filing, n.since_close,
                   1 / n.rel - 1 as g_close, exp(v.c5 - v.c) / n.rel - 1 as g_five,
                   case when v.adv < 1e6 then 0.0100 when v.adv < 1e7 then 0.0043
                        when v.adv < 1e8 then 0.0018 else 0.0005 end
                   + case when v.adv < 1e6 then 0.0025 when v.adv < 1e7 then 0.0010
                          when v.adv < 1e8 then 0.0005 else 0.0002 end
                   + 2 * least(0.01, greatest(0.000175, 0.0035 / n.paid)) as cost
            from read_parquet('{out}/entries_*.parquet') n
            join '{out}/events.parquet' v on v.day = n.day and v.symbol = n.symbol"""
    ).to_arrow_table()
    return {n: table.column(n).to_numpy(zero_copy_only=False) for n in table.column_names}


def pick(d, reading, reaction, kind, size, period):
    timing, column = reading.split("_")
    r = d["since_filing" if column == "A" else "since_close"].astype(float)
    lo, hi = REACTIONS[reaction]
    small, big = SIZES[size]
    first, last = PERIODS[period]
    return ((d["timing"] == timing) & (r >= lo) & (r < hi) & (d["kind"] == kind)
            & (d["mcap"] >= small) & (d["mcap"] < big) & (d["yr"] >= first) & (d["yr"] <= last))  # fmt: skip


def measure(d, keep, exit_):
    n = int(keep.sum())
    if n < 3:
        return {"n": n}
    gross = d["g_close" if exit_ == "close" else "g_five"][keep].astype(float)
    net = gross - d["cost"][keep]
    _, t, _ = weekly(net, d["week"][keep])
    _, before, _ = weekly(gross, d["week"][keep])
    years = d["yr"][keep]
    positive = sum(net[years == y].mean() > 0 for y in set(years))
    return {"n": n, "gross": gross.mean(), "net": net.mean(), "t": t, "pos": positive,
            "years": len(set(years)), "wins": (net > 0).mean(), "t_gross": before}  # fmt: skip


def show(label, m):
    if m["n"] < 3:
        return f"{label:<44} {m['n']:>6}"
    return (f"{label:<44} {m['n']:>6}  gross {100 * m['gross']:>6.2f}%  net {100 * m['net']:>6.2f}%  "
            f"t {m['t']:>6.2f}  yrs {m['pos']} of {m['years']}  wins {100 * m['wins']:>3.0f}%")  # fmt: skip


def search() -> None:
    d = load()
    print(f"{len(d['day'])} entries in all. Search years 2010 to 2017. Net is after the spread on entry,")
    print("the auction allowance on exit and commission.\n")
    print("The path after news, every kind and size together (mean before costs):")
    for reading in READINGS:
        for reaction in REACTIONS:
            keep = np.zeros(len(d["day"]), bool)
            for kind in KINDS:
                for size in SIZES:
                    keep |= pick(d, reading, reaction, kind, size, "search")
            a, b = measure(d, keep, "close"), measure(d, keep, "five")
            if a["n"] >= 3:
                print(f"  {reading:<9} {reaction:<6} {a['n']:>7}  to the close {100 * a['gross']:>6.2f}% (t {a['t_gross']:>6.2f})   "
                      f"five sessions {100 * b['gross']:>6.2f}% (t {b['t_gross']:>6.2f})")  # fmt: skip
    print("\nCells with 150 trades or more:")
    passed = []
    for reading in READINGS:
        for reaction in REACTIONS:
            for kind in KINDS:
                for size in SIZES:
                    keep = pick(d, reading, reaction, kind, size, "search")
                    for exit_ in EXITS:
                        m = measure(d, keep, exit_)
                        if m["n"] < 150:
                            continue
                        label = f"{reading} {reaction} {kind} {size} {exit_}"
                        print(show(label, m))
                        if m["net"] >= 0.01 and m["t"] >= 3 and m["pos"] >= 6:
                            passed.append(label)
    print("\nMeet the search bar:", passed or "none")


def test(reading, reaction, kind, size, exit_, periods=("early", "late")) -> None:
    d = load()
    for period in periods:
        keep = pick(d, reading, reaction, kind, size, period)
        print(show(f"{reading} {reaction} {kind} {size} {exit_} {period}", measure(d, keep, exit_)))
        net = d["g_close" if exit_ == "close" else "g_five"].astype(float) - d["cost"]
        for year in sorted(set(d["yr"][keep])):
            pickyear = keep & (d["yr"] == year)
            print(f"    {year}: {pickyear.sum():>5}  {100 * net[pickyear].mean():>6.2f}%")


if __name__ == "__main__":
    command = sys.argv[1]
    if command == "events":
        events()
    elif command == "collect":
        collect(int(sys.argv[2]), int(sys.argv[3]))
    elif command == "search":
        search()
    else:
        test(*sys.argv[2:7], tuple(sys.argv[7:]) or ("early", "late"))
