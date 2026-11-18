"""strategies/late_filer/HYPOTHESIS.md: buying when the overdue report arrives.

    cd research/claude
    uv run python late_filer.py events
    uv run python late_filer.py search
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

SEALED = date(2023, 11, 9)
SIZES = {"small": (5e7, 3e8), "larger": (3e8, 1e18)}
PERIODS = {"search": (2010, 2017), "early": (2005, 2009), "late": (2018, 2022), "check": (2023, 2023)}


def folder():
    out = load_settings().data_dir / "research" / "late_filer"
    out.mkdir(parents=True, exist_ok=True)
    return out


def events() -> None:
    stocks, days = sec_times.numbers(), sec_times.sessions()
    notices, reports = defaultdict(list), defaultdict(list)
    for row in sec_times.filings("other_forms.jsonl.gz"):
        if row["cik"] not in stocks or row["form"] not in ("NT 10-Q", "NT 10-K", "10-Q", "10-K"):
            continue
        when = sec_times.accepted(row)
        if not when or when[0] >= SEALED:
            continue
        (notices if row["form"].startswith("NT") else reports)[row["cik"]].append(when)
    found = []
    for cik, ns in notices.items():
        rs = sorted(reports.get(cik, []))
        for nday, _ in sorted(ns):
            i = bisect.bisect_right(rs, (nday, 9999))
            if i >= len(rs) or rs[i][0] > nday + timedelta(days=20):
                continue
            rday, rminute = rs[i]
            before = days[bisect.bisect_left(days, nday) - 1]  # the session before the notice
            # first open after acceptance: the next session if accepted from 09:30 on a session day or later
            j = bisect.bisect_right(days, rday) if (rday in days and rminute >= 570) or rday not in days else bisect.bisect_left(days, rday)
            if rday not in days and j < len(days) and days[j] <= rday:
                j += 1
            if j + 1 >= len(days) or days[j] > date(2023, 10, 13):
                continue
            for permaticker in stocks[cik]:
                found.append((permaticker, before, days[j - 1], days[j]))
    table = pa.table({"permaticker": [f[0] for f in found], "before": [f[1] for f in found],
                      "rsession": [f[2] for f in found], "entry": [f[3] for f in found]})  # fmt: skip
    store = DataStore(load_settings())
    con = duckdb.connect()
    con.execute(f"set threads=3; set memory_limit='1500MB'; set temp_directory='{tempfile.mkdtemp()}'")
    con.register("ev", table)
    base = load_settings().data_dir / "research" / "swing"
    con.execute(
        f"""copy (
            with p as (
                select permaticker, date, category, close, adv20_prev as adv, marketcap_prev as mcap,
                       open / close as oc, sum(ln(close / prev_close)) over w as c, row_number() over w as rn
                from read_parquet('{store.root}/panel/*.parquet')
                where date <= DATE '2023-11-08' and prev_close > 0 and close > 0 and open > 0
                  and permaticker in (select permaticker from ev)
                window w as (partition by permaticker order by date)),
            q as (select *, lead(c, 14) over w as c14, lead(c, 15) over w as c15, lead(oc, 1) over w as oc1,
                         lead(c, 1) over w as c1
                  from p window w as (partition by permaticker order by date)),
            e as (select distinct * from ev)
            select e.entry as day, e.permaticker, b.mcap, b.adv, b.close,
                   exp(r.c - b.c) - 1 as fall,
                   exp(q.c14 - q.c) / q.oc - 1 as g_once,
                   exp(q.c15 - q.c1) / q.oc1 - 1 as g_after,
                   2 * (least(0.01, greatest(0.000175, 0.0035 / b.close))
                        + case when b.adv < 1e6 then 0.0025 when b.adv < 1e7 then 0.0010
                               when b.adv < 1e8 then 0.0005 else 0.0002 end) as cost
            from e join q b on b.permaticker = e.permaticker and b.date = e.before
            join q r on r.permaticker = e.permaticker and r.date = e.rsession
            join q on q.permaticker = e.permaticker and q.date = e.entry
            where b.category like '%Common Stock%' and b.mcap >= 5e7 and b.adv >= 250000 and b.close >= 1
              and q.c15 is not null
            qualify row_number() over (partition by e.permaticker, e.entry order by e.before) = 1
        ) to '{folder()}/events_all.parquet' (format parquet)"""
    )
    con.execute(
        f"""copy (
            with recent as (
                select permaticker, day from read_parquet('{base}/wide_*.parquet') where esince <= 10
                  and permaticker in (select permaticker from '{folder()}/events_all.parquet')
                union all
                select permaticker, day from read_parquet('{base}/early_*.parquet') where esince <= 10
                  and permaticker in (select permaticker from '{folder()}/events_all.parquet'))
            select * from '{folder()}/events_all.parquet' e
            where not exists (select 1 from recent r where r.permaticker = e.permaticker and r.day = e.day)
        ) to '{folder()}/events.parquet' (format parquet)"""
    )
    print(con.sql(f"select count(*), count(*) filter (where fall <= -0.10), min(day), max(day) from '{folder()}/events.parquet'").fetchall())


def search(*periods) -> None:
    t = duckdb.sql(f"select *, year(day) as yr, (date_diff('day', DATE '2003-12-29', day) // 7) as week from '{folder()}/events.parquet'").to_arrow_table()
    d = {n: t.column(n).to_numpy(zero_copy_only=False) for n in t.column_names}
    for period in periods:
        first, last = PERIODS[period]
        for entry in ("once", "after"):
            for group in ("every", "fell10"):
                for size, (lo, hi) in SIZES.items():
                    keep = (d["yr"] >= first) & (d["yr"] <= last) & (d["mcap"] >= lo) & (d["mcap"] < hi)
                    if group == "fell10":
                        keep &= d["fall"] <= -0.10
                    net = d[f"g_{entry}"][keep].astype(float) - d["cost"][keep]
                    if len(net) < 3:
                        print(f"{period} {entry} {group} {size}: {len(net)}")
                        continue
                    _, tt, _ = weekly(net, d["week"][keep])
                    years = d["yr"][keep]
                    pos = sum(net[years == y].mean() > 0 for y in set(years))
                    print(f"{period:6} {entry:5} {group:6} {size:6} {len(net):>5} trades  net {100 * net.mean():>6.2f}%  "
                          f"median {100 * np.median(net):>6.2f}%  t {tt:>5.2f}  yrs {pos} of {len(set(years))}")  # fmt: skip


if __name__ == "__main__":
    if sys.argv[1] == "events":
        events()
    else:
        search(*sys.argv[2:])
