"""strategies/overnight_offering/HYPOTHESIS.md: the first session after a prospectus
supplement (424B5) is filed overnight.

    cd research/claude
    uv run python night_bids.py filings       # results nights, shared
    uv run python overnight_offering.py events
    uv run python overnight_offering.py search
    uv run python overnight_offering.py test long down10 small close
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
from swing_earnings import weekly

import sec_times
from kinn.core.settings import load_settings
from kinn.data.store import DataStore
from night_bids import folder as shared

SIZES = {"small": (5e7, 3e8), "mid": (3e8, 2e9), "large": (2e9, 1e18)}
GAPS = {"down3": (-0.10, -0.03), "down10": (-9.0, -0.10)}
EXITS = {"long": ("close", "five", "fifteen"), "short": ("close", "five")}
PERIODS = {"search": (2010, 2017), "early": (2005, 2009), "late": (2018, 2022), "check": (2023, 2023)}
SEALED = date(2023, 11, 9)
BORROW_DAY = 0.10 / 252


def folder():
    out = load_settings().data_dir / "research" / "overnight_offering"
    out.mkdir(parents=True, exist_ok=True)
    return out


def events() -> None:
    stocks, days = sec_times.numbers(), sec_times.sessions()
    by_cik = defaultdict(list)
    for row in sec_times.filings("other_forms.jsonl.gz"):
        if row["form"] != "424B5" or row["cik"] not in stocks:
            continue
        when = sec_times.accepted(row)
        if when and when[0] < SEALED:
            by_cik[row["cik"]].append(when)
    found = {}
    for cik, whens in by_cik.items():
        whens.sort()
        filed_days = [w[0] for w in whens]
        for day, minute in whens:
            i = bisect.bisect_right(days, day)  # sessions up to and including day
            if minute >= 960 and i and days[i - 1] == day:
                session = day
            elif minute < 555:
                session = days[bisect.bisect_left(days, day) - 1] if bisect.bisect_left(days, day) else None
            else:
                continue
            if session is None or session > date(2023, 10, 13):
                continue
            before = bisect.bisect_left(filed_days, session - timedelta(days=365))
            serial = bisect.bisect_left(filed_days, session) - before
            for permaticker in stocks[cik]:
                key = (permaticker, session)
                found[key] = min(found.get(key, serial), serial)
    table = pa.table({"permaticker": [k[0] for k in found], "day": [k[1] for k in found], "serial": list(found.values())})
    store = DataStore(load_settings())
    con = duckdb.connect()
    con.execute(f"set threads=3; set memory_limit='1500MB'; set temp_directory='{tempfile.mkdtemp()}'")
    con.register("filings", table)
    con.execute(
        f"""copy (
            with p as (
                select permaticker, date, symbol, category, close, adv20_prev as adv, marketcap_prev as mcap,
                       open / close as oc, sum(ln(close / prev_close)) over w as c, row_number() over w as rn
                from read_parquet('{store.root}/panel/*.parquet')
                where date <= DATE '2023-11-08' and prev_close > 0 and close > 0 and open > 0
                window w as (partition by permaticker order by date)),
            q as (select *, lead(c, 1) over w as c1, lead(oc, 1) over w as oc1, lead(c, 6) over w as c6,
                         lead(c, 16) over w as c16, lead(rn, 1) over w as rn1
                  from p window w as (partition by permaticker order by date)),
            e as (select q.*, f.serial from q join filings f on f.permaticker = q.permaticker and f.day = q.date
                  where f.serial <= 6 and q.category like '%Common Stock%' and q.mcap >= 5e7 and q.adv >= 250000
                    and q.close >= 1 and q.c1 is not null and q.rn1 = q.rn + 1
                    and not exists (select 1 from '{shared()}/results_due.parquet' x
                                    where x.permaticker = q.permaticker and x.day = q.date)),
            once as (select * from e
                     qualify coalesce(rn - lag(rn) over (partition by permaticker order by rn), 999) >= 20)
            select date as day, symbol, permaticker, mcap, adv, close, serial,
                   exp(c1 - c) * oc1 - 1 as gap,
                   1 / oc1 - 1 as g_close, exp(c6 - c1) / oc1 - 1 as g_five, exp(c16 - c1) / oc1 - 1 as g_fifteen,
                   2 * (least(0.01, greatest(0.000175, 0.0035 / close))
                        + case when adv < 1e6 then 0.0025 when adv < 1e7 then 0.0010
                               when adv < 1e8 then 0.0005 else 0.0002 end) as cost
            from once order by day, symbol
        ) to '{folder()}/events.parquet' (format parquet)"""
    )
    print(con.sql(f"select count(*), count(g_five), count(g_fifteen), min(day), max(day) from '{folder()}/events.parquet'").fetchall())
    print(con.sql(f"""select case when gap <= -0.10 then 'down10' when gap <= -0.03 then 'down3' else 'other' end, count(*),
                             median(gap) from '{folder()}/events.parquet' group by 1 order by 1""").fetchall())


def load() -> dict[str, np.ndarray]:
    t = duckdb.sql(
        f"""select *, year(day) as yr, (date_diff('day', DATE '2003-12-29', day) // 7) as week
            from '{folder()}/events.parquet' order by day, symbol"""
    ).to_arrow_table()
    return {n: t.column(n).to_numpy(zero_copy_only=False) for n in t.column_names}


def pick(d, size, gap, period):
    small, big = SIZES[size]
    lo, hi = GAPS[gap]
    first, last = PERIODS[period]
    return ((d["mcap"] >= small) & (d["mcap"] < big) & (d["gap"] > lo) & (d["gap"] <= hi)
            & (d["yr"] >= first) & (d["yr"] <= last))  # fmt: skip


def net(d, side, exit_):
    gross = d[f"g_{exit_}"].astype(float)
    if side == "long":
        return gross - d["cost"]
    held = {"close": 1, "five": 6}[exit_]
    return -gross / (1 + 0 * gross) - d["cost"] - BORROW_DAY * held


def measure(d, keep, side, exit_) -> dict:
    values = net(d, side, exit_)
    keep = keep & ~np.isnan(values)
    n = int(keep.sum())
    if n < 3:
        return {"n": n}
    v = values[keep]
    _, t, _ = weekly(v, d["week"][keep])
    years = d["yr"][keep]
    ordered = np.sort(v)
    return {"n": n, "net": v.mean(), "median": np.median(v), "t": t, "wins": (v > 0).mean(),
            "pos": sum(v[years == y].mean() > 0 for y in set(years)), "years": len(set(years)),
            "worst": ordered[0], "worst1": ordered[: max(1, n // 100)].mean()}  # fmt: skip


def show(label, m) -> str:
    if m["n"] < 3:
        return f"{label:30} {m['n']:>5}"
    return (f"{label:30} {m['n']:>5}  net {100 * m['net']:>6.2f}%  median {100 * m['median']:>6.2f}%  "
            f"t {m['t']:>5.2f}  yrs {m['pos']} of {m['years']}  wins {100 * m['wins']:>3.0f}%  "
            f"worst {100 * m['worst']:>5.0f}%  worst 1% {100 * m['worst1']:>4.0f}%")  # fmt: skip


def search() -> None:
    d = load()
    passed = []
    for side, exits in EXITS.items():
        for gap in GAPS:
            for size in SIZES:
                keep = pick(d, size, gap, "search")
                for exit_ in exits:
                    m = measure(d, keep, side, exit_)
                    label = f"{side} {gap} {size} {exit_}"
                    print(show(label, m))
                    if m["n"] >= 150 and m["net"] >= 0.01 and m["t"] >= 3 and m["pos"] >= 6:
                        passed.append(label)
    print("\nMeet the search bar:", passed or "none")


def test(side, gap, size, exit_) -> None:
    d = load()
    v = net(d, side, exit_)
    for period in ("early", "late"):
        keep = pick(d, size, gap, period)
        print(show(f"{side} {gap} {size} {exit_} {period}", measure(d, keep, side, exit_)))
        for year in sorted(set(d["yr"][keep])):
            mine = keep & (d["yr"] == year) & ~np.isnan(v)
            print(f"    {year}: {mine.sum():>5}  {100 * v[mine].mean():>6.2f}%")


if __name__ == "__main__":
    if sys.argv[1] == "events":
        events()
    elif sys.argv[1] == "search":
        search()
    else:
        test(*sys.argv[2:6])
