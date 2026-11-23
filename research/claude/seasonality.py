"""strategies/seasonality/HYPOTHESIS.md: stocks repeat their own calendar months.

cd research/claude
uv run python seasonality.py table      # monthly returns, eligibility and scores
uv run python seasonality.py search     # 2010-2017, the four cells
uv run python seasonality.py test       # 2007-2009, 2018-2022 and the 2023 check
"""

from __future__ import annotations

import sys
import tempfile

import duckdb
import numpy as np

from kinn.core.settings import load_settings
from kinn.data.store import DataStore

LAST = "2023-10-31"
SIZES = {"large": (2e9, None, 5e6), "mid": (3e8, 2e9, 1e6)}
PERIODS = {
    "search": (2010, 2017),
    "early": (2007, 2009),
    "late": (2018, 2022),
    "check": (2023, 2023),
}
BORROW = 0.01 / 12


def folder():
    out = load_settings().data_dir / "research" / "seasonality"
    out.mkdir(parents=True, exist_ok=True)
    return out


def connect():
    con = duckdb.connect()
    con.execute(
        f"set threads=4; set memory_limit='3000MB'; set temp_directory='{tempfile.mkdtemp()}'"
    )
    return con


def table() -> None:
    store = DataStore(load_settings())
    con = connect()
    out = folder() / "months.parquet"
    con.execute(
        f"""copy (
            with p as (
                select permaticker, date, year(date) as y, month(date) as m, category, open, close,
                       prev_close, adv20_prev as adv, marketcap_prev as mcap,
                       case when prev_close > 0 and close > 0 and close / prev_close between 0.02 and 50
                            then ln(close / prev_close) else 0 end as lr
                from read_parquet('{store.root}/panel/*.parquet')
                where date <= DATE '{LAST}' and category like 'Domestic Common Stock%'),
            cal as (select y, m, count(distinct date) as sessions from p group by 1, 2),
            first as (
                select * from p qualify row_number() over (partition by permaticker, y, m order by date) = 1),
            month as (
                select permaticker, y, m, count(*) as days, sum(lr) as lr
                from p where close > 0 group by 1, 2, 3)
            select month.permaticker, month.y, month.m, month.lr, month.days = cal.sessions as full_month,
                   first.date as first_day, first.mcap, first.adv, first.prev_close,
                   case when first.open > 0 and first.prev_close > 0 and first.open / first.prev_close between 0.02 and 50
                        then month.lr - ln(first.open / first.prev_close) end as hold_lr,
                   least(0.01, greatest(0.000175, 0.0035 / first.prev_close)) as fee,
                   case when first.adv < 1e6 then 0.0025 when first.adv < 1e7 then 0.0010
                        when first.adv < 1e8 then 0.0005 else 0.0002 end as spread
            from month join cal using (y, m) join first using (permaticker, y, m)
        ) to '{out}' (format parquet)"""
    )
    con.execute(
        f"""copy (
            with r as (select permaticker, y, m, exp(lr) - 1 as ret from read_parquet('{out}') where full_month and (y, m) != (2003, 9))
            select a.permaticker, a.y, a.m, avg(b.ret) as score, count(*) as years
            from read_parquet('{out}') a join r b
              on b.permaticker = a.permaticker and b.m = a.m and b.y between a.y - 5 and a.y - 1
            group by 1, 2, 3 having count(*) >= 3
        ) to '{folder() / "scores.parquet"}' (format parquet)"""
    )
    n = con.sql(
        f"select count(*), min(y), max(y) from read_parquet('{folder() / 'scores.parquet'}')"
    ).fetchall()[0]
    print(f"scores: {n[0]:,} stock-months, {n[1]} to {n[2]}")


def ranked(con, size: str):
    low, high, adv = SIZES[size]
    cap = f"and mcap < {high}" if high else ""
    return con.sql(
        f"""
        with s as (
            select a.*, b.score, exp(a.hold_lr) - 1 as ret, 2 * (a.fee + a.spread) as cost1,
                   2 * (a.fee + 2 * a.spread) as cost2
            from read_parquet('{folder() / "months.parquet"}') a
            join read_parquet('{folder() / "scores.parquet"}') b using (permaticker, y, m)
            where a.mcap >= {low} {cap} and a.prev_close >= 5 and a.adv >= {adv} and a.hold_lr is not null
              and (a.y < 2023 or a.m <= 10))
        select *, ntile(10) over (partition by y, m order by score) as tenth,
               count(*) over (partition by y, m) as stocks
        from s"""
    ).df()


def months(frame):
    rows = []
    for (y, m), g in frame.groupby(["y", "m"]):
        top, bottom = g[g.tenth == 10], g[g.tenth == 1]
        universe = g.ret.mean()
        ic = np.corrcoef(g.score.rank(), g.ret.rank())[0, 1]
        rows.append(
            {
                "y": y,
                "m": m,
                "stocks": len(g),
                "top": len(top),
                "long1": top.ret.mean() - top.cost1.mean() - universe,
                "long2": top.ret.mean() - top.cost2.mean() - universe,
                "ls1": top.ret.mean()
                - bottom.ret.mean()
                - top.cost1.mean()
                - bottom.cost1.mean()
                - BORROW,
                "ls2": top.ret.mean()
                - bottom.ret.mean()
                - top.cost2.mean()
                - bottom.cost2.mean()
                - BORROW,
                "ic": ic,
                **{f"t{k}": g[g.tenth == k].ret.mean() - universe for k in range(1, 11)},
            }
        )
    import pandas as pd

    return pd.DataFrame(rows)


def summary(series, years):
    x = series.to_numpy()
    t = x.mean() / (x.std(ddof=1) / np.sqrt(len(x))) if len(x) > 1 and x.std() > 0 else float("nan")
    by_year = series.groupby(years).sum()
    return x.mean(), t, int((by_year > 0).sum()), len(by_year)


def report(name: str) -> None:
    first, last = PERIODS[name] if name != "test" else (None, None)
    names = ["search"] if name == "search" else ["early", "late", "check"]
    con = connect()
    for size in SIZES:
        frame = months(ranked(con, size))
        for period in names:
            a, b = PERIODS[period]
            p = frame[(frame.y >= a) & (frame.y <= b)]
            if p.empty:
                continue
            print(
                f"\n{size} {period} {a}-{b}: {len(p)} months, {p.stocks.median():.0f} stocks a month "
                f"(top tenth {p.top.median():.0f}); IC {p.ic.mean():+.4f}"
            )
            for cell, label in (
                ("long", "top tenth vs its size"),
                ("ls", "top minus bottom tenth"),
            ):
                m1, t1, up, n = summary(p[f"{cell}1"], p.y)
                m2, t2, _, _ = summary(p[f"{cell}2"], p.y)
                print(
                    f"  {label:24s} 1x {100 * m1:+.2f}%/month t {t1:5.2f} years up {up}/{n}; 2x {100 * m2:+.2f}% t {t2:5.2f}"
                )
            print(
                "  tenths 1..10 vs the average, before costs: "
                + " ".join(f"{100 * p[f't{k}'].mean():+.2f}" for k in range(1, 11))
            )
            if period != "check":
                yearly = p.groupby("y")[["long1", "ls1"]].sum()
                print(
                    "  by year (1x, long / long-short): "
                    + "  ".join(
                        f"{y} {100 * r.long1:+.1f}/{100 * r.ls1:+.1f}" for y, r in yearly.iterrows()
                    )
                )


if __name__ == "__main__":
    {"table": table, "search": lambda: report("search"), "test": lambda: report("test")}[
        sys.argv[1]
    ]()
