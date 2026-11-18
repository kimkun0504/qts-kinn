"""strategies/russell_move/HYPOTHESIS.md: companies that move from the Russell 1000 to the
Russell 2000 (membership rebuilt from market values on the May rank day).

    cd research/claude
    uv run python russell_move.py table
    uv run python russell_move.py search
    uv run python russell_move.py test <period> <kind> <window>
"""

from __future__ import annotations

import sys
import tempfile
from datetime import date, timedelta

import duckdb
import numpy as np

from kinn.core.settings import load_settings
from kinn.data.store import DataStore
from swing_earnings import weekly

PERIODS = {"search": (2010, 2017), "early": (2005, 2009), "late": (2018, 2022), "check": (2023, 2023)}


def folder():
    out = load_settings().data_dir / "research" / "russell_move"
    out.mkdir(parents=True, exist_ok=True)
    return out


def recon_friday(year: int) -> date:
    day = date(year, 6, 30)
    while day.weekday() != 4:
        day -= timedelta(days=1)
    return day - timedelta(days=7) if day.day >= 29 else day


def table() -> None:
    store = DataStore(load_settings())
    con = duckdb.connect()
    con.execute(f"set threads=3; set memory_limit='2000MB'; set temp_directory='{tempfile.mkdtemp()}'")
    con.execute(
        f"""create table q as
            with p as (select permaticker, date, category, exchange, close, open, adv20_prev as adv,
                              marketcap_prev as mcap, open / close as oc, sum(ln(close / prev_close)) over w as c
                       from read_parquet('{store.root}/panel/*.parquet')
                       where date between DATE '2004-01-01' and DATE '2023-11-08' and prev_close > 0 and close > 0
                         and open > 0
                       window w as (partition by permaticker order by date))
            select *, row_number() over (partition by permaticker order by date) as s from p"""
    )
    days = [r[0] for r in con.sql("select distinct date from q order by 1").fetchall()]
    rows = []
    for year in range(2004, 2024):
        rank_day = max(d for d in days if d.year == year and d.month == 5)
        first = days[days.index(rank_day) + 1]
        recon = recon_friday(year)
        if recon not in days:
            recon = max(d for d in days if d <= recon)
        after = days[days.index(recon) + 1]
        rows.append((year, first, recon, after))
    con.execute("create table dates (yr int, first date, recon date, after date)")
    con.executemany("insert into dates values (?, ?, ?, ?)", rows)
    con.execute(
        """create table ranks as
           select d.yr, q.permaticker, q.mcap, q.adv, q.close,
                  row_number() over (partition by d.yr order by q.mcap desc) as rk
           from dates d join q on q.date = d.first
           where q.category like 'Domestic Common Stock%' and q.exchange in ('NYSE', 'NASDAQ', 'NYSEMKT', 'BATS', 'NYSEARCA')
             and q.mcap > 0 and q.close >= 1"""
    )
    con.execute(
        f"""copy (
            with r as (select a.*, b.rk as prev_rk from ranks a left join ranks b
                       on b.permaticker = a.permaticker and b.yr = a.yr - 1),
            w as (select r.*, d.first, d.recon, d.after,
                         exp(q2.c - q1.c) / q1.oc - 1 as g_into,
                         exp(q4.c - q3.c) / q3.oc - 1 as g_after, q3.adv as adv_after, q3.close as close_after
                  from r join dates d on d.yr = r.yr
                  join q q1 on q1.permaticker = r.permaticker and q1.date = d.first
                  join q q2 on q2.permaticker = r.permaticker and q2.date = d.recon
                  left join q q3 on q3.permaticker = r.permaticker and q3.date = d.after
                  left join q q4 on q4.permaticker = r.permaticker and q4.s = q3.s + 19),
            avgs as (select yr, avg(g_into) as all_into, avg(g_after) as all_after from w
                     where rk between 1001 and 3000 group by 1)
            select w.*, a.all_into, a.all_after,
                   case when w.prev_rk <= 1000 and w.rk between 1151 and 1600 then 'clearly' end as clearly,
                   case when w.prev_rk <= 1000 and w.rk > 1000 then 'down' end as down
            from w join avgs a on a.yr = w.yr
            where w.yr >= 2005 and w.prev_rk <= 1000 and w.rk > 1000
        ) to '{folder()}/events.parquet' (format parquet)"""
    )
    print(con.sql(f"select yr, count(*), count(clearly) from '{folder()}/events.parquet' group by 1 order by 1").fetchall())


def cost(price, adv):
    tier = np.where(adv < 1e6, 0.0025, np.where(adv < 1e7, 0.0010, np.where(adv < 1e8, 0.0005, 0.0002)))
    return 2 * (np.minimum(0.01, np.maximum(0.000175, 0.0035 / price)) + tier)


def run(period, cells) -> None:
    t = duckdb.sql(f"select * from '{folder()}/events.parquet'").to_arrow_table()
    d = {n: t.column(n).to_numpy(zero_copy_only=False) for n in t.column_names}
    first, last = PERIODS[period]
    for kind, window in cells:
        g = d[f"g_{window}"].astype(float)
        avg = d[f"all_{window}"].astype(float)
        price = (d["close"] if window == "into" else d["close_after"]).astype(float)
        adv = (d["adv"] if window == "into" else d["adv_after"]).astype(float)
        keep = (d["yr"] >= first) & (d["yr"] <= last) & ~np.isnan(g)
        if kind == "clearly":
            keep &= d["clearly"] == "clearly"
        n = int(keep.sum())
        over = g[keep] - avg[keep]
        net = g[keep] - cost(price[keep], np.nan_to_num(adv[keep]))
        _, tt, _ = weekly(over, d["yr"][keep])
        years = d["yr"][keep]
        yearly = {int(y): over[years == y].mean() for y in sorted(set(years))}
        pos = sum(v > 0 for v in yearly.values())
        bar = (150, 0.01, 3, 6) if period == "search" else (0, 0.005, 2.5, 4)
        ok = n >= bar[0] and over.mean() >= bar[1] and tt >= bar[2] and pos >= bar[3] and net.mean() > 0
        print(f"{kind:8} {window:6} {period:7} {n:>5} trades  over the average {100 * over.mean():>6.2f}%  t {tt:>5.2f}  "
              f"yrs {pos} of {len(yearly)}  after costs {100 * net.mean():>6.2f}%" + ("  MEETS THE BAR" if ok else ""))  # fmt: skip
        if period != "search":
            print("    " + "  ".join(f"{y} {100 * v:.2f}%" for y, v in yearly.items()))


if __name__ == "__main__":
    if sys.argv[1] == "table":
        table()
    elif sys.argv[1] == "search":
        run("search", [(k, w) for k in ("down", "clearly") for w in ("into", "after")])
    else:
        run(sys.argv[2], [(sys.argv[3], sys.argv[4])])
