"""strategies/bad_items/HYPOTHESIS.md: shorts after 8-Ks that carry quiet bad news.

    cd research/claude
    uv run python bad_items.py table
    uv run python bad_items.py search
    uv run python bad_items.py test <period> <item> <size> <hold>
"""

from __future__ import annotations

import sys
import tempfile
from datetime import date

import duckdb
import numpy as np
import pyarrow as pa

import sec_times
from dividend_signal import PERIODS
from kinn.core.settings import load_settings
from kinn.data.store import DataStore
from self_tender import entry_session
from swing_earnings import weekly

ITEMS = ("3.02", "4.02", "2.04", "3.01", "4.01", "2.06")
BAR = {20: 0.01, 60: 0.02}


def folder():
    out = load_settings().data_dir / "research" / "bad_items"
    out.mkdir(parents=True, exist_ok=True)
    return out


def table(shelf: bool = False) -> None:
    stocks, days = sec_times.numbers(), sec_times.sessions()
    found = []
    source = "other_forms.jsonl.gz" if shelf else "8k.jsonl.gz"
    for row in sec_times.filings(source):
        if row["cik"] not in stocks or row["filed"] >= "2023-11-09":
            continue
        if shelf:
            items = {"S-3"} if row["form"] == "S-3" else set()
        else:
            items = set((row.get("items") or "").split(",")) & set(ITEMS)
        when = sec_times.accepted(row) if items else None
        if when:
            found.extend((when, row["cik"], item) for item in items)
    last: dict = {}
    rows = []
    gap = 365 if shelf else 90
    for when, cik, item in sorted(found):
        previous = last.get((cik, item))
        last[(cik, item)] = when[0]
        if previous is not None and (when[0] - previous).days <= gap:
            continue
        day = entry_session(days, when)
        if day is None or not date(2005, 1, 1) <= day <= date(2023, 10, 13):
            continue
        rows.extend((p, day, item) for p in stocks[cik])
    events = pa.table({"permaticker": [r[0] for r in rows], "day": [r[1] for r in rows], "item": [r[2] for r in rows]})
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
            q as (select *, lead(c, 19) over w as c20, lead(c, 59) over w as c60,
                         case when mcap < 3e8 then 'small' else 'mid' end as size
                  from p window w as (partition by permaticker order by date)),
            ok as (select * from q where category like '%Common Stock%' and mcap >= 5e7 and mcap < 2e9
                   and adv >= 250000 and prev_close >= 2 and c20 is not null),
            avgs as (select date, size, avg(exp(c20 - c) / oc - 1) as all20, avg(exp(c60 - c) / oc - 1) as all60
                     from ok group by 1, 2)
            select distinct e.item, e.day, ok.permaticker, ok.size, ok.adv, ok.prev_close,
                   exp(ok.c20 - ok.c) / ok.oc - 1 as g20, exp(ok.c60 - ok.c) / ok.oc - 1 as g60, a.all20, a.all60,
                   2 * (least(0.01, greatest(0.000175, 0.0035 / ok.prev_close))
                        + case when ok.adv < 1e6 then 0.0025 when ok.adv < 1e7 then 0.0010
                               when ok.adv < 1e8 then 0.0005 else 0.0002 end) as cost
            from events e join ok on ok.permaticker = e.permaticker and ok.date = e.day
            left join avgs a on a.date = e.day and a.size = ok.size
        ) to '{folder()}/{"shelf" if shelf else "events"}.parquet' (format parquet)"""
    )
    name = "shelf" if shelf else "events"
    print(con.sql(f"select item, size, count(*) from '{folder()}/{name}.parquet' where year(day) between 2010 and 2017 group by 1, 2 order by 1, 2").fetchall())


def run(period, cells, name="events") -> None:
    t = duckdb.sql(
        f"select *, year(day) as yr, (date_diff('day', DATE '2003-12-29', day) // 7) as week from '{folder()}/{name}.parquet'"
    ).to_arrow_table()
    d = {n: t.column(n).to_numpy(zero_copy_only=False) for n in t.column_names}
    first, last = PERIODS[period]
    met = []
    for item, size, hold in cells:
        g = d[f"g{hold}"].astype(float)
        avg = d[f"all{hold}"].astype(float)
        keep = (d["item"] == item) & (d["size"] == size) & (d["yr"] >= first) & (d["yr"] <= last) & ~np.isnan(g) & ~np.isnan(avg)
        n = int(keep.sum())
        if n < 3:
            print(f"{item} {size:5} {hold} {period:7} {n}")
            continue
        over = avg[keep] - g[keep]  # the short's return over the average
        net = -g[keep] - d["cost"][keep] - 0.10 * hold / 252
        _, tt, _ = weekly(over, d["week"][keep])
        years = d["yr"][keep]
        yearly = {int(y): over[years == y].mean() for y in sorted(set(years))}
        pos = sum(v > 0 for v in yearly.values())
        bar = (150, BAR[hold], 3, 6) if period == "search" else (0, BAR[hold] / 2, 2.5, 4)
        ok = n >= bar[0] and over.mean() >= bar[1] and tt >= bar[2] and pos >= bar[3] and net.mean() > 0
        label = f"{item} {size} {hold}"
        print(f"{label:16} {period:7} {n:>5} shorts  over the average {100 * over.mean():>6.2f}%  t {tt:>5.2f}  "
              f"yrs {pos} of {len(yearly)}  after costs and borrow {100 * net.mean():>6.2f}%" + ("  MEETS THE BAR" if ok else ""))  # fmt: skip
        if ok:
            met.append(label)
        if period != "search":
            print("    " + "  ".join(f"{y} {100 * v:.2f}%" for y, v in yearly.items()))
    if period == "search":
        print("\nMeet the search bar:", met or "none")


if __name__ == "__main__":
    if sys.argv[1] == "table":
        table()
    elif sys.argv[1] == "search":
        run("search", [(i, s, h) for i in ITEMS for s in ("small", "mid") for h in (20, 60)])
    elif sys.argv[1] == "shelf_table":
        table(shelf=True)
    elif sys.argv[1] == "shelf":
        run(sys.argv[2], [("S-3", s, h) for s in ("small", "mid") for h in (20, 60)], "shelf")
    else:
        run(sys.argv[2], [(sys.argv[3], sys.argv[4], int(sys.argv[5]))])
