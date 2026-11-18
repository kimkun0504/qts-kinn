"""strategies/big_prints/HYPOTHESIS.md: quiet up days traded in unusually large pieces.

    cd research/claude
    uv run python big_prints.py table
    uv run python big_prints.py search
    uv run python big_prints.py test <period> <size> <hold>
"""

from __future__ import annotations

import sys
import tempfile

import duckdb
import numpy as np
import pyarrow as pa

import sec_times
from dividend_signal import PERIODS
from kinn.core.settings import load_settings
from kinn.data.store import DataStore
from swing_earnings import weekly


def folder():
    out = load_settings().data_dir / "research" / "big_prints"
    out.mkdir(parents=True, exist_ok=True)
    return out


def table() -> None:
    stocks, days = sec_times.numbers(), sec_times.sessions()
    news = set()
    for row in sec_times.filings("8k.jsonl.gz"):
        if row["cik"] not in stocks or row["filed"] >= "2023-11-09":
            continue
        when = sec_times.accepted(row)
        day = sec_times.reaction_session(days, when) if when else None
        if day is not None:
            news.update((p, day) for p in stocks[row["cik"]])
    filed = pa.table({"permaticker": [n[0] for n in news], "day": [n[1] for n in news]})
    store = DataStore(load_settings())
    bars = store.bars_roots[0] / "daily"
    tmp = tempfile.mkdtemp()
    con = duckdb.connect()
    con.execute(f"set threads=3; set memory_limit='2200MB'; set temp_directory='{tmp}'; set preserve_insertion_order=false")
    con.register("filed", filed)
    con.execute(
        f"""copy (
            with b as (select date, symbol, volume, transactions from read_parquet('{bars}/*.parquet')
                       where date <= DATE '2023-11-08' and transactions > 0 and volume > 0),
            p as (select p.permaticker, p.date, p.category, p.open, p.close, p.prev_close, p.adv20_prev as adv,
                         p.marketcap_prev as mcap, p.dollar_volume as dv, b.volume / b.transactions as ats
                  from read_parquet('{store.root}/panel/*.parquet') p
                  join b on b.symbol = p.symbol and b.date = p.date
                  where p.date <= DATE '2023-11-08' and p.prev_close > 0 and p.close > 0 and p.open > 0
                    and p.category like '%Common Stock%')
            select permaticker, date, open, close, prev_close, adv, mcap, dv,
                   ats / exp(avg(ln(ats)) over (partition by permaticker order by date rows between 60 preceding and 1 preceding)) as fp,
                   count(*) over (partition by permaticker order by date rows between 60 preceding and 1 preceding) as nfp,
                   sum(ln(close / prev_close)) over (partition by permaticker order by date) as c
            from p
        ) to '{tmp}/fp.parquet' (format parquet)"""
    )
    con.execute(
        f"""copy (
            with q as (select *, lead(c, 1) over w as c1, lead(open, 1) over w as o1, lead(close, 1) over w as cl1,
                              last_value(c) over (partition by permaticker order by date
                                                  rows between current row and 10 following) as c10,
                              last_value(c) over (partition by permaticker order by date
                                                  rows between current row and 20 following) as c20,
                              lead(c, 20) over w as c20_full
                       from '{tmp}/fp.parquet' window w as (partition by permaticker order by date)),
            ok as (select *, case when mcap < 3e8 then 'small' when mcap < 2e9 then 'mid' else 'large' end as size,
                          exp(c10 - c1) * cl1 / o1 - 1 as g10, exp(c20 - c1) * cl1 / o1 - 1 as g20
                   from q where nfp = 60 and c1 is not null
                     and ((mcap >= 3e8 and adv >= 1e6 and prev_close >= 5)
                          or (mcap >= 5e7 and mcap < 3e8 and adv >= 250000 and prev_close >= 2))
                     and date between DATE '2005-01-03' and DATE '2023-10-13'),
            daily as (select date, size, avg(g10) as all10, avg(g20) as all20,
                             avg(case when fp >= 2 then 1.0 else 0.0 end) as share from ok group by 1, 2)
            select ok.date as signal_day, ok.permaticker, ok.size, ok.fp, ok.dv / ok.adv as dvr, ok.c20_full is null as stopped,
                   ok.close / ok.prev_close - 1 as ret, ok.g10, ok.g20, d.all10, d.all20, d.share,
                   2 * (least(0.01, greatest(0.000175, 0.0035 / ok.close))
                        + case when ok.adv < 1e6 then 0.0025 when ok.adv < 1e7 then 0.0010
                               when ok.adv < 1e8 then 0.0005 else 0.0002 end) as cost
            from ok join daily d on d.date = ok.date and d.size = ok.size
            where (ok.fp >= 2 or ok.fp < 1.2) and ok.dv >= 1.5 * ok.adv and ok.close / ok.prev_close - 1 between 0 and 0.04
              and d.share < 0.05
              and not exists (select 1 from filed f where f.permaticker = ok.permaticker
                              and f.day between ok.date - 4 and ok.date)
        ) to '{folder()}/events_v4.parquet' (format parquet)"""
    )
    print(con.sql(f"select size, fp >= 2, count(*), sum(stopped::int) from '{folder()}/events_v4.parquet' group by 1, 2").fetchall())


def run(period, cells, name="events_v2") -> None:
    t = duckdb.sql(
        f"""select *, year(signal_day) as yr, (date_diff('day', DATE '2003-12-29', signal_day) // 7) as week
            from '{folder()}/{name}.parquet'"""
    ).to_arrow_table()
    d = {n: t.column(n).to_numpy(zero_copy_only=False) for n in t.column_names}
    first, last = PERIODS[period]
    for size, hold, floor in cells:
        g = d[f"g{hold}"].astype(float)
        avg = d[f"all{hold}"].astype(float)
        band = (d["fp"] >= floor) if floor > 0 else (d["fp"] < 1.2)
        keep = (d["size"] == size) & band & (d["yr"] >= first) & (d["yr"] <= last) & ~np.isnan(g)
        over = g[keep] - avg[keep]
        net = g[keep] - d["cost"][keep]
        _, tt, _ = weekly(over, d["week"][keep])
        years = d["yr"][keep]
        yearly = {int(y): over[years == y].mean() for y in sorted(set(years))}
        pos = sum(v > 0 for v in yearly.values())
        bar = (150, 0.01, 3, 6) if period == "search" else (0, 0.005, 2.5, 4)
        ok = len(over) >= bar[0] and over.mean() >= bar[1] and tt >= bar[2] and pos >= bar[3] and net.mean() > 0
        print(f"{size:5} {hold} fp>={floor} {period:7} {len(over):>6} trades  over the average {100 * over.mean():>6.2f}%  "
              f"t {tt:>5.2f}  yrs {pos} of {len(yearly)}  after costs {100 * net.mean():>6.2f}%"
              + ("  MEETS THE BAR" if ok else ""))  # fmt: skip
        if period != "search":
            print("    " + "  ".join(f"{y} {100 * v:.2f}%" for y, v in yearly.items()))


if __name__ == "__main__":
    if sys.argv[1] == "table":
        table()
    elif sys.argv[1] == "search":
        run("search", [(s, h, 2) for s in ("mid", "large") for h in (10, 20)], "events")
    elif sys.argv[1] == "stopped":
        for period in ("search", "early", "late", "check"):
            run(period, [("small", 20, 3)], "events_v4")
    elif sys.argv[1] == "control":
        for period in ("search", "early", "late"):
            run(period, [("small", 20, 0)], "events_v3")
    elif sys.argv[1] == "followup":
        run(sys.argv[2], [("mid", 20, 3), ("mid", 20, 4), ("small", 20, 2), ("small", 20, 3)])
    else:
        run(sys.argv[2], [(sys.argv[3], int(sys.argv[4]), float(sys.argv[5]))])
