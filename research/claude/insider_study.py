"""The insider-buying study (strategies/insider_buying/HYPOTHESIS.md): signals joined to the
daily tables, the grid chosen on 2010 to 2017, and the test of chosen cells elsewhere.

    uv run python research/claude/insider_study.py build
    uv run python research/claude/insider_study.py choose
    uv run python research/claude/insider_study.py test <size> <dollars> <insiders> <officer> <fall> <hold> [periods]
"""

from __future__ import annotations

import itertools
import sys
import tempfile
from datetime import date

import duckdb
import numpy as np

from kinn.core.settings import load_settings
from swing_earnings import AUCTION, weekly

SIZES = {"under $50M": (0, 5e7), "$50M-$300M": (5e7, 3e8), "$300M-$2B": (3e8, 2e9),
         "over $2B": (2e9, 1e18)}  # fmt: skip
DOLLARS = (0.0, 1e5, 5e5)
INSIDERS = (1, 2, 3)
OFFICER = (False, True)
FALL = (False, True)
HOLDS = (5, 10, 15)
PERIODS = {
    "choose": ("2010-01-04", "2017-12-08"), "early": ("2006-01-03", "2009-12-08"),
    "late": ("2018-01-02", "2022-11-30"), "check": ("2023-01-03", "2023-09-29"),
}  # fmt: skip


def build() -> None:
    settings = load_settings()
    swing = settings.data_dir / "research" / "swing"
    out = settings.data_dir / "research" / "insider"
    con = duckdb.connect()
    con.execute(
        f"set threads=3; set memory_limit='2000MB'; set temp_directory='{tempfile.mkdtemp()}'"
    )
    con.execute(
        f"""create table sig as
            with p as (select * from '{out}/purchases.parquet'
                       where symbol is not null and symbol <> '' and filed is not null
                         and date_diff('day', traded, filed) between 0 and 10),
            d as (select symbol, filed, sum(dollars) as dollars, bool_or(officer) as officer,
                         bool_or(director) as director, bool_and(ten and not officer and not director) as only_ten
                  from p group by 1, 2)
            select d.*, (select count(distinct q.owner) from p q
                         where q.symbol = d.symbol and q.filed between d.filed - 14 and d.filed) as insiders
            from d"""
    )
    holds = ", ".join(f"exp(first_day + c_exit{h} - c_next) - 1 as g{h}, m.mk{h}" for h in HOLDS)
    for name, market in (("early", "market_early"), ("wide", "market")):
        con.execute(
            f"""copy (
                select s.symbol, s.filed, s.dollars, s.officer, s.director, s.only_ten, s.insiders,
                       w.day, w.yr, w.permaticker, w.mcap, w.adv, w.close, w.ret20, w.earn,
                       (date_diff('day', DATE '2003-12-29', w.day) // 7) as week,
                       {AUCTION} as cost, 2 * (half_spread + commission) as cost1, {holds}
                from sig s join read_parquet('{swing}/{name}_*.parquet') w
                  on w.symbol = s.symbol and w.day between s.filed - 5 and s.filed
                left join '{swing}/{market}.parquet' m on m.day = w.day
                where w.next_open is not null
                qualify row_number() over (partition by s.symbol, s.filed order by w.day desc) = 1
            ) to '{out}/signals_{name}.parquet' (format parquet)"""
        )
        print(
            name,
            con.sql(f"""select yr, count(*) from '{out}/signals_{name}.parquet'
                                group by 1 order by 1""").fetchall(),
        )


def rows(period: str) -> dict[str, np.ndarray]:
    settings = load_settings()
    out = settings.data_dir / "research" / "insider"
    a, b = PERIODS[period]
    table = duckdb.sql(
        f"""select * from read_parquet('{out}/signals_*.parquet')
            where day between DATE '{a}' and DATE '{b}' order by day, symbol"""
    ).to_arrow_table()
    d = {n: table.column(n).to_numpy(zero_copy_only=False) for n in table.column_names}
    d["ordinal"] = d["day"].astype("datetime64[D]").astype(np.int64)
    return d


def pick(d, size, dollars, insiders, officer, fall) -> np.ndarray:
    low, high = SIZES[size]
    keep = (d["mcap"] >= low) & (d["mcap"] < high) & (d["dollars"] >= dollars)
    keep &= d["insiders"] >= insiders
    if officer:
        keep &= d["officer"].astype(bool)
    if fall:
        keep &= d["ret20"] <= -0.10
    # One signal a company in any 21 days.
    index = np.flatnonzero(keep)
    last: dict[int, int] = {}
    for i in index:
        company, day = d["permaticker"][i], d["ordinal"][i]
        if day - last.get(company, -(10**9)) < 21:
            keep[i] = False
        else:
            last[company] = day
    return keep


def choose() -> None:
    d = rows("choose")
    print(f"{len(d['day'])} company-days with purchases, 2010-2017")
    found = []
    for cell in itertools.product(SIZES, DOLLARS, INSIDERS, OFFICER, FALL):
        keep = pick(d, *cell)
        if keep.sum() < 300:
            continue
        for h in HOLDS:
            net = d[f"g{h}"][keep] - d["cost"][keep]
            excess = d[f"g{h}"][keep] - d[f"mk{h}"][keep]
            _, t, weeks = weekly(net, d["week"][keep])
            found.append((t, net.mean(), excess.mean(), int(keep.sum()), *cell, h))
    eligible = sorted((f for f in found if f[1] >= 0.02 and f[0] >= 3), reverse=True)
    print(f"{len(found)} cells with 300+ trades (of 432); {len(eligible)} with 2%+ and t of 3+")
    print("     t   mean  over-market trades  size        dollars insiders officer fell hold")
    for f in sorted(found, reverse=True)[:25]:
        t, mean, excess, n, size, dollars, insiders, officer, fall, h = f
        mark = "*" if f in eligible[:5] else " "
        print(f"{mark}{t:5.2f} {100 * mean:5.2f}% {100 * excess:9.2f}% {n:6d}  {size:11} "
              f"{dollars / 1e3:5.0f}k {insiders:7d} {officer!s:>7} {fall!s:>5} {h:4d}")  # fmt: skip
    best = sorted(found, key=lambda f: -f[1])[:8]
    print("highest means:")
    for t, mean, excess, n, size, dollars, insiders, officer, fall, h in best:
        print(f" {t:5.2f} {100 * mean:5.2f}% {100 * excess:9.2f}% {n:6d}  {size:11} "
              f"{dollars / 1e3:5.0f}k {insiders:7d} {officer!s:>7} {fall!s:>5} {h:4d}")  # fmt: skip


def test(size, dollars, insiders, officer, fall, hold, periods) -> None:
    nets, weeks = [], []
    for period in periods:
        d = rows(period)
        keep = pick(d, size, dollars, insiders, officer, fall)
        g = d[f"g{hold}"][keep]
        net = g - d["cost"][keep]
        mean, t, n_weeks = weekly(net, d["week"][keep])
        print(f"{period}: {keep.sum()} trades in {n_weeks} weeks; gross {100 * g.mean():.2f}%  "
              f"auction basis {100 * net.mean():.2f}%  spread crossed "
              f"{100 * (g - d['cost1'][keep]).mean():.2f}%  over the market "
              f"{100 * (g - d[f'mk{hold}'][keep]).mean():.2f}%  weekly t {t:.2f}  "
              f"winners {100 * (net > 0).mean():.0f}%  median {100 * np.median(net):.2f}%")  # fmt: skip
        years = d["yr"][keep]
        print("   " + "  ".join(f"{y}: {100 * net[years == y].mean():.1f}% ({(years == y).sum()})"
                                for y in sorted(set(years))))  # fmt: skip
        nets.append(net)
        weeks.append(d["week"][keep])
    if len(periods) > 1:
        net, week = np.concatenate(nets), np.concatenate(weeks)
        print(f"together: {len(net)} trades, mean {100 * net.mean():.2f}%, "
              f"weekly t {weekly(net, week)[1]:.2f}")  # fmt: skip


if __name__ == "__main__":
    if sys.argv[1] == "build":
        build()
    elif sys.argv[1] == "choose":
        choose()
    else:
        size, dollars, insiders, officer, fall, hold = sys.argv[2:8]
        test(size, float(dollars), int(insiders), officer == "True", fall == "True", int(hold),
             sys.argv[8:] or ["early", "late"])  # fmt: skip
    _ = date
