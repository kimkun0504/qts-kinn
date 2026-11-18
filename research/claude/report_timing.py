"""strategies/report_timing/HYPOTHESIS.md: late and early results against a company's own calendar.

    cd research/claude
    uv run python report_timing.py events
    uv run python report_timing.py search
    uv run python report_timing.py test late 2 mid
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
from swing_earnings import weekly

from kinn.core.settings import load_settings
from kinn.data.store import DataStore

PERIODS = {"search": (2010, 2017), "early": (2005, 2009), "late": (2018, 2022), "check": (2023, 2023)}
SIZES = {"small": (5e7, 3e8), "mid": (3e8, 2e9), "large": (2e9, 1e18)}
CELLS = [("late", 2, "mid"), ("late", 2, "large"), ("late", 5, "mid"), ("late", 5, "large"),
         ("early", 7, "small"), ("early", 7, "mid")]  # fmt: skip
BORROW_DAY = 0.01 / 252


def folder():
    out = load_settings().data_dir / "research" / "report_timing"
    out.mkdir(parents=True, exist_ok=True)
    return out


def events() -> None:
    settings = load_settings()
    store = DataStore(settings)
    sessions = store.sessions(date(2004, 12, 1), date(2023, 11, 8))
    index = {d: i for i, d in enumerate(sessions)}
    reports = defaultdict(list)
    for r in pq.read_table(settings.data_dir / "research" / "swing" / "timed.parquet").to_pylist():
        reports[r["permaticker"]].append(r["day"])
    rows = []
    for p, days in reports.items():
        days = sorted(set(days))
        for base in days:
            target = base + timedelta(days=364)
            i = bisect.bisect_left(sessions, target)
            if i >= len(sessions):
                continue
            e = sessions[i]
            if e > date(2023, 10, 13) or e.year < 2005:
                continue
            j = bisect.bisect_left(days, e - timedelta(days=30))
            actual = days[j] if j < len(days) else None
            if actual is not None and actual - base < timedelta(days=200):
                continue  # the report before the expected one is still the base's neighbour
            for wait in (2, 5):
                s = i + wait
                if s + 31 >= len(sessions):
                    continue
                if actual is None or index.get(actual, 10**9) > s:
                    exit_i = min(index.get(actual, 10**9) + 1, s + 30) if actual else s + 30
                    if exit_i < len(sessions):
                        rows.append((p, "late", wait, sessions[s], sessions[s], sessions[exit_i]))
            if actual is not None and e - timedelta(days=30) <= actual <= e - timedelta(days=7):
                a = index.get(actual)
                if a is not None and a + 15 < len(sessions):
                    rows.append((p, "early", 7, actual, sessions[a + 1], sessions[a + 15]))
    names = ("permaticker", "kind", "wait", "signal", "entry", "exit")
    con = duckdb.connect()
    con.execute(f"set threads=3; set memory_limit='2000MB'; set temp_directory='{tempfile.mkdtemp()}'")
    con.register("ev", pa.table({n: [r[k] for r in rows] for k, n in enumerate(names)}))
    con.execute(
        f"""copy (
            with p as (select permaticker, date, category, close, adv20_prev as adv, marketcap_prev as mcap,
                              open / close as oc, sum(ln(close / prev_close)) over w as c
                       from read_parquet('{store.root}/panel/*.parquet')
                       where date <= DATE '2023-11-08' and prev_close > 0 and close > 0 and open > 0
                         and permaticker in (select distinct permaticker from ev)
                       window w as (partition by permaticker order by date))
            select ev.*, s.mcap, s.adv, s.close, s.category, s.c as c_signal, n.c as c_entry, n.oc as oc_entry, x.c as c_exit,
                   2 * (least(0.01, greatest(0.000175, 0.0035 / s.close))
                        + case when s.adv < 1e6 then 0.0025 when s.adv < 1e7 then 0.0010
                               when s.adv < 1e8 then 0.0005 else 0.0002 end) as cost
            from ev join p s on s.permaticker = ev.permaticker and s.date = ev.signal
            join p n on n.permaticker = ev.permaticker and n.date = ev.entry
            asof join p x on x.permaticker = ev.permaticker and x.date <= ev.exit
        ) to '{folder()}/events.parquet' (format parquet)"""
    )
    print(con.sql(f"select kind, wait, count(*) from '{folder()}/events.parquet' group by 1, 2 order by 1, 2").fetchall())


def load():
    t = duckdb.sql(
        f"""select *, year(signal) as yr, (date_diff('day', DATE '2003-12-29', signal) // 7) as week,
                   date_diff('day', signal, exit) as days
            from '{folder()}/events.parquet'
            where category like '%Common Stock%' and adv >= 250000 and close >= 1"""
    ).to_arrow_table()
    d = {n: t.column(n).to_numpy(zero_copy_only=False) for n in t.column_names}
    late = d["kind"] == "late"
    d["net"] = np.where(late, -(np.exp(d["c_exit"] - d["c_signal"]) - 1) - d["cost"] - BORROW_DAY * d["days"],
                        np.exp(d["c_exit"] - d["c_entry"]) / d["oc_entry"] - 1 - d["cost"])  # fmt: skip
    return d


def line(d, kind, wait, size, period):
    lo, hi = SIZES[size]
    a, b = PERIODS[period]
    k = (d["kind"] == kind) & (d["wait"] == wait) & (d["mcap"] >= lo) & (d["mcap"] < hi) & (d["yr"] >= a) & (d["yr"] <= b)
    net = d["net"][k]
    if len(net) < 3:
        return f"{kind} {wait} {size} {period}: {len(net)}", {}
    _, t, _ = weekly(net, d["week"][k])
    years = d["yr"][k]
    yearly = {int(y): net[years == y].mean() for y in sorted(set(years))}
    return (f"{kind:5} {wait} {size:5} {period:6} {len(net):>5} trades  net {100 * net.mean():6.2f}%  "
            f"median {100 * np.median(net):6.2f}%  t {t:5.2f}  yrs {sum(v > 0 for v in yearly.values())} of {len(yearly)}"), yearly  # fmt: skip


def search() -> None:
    d = load()
    for kind, wait, size in CELLS:
        print(line(d, kind, wait, size, "search")[0])


def test(kind, wait, size) -> None:
    d = load()
    for period in ("early", "late"):
        text, yearly = line(d, kind, int(wait), size, period)
        print(text)
        print("    " + "  ".join(f"{y} {100 * v:.2f}%" for y, v in yearly.items()))


if __name__ == "__main__":
    if sys.argv[1] == "events":
        events()
    elif sys.argv[1] == "search":
        search()
    else:
        test(*sys.argv[2:5])
