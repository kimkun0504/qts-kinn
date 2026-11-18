"""strategies/lockup_end/HYPOTHESIS.md: the weeks around the 180-day lockup end after an IPO.

    cd research/claude
    uv run python lockup_end.py events
    uv run python lockup_end.py search
    uv run python lockup_end.py test long22 small
"""

from __future__ import annotations

import bisect
import csv
import io
import re
import sys
import tempfile
import zipfile
from collections import defaultdict
from datetime import date, timedelta

import duckdb
import numpy as np
import pyarrow as pa
from swing_earnings import weekly

import sec_times
from kinn.core.settings import load_settings
from kinn.data.store import DataStore

SIZES = {"small": (5e7, 3e8), "mid": (3e8, 2e9), "large": (2e9, 1e18)}
TRADES = ("short", "long12", "long22")
PERIODS = {"search": (2010, 2017), "early": (2005, 2009), "late": (2018, 2022), "check": (2023, 2023)}
SEALED = date(2023, 11, 9)
BORROW_DAY = 0.10 / 252


def folder():
    out = load_settings().data_dir / "research" / "lockup_end"
    out.mkdir(parents=True, exist_ok=True)
    return out


def events() -> None:
    settings = load_settings()
    raw = max((settings.raw_dir / "sharadar").iterdir())
    keep, cik_of = set(), {}
    with zipfile.ZipFile(next(raw.glob("SHARADAR_TICKERS_*.zip"))) as z, z.open(z.namelist()[0]) as handle:
        for row in csv.DictReader(io.TextIOWrapper(handle, "utf-8")):
            match = re.search(r"CIK=0*(\d+)", row.get("secfilings") or "")
            if (row["table"] == "SEP" and row["category"].startswith("Domestic Common Stock")
                    and row["siccode"] != "6770" and match):  # fmt: skip
                keep.add(int(row["permaticker"]))
                cik_of[int(row["permaticker"])] = int(match.group(1))
    s1, spun = defaultdict(list), set()
    for row in sec_times.filings("other_forms.jsonl.gz"):
        when = sec_times.accepted(row)
        if not when or when[0] >= SEALED:
            continue
        if row["form"] == "S-1":
            s1[row["cik"]].append(when[0])
        elif row["form"] == "10-12B":
            spun.add(row["cik"])
    for v in s1.values():
        v.sort()
    store = DataStore(settings)
    con = duckdb.connect()
    con.execute(f"set threads=3; set memory_limit='1500MB'; set temp_directory='{tempfile.mkdtemp()}'")
    first = con.sql(
        f"""select permaticker, min(date) from read_parquet('{store.root}/panel/*.parquet')
            where date <= DATE '2023-11-08' group by 1 having min(date) >= DATE '2005-01-03'"""
    ).fetchall()
    sessions = store.sessions(date(2005, 1, 3), date(2023, 11, 8))
    found = []
    for permaticker, start in first:
        cik = cik_of.get(permaticker)
        if permaticker not in keep or cik in spun:
            continue
        dates = s1.get(cik, [])
        i = bisect.bisect_right(dates, start)
        if not i or dates[i - 1] < start - timedelta(days=365):
            continue
        k = bisect.bisect_left(sessions, start + timedelta(days=180))
        if k < len(sessions) and sessions[k] <= date(2023, 10, 13):
            found.append((permaticker, start, sessions[k]))
    con.register("ipos", pa.table({"permaticker": [f[0] for f in found], "first": [f[1] for f in found],
                                   "lockup": [f[2] for f in found]}))  # fmt: skip
    con.execute(
        f"""copy (
            with p as (
                select permaticker, date, symbol, close, adv20_prev as adv, marketcap_prev as mcap,
                       sum(ln(close / prev_close)) over w as c, row_number() over w as rn
                from read_parquet('{store.root}/panel/*.parquet')
                where date <= DATE '2023-11-08' and prev_close > 0 and close > 0
                window w as (partition by permaticker order by date)),
            q as (select *, lag(c, 6) over w as c_m6, lag(mcap, 6) over w as mcap_m6, lag(adv, 6) over w as adv_m6,
                         lag(close, 6) over w as close_m6, lead(c, 1) over w as c_p1, lead(c, 2) over w as c_p2,
                         lead(c, 12) over w as c_p12, lead(c, 22) over w as c_p22,
                         lag(date, 6) over w as day_m6, lead(close, 2) over w as close_p2, lead(adv, 2) over w as adv_p2
                  from p window w as (partition by permaticker order by date))
            select q.date as day, q.symbol, q.permaticker, i.first, q.mcap_m6 as mcap, q.adv_m6 as adv, q.day_m6,
                   exp(q.c_p1 - q.c_m6) - 1 as g_short, exp(q.c_p12 - q.c_p2) - 1 as g_long12,
                   exp(q.c_p22 - q.c_p2) - 1 as g_long22,
                   2 * (least(0.01, greatest(0.000175, 0.0035 / q.close_m6))
                        + case when q.adv_m6 < 1e6 then 0.0025 when q.adv_m6 < 1e7 then 0.0010
                               when q.adv_m6 < 1e8 then 0.0005 else 0.0002 end) as cost
            from q join ipos i on i.permaticker = q.permaticker and i.lockup = q.date
            where q.mcap_m6 >= 5e7 and q.adv_m6 >= 250000 and q.c_m6 is not null and q.c_p1 is not null
            order by day
        ) to '{folder()}/events.parquet' (format parquet)"""
    )
    print(len(found), "IPOs;", con.sql(f"select count(*), count(g_long22), min(day), max(day) from '{folder()}/events.parquet'").fetchall())
    print(con.sql(f"select year(day), count(*) from '{folder()}/events.parquet' group by 1 order by 1").fetchall())


def load() -> dict[str, np.ndarray]:
    t = duckdb.sql(
        f"""select *, year(day) as yr, (date_diff('day', DATE '2003-12-29', day) // 7) as week
            from '{folder()}/events.parquet' order by day"""
    ).to_arrow_table()
    d = {n: t.column(n).to_numpy(zero_copy_only=False) for n in t.column_names}
    d["n_short"] = -d["g_short"].astype(float) - d["cost"] - BORROW_DAY * 7
    d["n_long12"] = d["g_long12"].astype(float) - d["cost"]
    d["n_long22"] = d["g_long22"].astype(float) - d["cost"]
    return d


def pick(d, size, period):
    small, big = SIZES[size]
    first, last = PERIODS[period]
    return (d["mcap"] >= small) & (d["mcap"] < big) & (d["yr"] >= first) & (d["yr"] <= last)


def measure(d, keep, trade) -> dict:
    v = d[f"n_{trade}"]
    keep = keep & ~np.isnan(v)
    n = int(keep.sum())
    if n < 3:
        return {"n": n}
    x = v[keep]
    _, t, _ = weekly(x, d["week"][keep])
    years = d["yr"][keep]
    return {"n": n, "net": x.mean(), "median": np.median(x), "t": t, "wins": (x > 0).mean(),
            "pos": sum(x[years == y].mean() > 0 for y in set(years)), "years": len(set(years)), "worst": x.min()}  # fmt: skip


def show(label, m) -> str:
    if m["n"] < 3:
        return f"{label:22} {m['n']:>5}"
    return (f"{label:22} {m['n']:>5}  net {100 * m['net']:>6.2f}%  median {100 * m['median']:>6.2f}%  "
            f"t {m['t']:>5.2f}  yrs {m['pos']} of {m['years']}  wins {100 * m['wins']:>3.0f}%  worst {100 * m['worst']:>5.0f}%")  # fmt: skip


def search() -> None:
    d = load()
    passed = []
    for trade in TRADES:
        for size in SIZES:
            m = measure(d, pick(d, size, "search"), trade)
            label = f"{trade} {size}"
            print(show(label, m))
            if m["n"] >= 150 and m["net"] >= 0.01 and m["t"] >= 3 and m["pos"] >= 6:
                passed.append(label)
    print("\nMeet the search bar:", passed or "none")


def test(trade, size) -> None:
    d = load()
    for period in ("early", "late"):
        keep = pick(d, size, period)
        print(show(f"{trade} {size} {period}", measure(d, keep, trade)))
        v = d[f"n_{trade}"]
        print("    " + "  ".join(f"{y} {100 * np.nanmean(v[keep & (d['yr'] == y)]):.2f}% ({(keep & (d['yr'] == y)).sum()})"
                                  for y in sorted(set(d["yr"][keep]))))


if __name__ == "__main__":
    if sys.argv[1] == "events":
        events()
    elif sys.argv[1] == "search":
        search()
    else:
        test(*sys.argv[2:4])
