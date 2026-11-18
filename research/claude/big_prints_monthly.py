"""strategies/big_prints/HYPOTHESIS.md, follow-up 11: the monthly footprint ranking.

    cd research/claude
    uv run python big_prints_monthly.py table
    uv run python big_prints_monthly.py read <period>
"""

from __future__ import annotations

import sys
import tempfile

import duckdb

from big_prints import folder
from dividend_signal import PERIODS
from kinn.core.settings import load_settings
from kinn.data.store import DataStore
from swing_earnings import weekly


def table() -> None:
    store = DataStore(load_settings())
    bars = store.bars_roots[0] / "daily"
    tmp = tempfile.mkdtemp()
    con = duckdb.connect()
    con.execute(f"set threads=3; set memory_limit='2200MB'; set temp_directory='{tmp}'; set preserve_insertion_order=false")
    con.execute(
        f"""copy (
            with b as (select date, symbol, volume, transactions from read_parquet('{bars}/*.parquet')
                       where date <= DATE '2023-11-08' and transactions > 0 and volume > 0),
            p as (select p.permaticker, p.date, p.open, p.close, p.prev_close, p.adv20_prev as adv,
                         p.marketcap_prev as mcap, ln(b.volume / b.transactions) as la
                  from read_parquet('{store.root}/panel/*.parquet') p
                  join b on b.symbol = p.symbol and b.date = p.date
                  where p.date <= DATE '2023-11-08' and p.prev_close > 0 and p.close > 0 and p.open > 0
                    and p.category like '%Common Stock%')
            select permaticker, date, open, close, prev_close, adv, mcap,
                   avg(la) over (partition by permaticker order by date rows between 20 preceding and 1 preceding)
                   - avg(la) over (partition by permaticker order by date rows between 80 preceding and 21 preceding) as lfp,
                   count(*) over (partition by permaticker order by date rows between 80 preceding and 1 preceding) as n,
                   sum(ln(close / prev_close)) over (partition by permaticker order by date) as c
            from p
        ) to '{tmp}/m.parquet' (format parquet)"""
    )
    con.execute(
        f"""copy (
            with q as (select *, last_value(c) over (partition by permaticker order by date
                                 rows between current row and 19 following) as c20
                       from '{tmp}/m.parquet'),
            firsts as (select min(date) as date from q where date between DATE '2005-01-01' and DATE '2023-10-13'
                       group by year(date), month(date)),
            u as (select q.*, case when mcap < 3e8 then 'small' else 'mid' end as size,
                         exp(c20 - c) * close / open - 1 as g
                  from q join firsts f on f.date = q.date
                  where mcap >= 5e7 and mcap < 2e9 and adv >= 250000 and prev_close >= 2 and n = 80),
            r as (select *, ntile(10) over (partition by date, size order by lfp) as decile,
                         avg(g) over (partition by date, size) as all_g from u)
            select date as day, permaticker, size, exp(lfp) as fp20, g, all_g,
                   2 * (least(0.01, greatest(0.000175, 0.0035 / open))
                        + case when adv < 1e6 then 0.0025 when adv < 1e7 then 0.0010
                               when adv < 1e8 then 0.0005 else 0.0002 end) as cost
            from r where decile = 10
        ) to '{folder()}/monthly.parquet' (format parquet)"""
    )
    print(con.sql(f"select size, count(*), round(median(fp20), 2) from '{folder()}/monthly.parquet' group by 1").fetchall())


def read(period) -> None:
    t = duckdb.sql(
        f"select *, year(day) as yr, (date_diff('day', DATE '2003-12-29', day) // 7) as week from '{folder()}/monthly.parquet'"
    ).to_arrow_table()
    d = {n: t.column(n).to_numpy(zero_copy_only=False) for n in t.column_names}
    first, last = PERIODS[period]
    for size in ("small", "mid"):
        keep = (d["size"] == size) & (d["yr"] >= first) & (d["yr"] <= last)
        over = d["g"][keep] - d["all_g"][keep]
        net = d["g"][keep] - d["cost"][keep]
        _, tt, _ = weekly(over, d["week"][keep])
        years = d["yr"][keep]
        yearly = {int(y): over[years == y].mean() for y in sorted(set(years))}
        pos = sum(v > 0 for v in yearly.values())
        bar = (150, 0.01, 3, 6) if period == "search" else (0, 0.005, 2.5, 4)
        ok = len(over) >= bar[0] and over.mean() >= bar[1] and tt >= bar[2] and pos >= bar[3] and net.mean() > 0
        print(f"monthly {size:5} {period:7} {len(over):>6} trades  over the average {100 * over.mean():>6.2f}%  "
              f"t {tt:>5.2f}  yrs {pos} of {len(yearly)}  after costs {100 * net.mean():>6.2f}%"
              + ("  MEETS THE BAR" if ok else ""))  # fmt: skip
        if period != "search":
            print("    " + "  ".join(f"{y} {100 * v:.2f}%" for y, v in yearly.items()))


if __name__ == "__main__":
    if sys.argv[1] == "table":
        table()
    else:
        read(sys.argv[2])
