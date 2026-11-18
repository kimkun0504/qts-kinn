"""strategies/after_hours_other/HYPOTHESIS.md: large after-hours moves that are not results.

    cd research/claude
    uv run python after_hours_other.py universe
    uv run python after_hours_other.py collect 2010 2017     # by year, resumable
    uv run python after_hours_other.py search
    uv run python after_hours_other.py test <kind> <side> <size> <exit>
"""

from __future__ import annotations

import bisect
import sys
import tempfile
from collections import defaultdict
from datetime import date, timedelta

import duckdb
import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
import sec_times
from swing_earnings import weekly

from kinn.core.settings import load_settings
from kinn.data.store import DataStore

OPEN, CLOSE, LAST = 570, 960, 1170
MOVE, MIN_DOLLARS, MIN_BAR = 0.10, 50_000, 5_000
BORROW_NIGHT = 0.10 / 252
PERIODS = {"search": (2010, 2017), "early": (2005, 2009), "late": (2018, 2022), "check": (2023, 2023)}


def folder():
    out = load_settings().data_dir / "research" / "after_hours_other"
    out.mkdir(parents=True, exist_ok=True)
    return out


def universe() -> None:
    store = DataStore(load_settings())
    con = duckdb.connect()
    con.execute(f"set threads=3; set memory_limit='2000MB'; set temp_directory='{tempfile.mkdtemp()}'")
    con.execute(
        f"""copy (
            with p as (select permaticker, date, symbol, category, open, close, adv20_prev as adv, marketcap_prev as mcap,
                              lead(open) over w as next_open, lead(close) over w as next_close, lead(date) over w as next_date
                       from read_parquet('{store.root}/panel/*.parquet')
                       where date <= DATE '2023-11-08' and close > 0 and open > 0
                       window w as (partition by permaticker order by date))
            select date, symbol, permaticker, mcap, adv, close, next_open, next_close from p
            where date between DATE '2005-01-03' and DATE '2023-10-13' and category like '%Common Stock%'
              and mcap >= 5e7 and mcap < 2e9 and adv >= 250000 and close >= 2 and next_open > 0
              and next_date <= date + 5
            qualify row_number() over (partition by symbol, date order by adv desc) = 1
        ) to '{folder()}/universe.parquet' (format parquet)"""
    )
    print(con.sql(f"select count(*), count(distinct date) from '{folder()}/universe.parquet'").fetchall())


def kinds() -> dict:
    """{(permaticker, D): 'results' or 'other'} for 8-Ks accepted from 15:30 on D to 09:30 after."""
    stocks, days = sec_times.numbers(), sec_times.sessions()
    found: dict = {}
    for row in sec_times.filings("8k.jsonl.gz"):
        if row["cik"] not in stocks or row["filed"] >= "2023-11-09":
            continue
        when = sec_times.accepted(row)
        if not when:
            continue
        day, minute = when
        at = bisect.bisect_left(days, day)
        if at < len(days) and days[at] == day and minute >= 930:
            d = day
        elif at < len(days) and days[at] == day and minute < OPEN or not (at < len(days) and days[at] == day):
            d = days[at - 1] if at > 0 else None
        else:
            continue
        if d is None:
            continue
        kind = "results" if "2.02" in (row.get("items") or "").split(",") else "other"
        for permaticker in stocks[row["cik"]]:
            if found.get((permaticker, d)) != "results":
                found[(permaticker, d)] = kind
    return found


def filing_dates() -> dict:
    """{permaticker: sorted New York dates of its 8-Ks and 6-Ks} (the follow-up's quiet test)."""
    stocks = sec_times.numbers()
    found = defaultdict(list)
    for name, forms in (("8k.jsonl.gz", ("8-K",)), ("other_forms.jsonl.gz", ("6-K",))):
        for row in sec_times.filings(name):
            if row["form"] not in forms or row["cik"] not in stocks or row["filed"] >= "2023-11-09":
                continue
            when = sec_times.accepted(row)
            if when:
                for permaticker in stocks[row["cik"]]:
                    found[permaticker].append(when[0])
    return {k: sorted(v) for k, v in found.items()}


def quiet(dates: dict, permaticker: int, day: date) -> bool:
    """No 8-K or 6-K accepted from the day before ``day`` to four days after it."""
    got = dates.get(permaticker, [])
    at = bisect.bisect_left(got, day - timedelta(days=1))
    return not (at < len(got) and got[at] <= day + timedelta(days=4))


def collect(first: int, last: int) -> None:
    store = DataStore(load_settings())
    out = folder()
    known = kinds()
    dates = filing_dates()
    for year in range(first, last + 1):
        target = out / f"v2_{year}.parquet"
        if target.exists():
            continue
        by_day = defaultdict(dict)
        for r in duckdb.sql(
            f"select * from '{out}/universe.parquet' where year(date) = {year}"
        ).to_arrow_table().to_pylist():
            by_day[r["date"]][r["symbol"]] = r
        found = []
        for day in sorted(d for d in by_day if d.year == year):
            rows = by_day[day]
            try:
                bars = store.minute(day, symbols=list(rows), columns="symbol, minute_et, high, low, close, volume")
            except FileNotFoundError:
                continue
            symbol = bars.column("symbol").to_pylist()
            cols = {n: bars.column(n).to_numpy(zero_copy_only=False).astype(float)
                    for n in ("minute_et", "high", "low", "close", "volume")}  # fmt: skip
            where: dict = {}
            for i, s in enumerate(symbol):
                where.setdefault(s, [i, i])[1] = i
            for s, (a, b) in where.items():
                minute, high, low, price, volume = (cols[n][a : b + 1] for n in ("minute_et", "high", "low", "close", "volume"))
                regular = np.flatnonzero((minute >= OPEN) & (minute <= CLOSE))
                after = minute > CLOSE
                if not len(regular) or not after.any():
                    continue
                base = price[regular[-1]]
                dollars = price * volume * after
                cum = np.cumsum(dollars)
                move = price / base - 1
                hit = np.flatnonzero(after & (minute <= LAST) & (cum >= MIN_DOLLARS) & (dollars >= MIN_BAR)
                                     & (np.abs(move) >= MOVE))  # fmt: skip
                if not len(hit):
                    continue
                k = int(hit[0])
                e = k + 1
                if e >= len(minute) or minute[e] > minute[k] + 20:
                    continue
                side = "short" if move[k] < 0 else "long"
                paid = low[e] if side == "short" else high[e]
                r = rows[s]
                found.append({"day": day, "symbol": s, "permaticker": r["permaticker"], "side": side,
                              "kind": known.get((r["permaticker"], day), "none"), "reaction": float(move[k]),
                              "minute": int(minute[k]), "paid": float(paid), "base": float(base),
                              "low_e": float(low[e]), "high_e": float(high[e]),
                              "quiet": quiet(dates, r["permaticker"], day),
                              "dollars": float(cum[k]), "mcap": r["mcap"], "adv": r["adv"],
                              "next_open": r["next_open"], "next_close": r["next_close"]})  # fmt: skip
        pq.write_table(pa.Table.from_pylist(found), target)
        print(f"{year}: {len(found)} entries", flush=True)


def load() -> dict:
    t = duckdb.sql(
        f"""select *, year(day) as yr, (date_diff('day', DATE '2003-12-29', day) // 7) as week
            from read_parquet('{folder()}/v2_*.parquet', union_by_name = true)"""
    ).to_arrow_table()
    d = {n: t.column(n).to_numpy(zero_copy_only=False) for n in t.column_names}
    paid = d["paid"].astype(float)
    adv = d["adv"].astype(float)
    tier = np.where(adv < 1e6, 0.0025, np.where(adv < 1e7, 0.0010, np.where(adv < 1e8, 0.0005, 0.0002)))
    commission = 2 * np.minimum(0.01, np.maximum(0.000175, 0.0035 / paid))
    short = d["side"] == "short"
    for exit_ in ("next_open", "next_close"):
        price = d[exit_].astype(float)
        gross = np.where(short, 1 - price / paid, price / paid - 1)
        d[exit_ + "_net"] = gross - tier - commission - np.where(short, BORROW_NIGHT, 0)
    d["size"] = np.where(d["mcap"].astype(float) < 3e8, "small", "mid")
    return d


def measure(d, keep, exit_):
    net = d[exit_ + "_net"][keep]
    n = len(net)
    if n < 3:
        return {"n": n}
    _, t, _ = weekly(net, d["week"][keep])
    years = d["yr"][keep]
    yearly = {int(y): net[years == y].mean() for y in sorted(set(years))}
    return {"n": n, "mean": net.mean(), "median": float(np.median(net)), "t": t,
            "pos": sum(v > 0 for v in yearly.values()), "years": len(yearly), "yearly": yearly}  # fmt: skip


def show(label, m):
    if m["n"] < 3:
        return f"{label:38} {m['n']}"
    return (f"{label:38} {m['n']:>5} trades  after costs {100 * m['mean']:>6.2f}%  median {100 * m['median']:>6.2f}%  "
            f"t {m['t']:>5.2f}  yrs {m['pos']} of {m['years']}")  # fmt: skip


def pick(d, kind, side, size, period):
    first, last = PERIODS[period]
    return (d["kind"] == kind) & (d["side"] == side) & (d["size"] == size) & (d["yr"] >= first) & (d["yr"] <= last)


def search() -> None:
    d = load()
    met = []
    for kind in ("other", "none"):
        for side in ("short", "long"):
            for size in ("small", "mid"):
                for exit_ in ("next_open", "next_close"):
                    m = measure(d, pick(d, kind, side, size, "search"), exit_)
                    label = f"{kind} {side} {size} {exit_}"
                    ok = m["n"] >= 150 and m["mean"] >= 0.01 and m["t"] >= 3 and m["pos"] >= 6
                    print(show(label, m) + ("  MEETS THE BAR" if ok else ""))
                    if ok:
                        met.append(label)
    print(show("comparison: results short mid next_open", measure(d, pick(d, "results", "short", "mid", "search"), "next_open")))
    print("\nMeet the search bar:", met or "none")


def fade(*periods) -> None:
    """The follow-up: no-news rises sold short at the low of the entry minute."""
    d = load()
    paid = d["low_e"].astype(float)
    adv = d["adv"].astype(float)
    tier = np.where(adv < 1e6, 0.0025, np.where(adv < 1e7, 0.0010, np.where(adv < 1e8, 0.0005, 0.0002)))
    commission = 2 * np.minimum(0.01, np.maximum(0.000175, 0.0035 / paid))
    for exit_ in ("next_open", "next_close"):
        gross = 1 - d[exit_].astype(float) / paid
        d[exit_ + "_net"] = gross - tier - commission - BORROW_NIGHT
    for period in periods or ("search",):
        first, last = PERIODS[period]
        for size in ("small", "mid"):
            for exit_ in ("next_open", "next_close"):
                keep = ((d["kind"] == "none") & d["quiet"].astype(bool) & (d["side"] == "long")
                        & (d["size"] == size) & (d["yr"] >= first) & (d["yr"] <= last))  # fmt: skip
                m = measure(d, keep, exit_)
                bar = (0.01, 3, 6, 150) if period == "search" else (0.005, 2.5, 4, 0)
                ok = m["n"] >= max(3, bar[3]) and m["mean"] >= bar[0] and m["t"] >= bar[1] and m["pos"] >= bar[2]
                print(show(f"fade {size} {exit_} {period}", m) + ("  MEETS THE BAR" if ok else ""))
                if period != "search" and m["n"] >= 3:
                    print("    " + "  ".join(f"{y} {100 * v:.2f}%" for y, v in m["yearly"].items()))


def test(kind, side, size, exit_) -> None:
    d = load()
    for period in ("early", "late"):
        m = measure(d, pick(d, kind, side, size, period), exit_)
        print(show(f"{kind} {side} {size} {exit_} {period}", m))
        if m["n"] >= 3:
            print("    " + "  ".join(f"{y} {100 * v:.2f}%" for y, v in m["yearly"].items()))


if __name__ == "__main__":
    command = sys.argv[1]
    if command == "universe":
        universe()
    elif command == "collect":
        collect(int(sys.argv[2]), int(sys.argv[3]))
    elif command == "search":
        search()
    elif command == "fade":
        fade(*sys.argv[2:])
    else:
        test(*sys.argv[2:])
    _ = date
