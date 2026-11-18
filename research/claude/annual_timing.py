"""strategies/annual_timing/HYPOTHESIS.md: 10-Ks filed much earlier than last year.

    cd research/claude
    uv run python annual_timing.py table
    uv run python annual_timing.py search
    uv run python annual_timing.py test <period> <size> <hold>
"""

from __future__ import annotations

import sys
import tempfile
from datetime import date

import duckdb
import pyarrow as pa

import sec_times
from dividend_signal import BAR, PERIODS, measure, show
from kinn.core.settings import load_settings
from kinn.data.store import DataStore
from self_tender import entry_session


def folder():
    out = load_settings().data_dir / "research" / "annual_timing"
    out.mkdir(parents=True, exist_ok=True)
    return out


def table() -> None:
    stocks, days = sec_times.numbers(), sec_times.sessions()
    filed: dict = {}
    for row in sec_times.filings("other_forms.jsonl.gz"):
        if row["form"] != "10-K" or row["cik"] not in stocks or row["filed"] >= "2023-11-09":
            continue
        when = sec_times.accepted(row)
        if when:
            filed.setdefault(row["cik"], []).append(when)
    rows = []
    for cik, whens in filed.items():
        whens.sort()
        for prev, now in zip(whens, whens[1:], strict=False):
            gap = (now[0] - prev[0]).days
            if not 300 <= gap <= 430:
                continue
            earlier = (now[0].timetuple().tm_yday - prev[0].timetuple().tm_yday) if now[0].year == prev[0].year + 1 else gap - 365
            if earlier > -10:
                continue
            day = entry_session(days, now)
            if day and date(2005, 1, 1) <= day <= date(2023, 10, 13):
                rows.extend((p, day) for p in stocks[cik])
    events = pa.table({"permaticker": [r[0] for r in rows], "day": [r[1] for r in rows]})
    store = DataStore(load_settings())
    con = duckdb.connect()
    con.execute(f"set threads=3; set memory_limit='2000MB'; set temp_directory='{tempfile.mkdtemp()}'")
    con.register("events", events)
    con.execute(
        f"""copy (
            with p as (select permaticker, date, category, close, prev_close, adv20_prev as adv, marketcap_prev as mcap,
                              open / close as oc, sum(ln(close / prev_close)) over w as c
                       from read_parquet('{store.root}/panel/*.parquet')
                       where date <= DATE '2023-11-08' and prev_close > 0 and close > 0 and open > 0
                       window w as (partition by permaticker order by date)),
            q as (select *, last_value(c) over (partition by permaticker order by date
                              rows between current row and 19 following) as c20,
                         last_value(c) over (partition by permaticker order by date
                              rows between current row and 59 following) as c60,
                         case when mcap < 3e8 then 'small' else 'mid' end as size
                  from p window w as (partition by permaticker order by date)),
            ok as (select * from q where category like '%Common Stock%' and mcap >= 5e7 and mcap < 2e9
                   and adv >= 250000 and prev_close >= 2),
            avgs as (select date, size, avg(exp(c20 - c) / oc - 1) as all20, avg(exp(c60 - c) / oc - 1) as all60
                     from ok group by 1, 2)
            select distinct e.day, ok.permaticker, ok.size, ok.adv, ok.prev_close,
                   exp(ok.c20 - ok.c) / ok.oc - 1 as g20, exp(ok.c60 - ok.c) / ok.oc - 1 as g60, a.all20, a.all60,
                   2 * (least(0.01, greatest(0.000175, 0.0035 / ok.prev_close))
                        + case when ok.adv < 1e6 then 0.0025 when ok.adv < 1e7 then 0.0010
                               when ok.adv < 1e8 then 0.0005 else 0.0002 end) as cost
            from events e join ok on ok.permaticker = e.permaticker and ok.date = e.day
            left join avgs a on a.date = e.day and a.size = ok.size
        ) to '{folder()}/events.parquet' (format parquet)"""
    )
    print(con.sql(f"select size, count(*) from '{folder()}/events.parquet' group by 1").fetchall())


def run(period, cells) -> None:
    t = duckdb.sql(
        f"select *, year(day) as yr, (date_diff('day', DATE '2003-12-29', day) // 7) as week from '{folder()}/events.parquet'"
    ).to_arrow_table()
    d = {n: t.column(n).to_numpy(zero_copy_only=False) for n in t.column_names}
    first, last = PERIODS[period]
    for size, hold in cells:
        keep = (d["size"] == size) & (d["yr"] >= first) & (d["yr"] <= last)
        m = measure(d, keep, hold)
        ok = m["n"] >= 150 and m["over"] >= BAR[hold] and m["t"] >= 3 and m["pos"] >= 6 and m["net"] > 0
        print(show(f"early {size} {hold} {period}", m) + ("  MEETS THE BAR" if ok and period == "search" else ""))
        if period != "search" and m["n"] >= 3:
            print("    " + "  ".join(f"{y} {100 * v:.2f}%" for y, v in m["yearly"].items()))


if __name__ == "__main__":
    if sys.argv[1] == "table":
        table()
    elif sys.argv[1] == "search":
        run("search", [(s, h) for s in ("small", "mid") for h in (20, 60)])
    else:
        run(sys.argv[2], [(sys.argv[3], int(sys.argv[4]))])
