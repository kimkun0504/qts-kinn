"""strategies/asset_growth/HYPOTHESIS.md: slow asset growers against fast ones.

    cd research/claude
    uv run python seasonality.py table      # the monthly returns this study shares
    uv run python asset_growth.py table     # growth of total assets, as known each month
    uv run python asset_growth.py search    # 2010-2017, the four cells
    uv run python asset_growth.py test      # 2005-2009, 2018-2022 and the 2023 check
"""

from __future__ import annotations

import sys
from datetime import timedelta

import pyarrow as pa
import pyarrow.parquet as pq

import seasonality
from kinn.core.settings import load_settings
from kinn.data.store import DataStore

PERIODS = {"search": (2010, 2017), "early": (2005, 2009), "late": (2018, 2022), "check": (2023, 2023)}
STALE = timedelta(days=500)


def folder():
    out = load_settings().data_dir / "research" / "asset_growth"
    out.mkdir(parents=True, exist_ok=True)
    return out


def table() -> None:
    store = DataStore(load_settings())
    months = seasonality.folder() / "months.parquet"
    con = seasonality.connect()
    firsts = con.sql(
        f"select y, m, min(first_day) as day from read_parquet('{months}') "
        "where y >= 2005 group by 1, 2 order by 1, 2"
    ).fetchall()
    rows = {"permaticker": [], "y": [], "m": [], "growth": []}
    for y, m, day in firsts:
        found = store.fundamentals_as_of(day, fields=("assets",)).to_pylist()
        for r in found:
            now, before = r["assets"], r["assets_year_ago"]
            if not now or not before or now <= 0 or before <= 0 or r["calendardate"] < day - STALE:
                continue
            rows["permaticker"].append(r["permaticker"])
            rows["y"].append(y)
            rows["m"].append(m)
            rows["growth"].append(now / before - 1)
    pq.write_table(pa.table(rows), folder() / "growth.parquet")
    print(f"growth: {len(rows['y']):,} company-months over {len(firsts)} months")


def ranked(con, size: str):
    low, high, adv = seasonality.SIZES[size]
    cap = f"and a.mcap < {high}" if high else ""
    return con.sql(
        f"""
        with s as (
            select a.*, g.growth as score, exp(a.hold_lr) - 1 as ret,
                   2 * (a.fee + a.spread) as cost1, 2 * (a.fee + 2 * a.spread) as cost2
            from read_parquet('{seasonality.folder() / "months.parquet"}') a
            join read_parquet('{folder() / "growth.parquet"}') g using (permaticker, y, m)
            where a.mcap >= {low} {cap} and a.prev_close >= 5 and a.adv >= {adv}
              and a.hold_lr is not null and (a.y < 2023 or a.m <= 10))
        select *, ntile(10) over (partition by y, m order by score desc) as tenth,
               count(*) over (partition by y, m) as stocks
        from s"""
    ).df()


def report(name: str) -> None:
    names = ["search"] if name == "search" else ["early", "late", "check"]
    con = seasonality.connect()
    for size in seasonality.SIZES:
        frame = seasonality.months(ranked(con, size))
        for period in names:
            a, b = PERIODS[period]
            p = frame[(frame.y >= a) & (frame.y <= b)]
            if p.empty:
                continue
            print(f"\n{size} {period} {a}-{b}: {len(p)} months, {p.stocks.median():.0f} stocks a month "
                  f"(lowest tenth {p.top.median():.0f}); rank correlation of -growth and return {p.ic.mean():+.4f}")
            for cell, label in (("long", "lowest tenth vs its size"), ("ls", "lowest minus highest tenth")):
                m1, t1, up, n = seasonality.summary(p[f"{cell}1"], p.y)
                m2, t2, _, _ = seasonality.summary(p[f"{cell}2"], p.y)
                print(f"  {label:27s} 1x {100 * m1:+.2f}%/month t {t1:5.2f} years up {up}/{n}; "
                      f"2x {100 * m2:+.2f}% t {t2:5.2f}")
            print("  tenths, fastest to slowest growth, vs the average, before costs: "
                  + " ".join(f"{100 * p[f't{k}'].mean():+.2f}" for k in range(1, 11)))
            if period != "check":
                yearly = p.groupby("y")[["long1", "ls1"]].sum()
                print("  by year (1x, long / long-short): " + "  ".join(
                    f"{y} {100 * r.long1:+.1f}/{100 * r.ls1:+.1f}" for y, r in yearly.iterrows()))


if __name__ == "__main__":
    {"table": table, "search": lambda: report("search"), "test": lambda: report("test")}[sys.argv[1]]()
