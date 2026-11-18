"""strategies/busy_day/HYPOTHESIS.md: results jumps on crowded reporting days.

    cd research/claude
    uv run python busy_day.py table
    uv run python busy_day.py search
    uv run python busy_day.py test <period> <day> <hold>
"""

from __future__ import annotations

import sys
import tempfile
from collections import Counter

import duckdb
import numpy as np
import pyarrow as pa

import sec_times
from dividend_signal import BAR, PERIODS, measure, show
from kinn.core.settings import load_settings
from kinn.data.store import DataStore


def folder():
    out = load_settings().data_dir / "research" / "busy_day"
    out.mkdir(parents=True, exist_ok=True)
    return out


def table() -> None:
    stocks, days = sec_times.numbers(), sec_times.sessions()
    counts = Counter()
    hits = set()
    for row in sec_times.filings("8k.jsonl.gz"):
        if row["filed"] >= "2023-11-09" or "2.02" not in (row.get("items") or "").split(","):
            continue
        when = sec_times.accepted(row)
        day = sec_times.reaction_session(days, when) if when else None
        if day is None:
            continue
        counts[day] += 1
        for permaticker in stocks.get(row["cik"], ()):
            hits.add((permaticker, day))
    series = np.array([counts.get(d, 0) for d in days], dtype=float)
    label = {}
    for i, d in enumerate(days):
        if i < 250:
            continue
        past = series[i - 250 : i]
        label[d] = ("busy" if series[i] >= np.percentile(past, 80)
                    else "quiet" if series[i] <= np.percentile(past, 40) else "middle")  # fmt: skip
    events = pa.table({"permaticker": [h[0] for h in hits], "day": [h[1] for h in hits],
                       "crowd": [label.get(h[1], "none") for h in hits],
                       "count": [counts[h[1]] for h in hits]})  # fmt: skip
    store = DataStore(load_settings())
    con = duckdb.connect()
    con.execute(f"set threads=3; set memory_limit='2000MB'; set temp_directory='{tempfile.mkdtemp()}'")
    con.register("events", events)
    con.execute(
        f"""copy (
            with p as (select permaticker, date, category, close, prev_close, adv20_prev as adv,
                              marketcap_prev as mcap, open / close as oc, sum(ln(close / prev_close)) over w as c
                       from read_parquet('{store.root}/panel/*.parquet')
                       where date <= DATE '2023-11-08' and prev_close > 0 and close > 0 and open > 0
                       window w as (partition by permaticker order by date)),
            q as (select *, lead(date) over w as next_date, lead(c, 20) over w as c20, lead(c, 60) over w as c60,
                         lead(c) over w as c1, lead(oc) over w as oc1, lead(close) over w as close1
                  from p window w as (partition by permaticker order by date)),
            ok as (select * from q where category like '%Common Stock%' and mcap >= 3e8 and mcap < 2e9
                   and adv >= 1e6 and prev_close >= 2 and c20 is not null),
            avgs as (select next_date as date, avg(exp(c20 - c1) / oc1 - 1) as all20,
                            avg(exp(c60 - c1) / oc1 - 1) as all60 from ok group by 1)
            select ok.next_date as day, e.day as reaction_day, e.crowd, e.count, ok.permaticker, ok.mcap, ok.adv,
                   ok.close / ok.prev_close - 1 as reaction, ok.close as prev_close,
                   exp(ok.c20 - ok.c1) / ok.oc1 - 1 as g20, exp(ok.c60 - ok.c1) / ok.oc1 - 1 as g60,
                   a.all20, a.all60,
                   2 * (least(0.01, greatest(0.000175, 0.0035 / ok.close))
                        + case when ok.adv < 1e6 then 0.0025 when ok.adv < 1e7 then 0.0010
                               when ok.adv < 1e8 then 0.0005 else 0.0002 end) as cost
            from events e join ok on ok.permaticker = e.permaticker and ok.date = e.day
            left join avgs a on a.date = ok.next_date
            where ok.close / ok.prev_close - 1 >= 0.05 and e.day between DATE '2005-01-03' and DATE '2023-10-13'
        ) to '{folder()}/events.parquet' (format parquet)"""
    )
    print(con.sql(f"select crowd, count(*), round(avg(count)) from '{folder()}/events.parquet' group by 1").fetchall())


def run(period, cells) -> None:
    t = duckdb.sql(
        f"select *, year(day) as yr, (date_diff('day', DATE '2003-12-29', day) // 7) as week from '{folder()}/events.parquet'"
    ).to_arrow_table()
    d = {n: t.column(n).to_numpy(zero_copy_only=False) for n in t.column_names}
    first, last = PERIODS[period]
    for crowd, hold in cells:
        keep = (d["crowd"] == crowd) & (d["yr"] >= first) & (d["yr"] <= last)
        m = measure(d, keep, hold)
        ok = (crowd == "busy" and m["n"] >= 150 and m["over"] >= BAR[hold] and m["t"] >= 3 and m["pos"] >= 6
              and m["net"] > 0)  # fmt: skip
        print(show(f"{crowd} {hold} {period}", m) + ("  MEETS THE BAR" if ok and period == "search" else ""))
        if period != "search" and m["n"] >= 3:
            print("    " + "  ".join(f"{y} {100 * v:.2f}%" for y, v in m["yearly"].items()))


if __name__ == "__main__":
    if sys.argv[1] == "table":
        table()
    elif sys.argv[1] == "search":
        run("search", [(c, h) for c in ("busy", "quiet") for h in (20, 60)])
    else:
        run(sys.argv[2], [(sys.argv[3], int(sys.argv[4]))])
