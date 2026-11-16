"""The earnings rule and rule I with the small-stock index fund sold short against each
trade (strategies/insider_buying/HYPOTHESIS.md, addendum of 2026-11-16).

    uv run python research/claude/insider_hedge.py
"""

from __future__ import annotations

import math
from collections import defaultdict

import duckdb
import numpy as np

import insider_book as ib
import swing_book as book
from kinn.core.settings import load_settings
from kinn.data.store import DataStore

HEDGE_COST = 0.0010  # a trade: the fund's commission, spread and borrow


def fund_returns(symbol: str = "IWM") -> dict:
    """The fund's log return each session: open to close, and close to close (it has not
    split). From the daily bars, since funds are not in the company panel."""
    from datetime import date

    store = DataStore(load_settings())
    bars = store.daily(date(2005, 12, 1), date(2023, 11, 8), symbols=[symbol])
    con = duckdb.connect()
    con.register("bars", bars)
    rows = con.execute(
        """select date, ln(close / open) as first,
                  ln(close / lag(close) over (order by date)) as lr
           from bars order by date"""
    ).fetchall()
    return {d: (first, lr) for d, first, lr in rows if lr is not None}


def hedged(found: dict, fund: dict) -> dict:
    out = {}
    for key, t in found.items():
        if any(d not in fund for d in t["dates"]):
            continue
        r = [x - (fund[d][0] if i == 0 else fund[d][1])
             for i, (d, x) in enumerate(zip(t["dates"], t["r"], strict=True))]  # fmt: skip
        r[-1] += math.log(1 - HEDGE_COST)
        out[key] = {**t, "r": r}
    return out


def by_year(found: dict, label: str) -> None:
    years = defaultdict(list)
    for key, t in found.items():
        years[key[0].year].append(math.exp(sum(t["r"])) * (1 - t["costs"][0]) - (1 + t["costs"][0]))
    print(
        f"{label:26}"
        + " ".join(f"{y % 100:02d}:{100 * np.mean(v):5.1f}" for y, v in sorted(years.items()))
    )


def sleeves(parts: list[dict], label: str) -> None:
    for basis, name in ((0, "auction basis"), (1, "spread crossed")):
        series = defaultdict(float)
        for found in parts:
            days, pnl, _, _, _ = book.run(found, basis, 10, 1000.0)
            for d, x in zip(days, pnl, strict=True):
                if d.year >= 2006:
                    series[d] += x
        days = sorted(series)
        pnl = np.array([series[d] for d in days])
        equity = np.cumsum(pnl)
        drawdown = (np.maximum.accumulate(equity) - equity).max()
        years = (days[-1] - days[0]).days / 365.25
        totals = defaultdict(float)
        for d, x in zip(days, pnl, strict=True):
            totals[d.year] += x
        print(f"{label:30} {name:14} ${equity[-1] / years:6,.0f} a year  Sharpe "
              f"{pnl.mean() / pnl.std(ddof=1) * 252**0.5:4.2f}  drawdown ${drawdown:6,.0f}  worst year "
              f"${min(totals.values()):,.0f}  losing {sorted(y for y, v in totals.items() if v < 0)}")  # fmt: skip
        if basis == 0:
            print("      " + "  ".join(f"{y}: {v:,.0f}" for y, v in sorted(totals.items())))


def main() -> None:
    fund = fund_returns()
    print(len(fund), "sessions of IWM, from", min(fund), "to", max(fund))
    earn: dict = {}
    for period in ("early", "search", "check"):
        earn.update(book.paths("A50", period, "dvr2"))
    earn = {k: v for k, v in earn.items() if k[0].year >= 2006}
    ins = ib.insider_paths()
    earn_h, ins_h = hedged(earn, fund), hedged(ins, fund)
    print("mean a trade by year, auction basis (%)")
    by_year(earn, "earnings rule")
    by_year(earn_h, "earnings rule, hedged")
    by_year(ins, "rule I")
    by_year(ins_h, "rule I, hedged")
    sleeves([earn, ins], "two sleeves")
    sleeves([earn_h, ins_h], "two sleeves, hedged")
    sleeves([earn_h], "earnings sleeve only, hedged")


if __name__ == "__main__":
    main()
