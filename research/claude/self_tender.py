"""strategies/self_tender/HYPOTHESIS.md: a company that files an issuer tender offer (SC TO-I).

    cd research/claude
    uv run python self_tender.py table
    uv run python self_tender.py search
    uv run python self_tender.py test <period> <size> <hold>
"""

from __future__ import annotations

import bisect
import sys
import tempfile
from datetime import date

import duckdb
import pyarrow as pa
import pyarrow.parquet as pq

from dividend_signal import BAR, PERIODS, measure, show
from kinn.core.settings import load_settings
from kinn.data.store import DataStore
from sec_times import accepted, filings, numbers, sessions

SIZES = {"small": (5e7, 3e8), "mid": (3e8, 1e15)}


def folder():
    out = load_settings().data_dir / "research" / "self_tender"
    out.mkdir(parents=True, exist_ok=True)
    return out


def entry_session(days, when):
    day, minute = when
    at = bisect.bisect_left(days, day)
    if at < len(days) and days[at] == day and minute < 570:
        return day
    at = bisect.bisect_right(days, day)
    return days[at] if at < len(days) and (days[at] - day).days <= 5 else None


def table() -> None:
    stocks = numbers()
    days = sessions()
    last = {}
    rows = []
    found = sorted(
        (accepted(r), r["cik"]) for r in filings("other_forms.jsonl.gz")
        if r["form"] == "SC TO-I" and r["cik"] in stocks and r["filed"] < "2023-11-09" and accepted(r)
    )  # fmt: skip
    for when, cik in found:
        previous = last.get(cik)
        last[cik] = when[0]
        if previous is not None and (when[0] - previous).days <= 365:
            continue
        day = entry_session(days, when)
        if day is None or not date(2005, 1, 1) <= day <= date(2023, 10, 13):
            continue
        for permaticker in stocks[cik]:
            rows.append((permaticker, day))
    pq.write_table(pa.table({"permaticker": [r[0] for r in rows], "day": [r[1] for r in rows]}),
                   folder() / "filings.parquet")  # fmt: skip
    store = DataStore(load_settings())
    con = duckdb.connect()
    con.execute(f"set threads=3; set memory_limit='2000MB'; set temp_directory='{tempfile.mkdtemp()}'")
    con.execute(
        f"""copy (
            with p as (select permaticker, date, category, close, prev_close, adv20_prev as adv, marketcap_prev as mcap,
                              open / close as oc, sum(ln(close / prev_close)) over w as c
                       from read_parquet('{store.root}/panel/*.parquet')
                       where date <= DATE '2023-11-08' and prev_close > 0 and close > 0 and open > 0
                       window w as (partition by permaticker order by date)),
            q as (select *, lead(c, 19) over w as c20, lead(c, 59) over w as c60,
                         case when mcap < 3e8 then 'small' else 'mid' end as size
                  from p window w as (partition by permaticker order by date)),
            ok as (select * from q where category like '%Common Stock%' and mcap >= 5e7 and adv >= 250000
                   and prev_close >= 2 and c20 is not null),
            avgs as (select date, size, avg(exp(c20 - c) / oc - 1) as all20, avg(exp(c60 - c) / oc - 1) as all60
                     from ok group by 1, 2)
            select distinct f.day, ok.permaticker, ok.size, ok.mcap, ok.adv, ok.prev_close,
                   exp(ok.c20 - ok.c) / ok.oc - 1 as g20, exp(ok.c60 - ok.c) / ok.oc - 1 as g60, a.all20, a.all60,
                   2 * (least(0.01, greatest(0.000175, 0.0035 / ok.prev_close))
                        + case when ok.adv < 1e6 then 0.0025 when ok.adv < 1e7 then 0.0010
                               when ok.adv < 1e8 then 0.0005 else 0.0002 end) as cost
            from '{folder()}/filings.parquet' f join ok on ok.permaticker = f.permaticker and ok.date = f.day
            left join avgs a on a.date = f.day and a.size = ok.size
        ) to '{folder()}/events.parquet' (format parquet)"""
    )
    print(con.sql(f"select size, count(*), min(day), max(day) from '{folder()}/events.parquet' group by 1").fetchall())


def load():
    t = duckdb.sql(
        f"select *, year(day) as yr, (date_diff('day', DATE '2003-12-29', day) // 7) as week from '{folder()}/events.parquet'"
    ).to_arrow_table()
    return {n: t.column(n).to_numpy(zero_copy_only=False) for n in t.column_names}


def run(period, cells) -> None:
    d = load()
    first, last = PERIODS[period]
    for size, hold in cells:
        keep = (d["size"] == size) & (d["yr"] >= first) & (d["yr"] <= last)
        m = measure(d, keep, hold)
        ok = m["n"] >= 3 and m["over"] >= BAR[hold] and m["t"] >= 3 and m["pos"] >= 6 and m["net"] > 0
        print(show(f"{size} {hold} {period}", m) + ("  MEETS THE BAR" if ok and period == "search" else ""))
        if period != "search" and m["n"] >= 3:
            print("    " + "  ".join(f"{y} {100 * v:.2f}%" for y, v in m["yearly"].items()))


if __name__ == "__main__":
    if sys.argv[1] == "table":
        table()
    elif sys.argv[1] == "search":
        run("search", [(s, h) for s in SIZES for h in (20, 60)])
    else:
        run(sys.argv[2], [(sys.argv[3], int(sys.argv[4]))])
