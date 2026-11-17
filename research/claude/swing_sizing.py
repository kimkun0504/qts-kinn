"""Sizing by how full the book is (addendum of 2026-11-17 in
strategies/earnings_drift/HYPOTHESIS.md): a position is larger while few are open.

    cd research/claude && uv run python swing_sizing.py
"""

from __future__ import annotations

import math
from collections import defaultdict

import numpy as np

import swing_overnight as so

ACCOUNT = 20000.0


def run(trades, basis: str, size) -> tuple[dict, int, float]:
    """The book day by day when ``size(open positions)`` gives each new position's dollars.
    Never more invested (at cost) than the account. Returns the daily P&L, the signals
    taken, and the mean dollars invested."""
    by_entry = defaultdict(list)
    for x in trades:
        by_entry[x["dates"][0]].append(x)
    held: list = []  # (last day, dollars)
    daily: dict = defaultdict(float)
    invested_by_day: dict = defaultdict(float)
    taken = 0
    for day in sorted(by_entry):
        held = [h for h in held if h[0] >= day]
        for x in sorted(by_entry[day], key=lambda x: (-x["t"]["volume"], x["t"]["symbol"])):
            dollars = size(len(held))
            if dollars <= 0 or sum(h[1] for h in held) + dollars > ACCOUNT + 1e-6:
                continue
            held.append((x["dates"][-1], dollars))
            taken += 1
            c = so.side_costs(x["t"], basis)
            daily[x["dates"][0]] -= dollars * c
            before = 1.0
            for d, s in zip(x["dates"], x["stock"], strict=True):
                daily[d] += dollars * (s - before)
                invested_by_day[d] += dollars
                before = s
            daily[x["dates"][-1]] -= dollars * x["stock"][-1] * (c + x["extra"])
    return daily, taken, invested_by_day


def describe(label: str, trades, size) -> None:
    line = f"{label:34}"
    for basis in ("auction", "crossed"):
        daily, taken, invested = run(trades, basis, size)
        days = sorted(d for d in daily if d.year >= 2006)
        pnl = np.array([daily[d] for d in days])
        equity = np.cumsum(pnl)
        drawdown = (np.maximum.accumulate(equity) - equity).max()
        span = (days[-1] - days[0]).days / 365.25
        totals = defaultdict(float)
        for d, x in zip(days, pnl, strict=True):
            totals[d.year] += x
        sharpe = pnl.mean() / pnl.std(ddof=1) * math.sqrt(252)
        line += (f" | {basis[:4]} taken {taken:4d} ${equity[-1] / span:6,.0f}/yr Sh {sharpe:4.2f} "
                 f"DD ${drawdown:6,.0f} worst {min(totals, key=totals.get)} "
                 f"${min(totals.values()):6,.0f} lose {sum(v < 0 for v in totals.values())}")  # fmt: skip
    print(line)


def main() -> None:
    a50, fund = so.load("A50"), so.index()
    keep = so.GROUPS["up or net debt"]
    sizes = {
        "10 positions of $2,000": lambda n: 2000.0 if n < 10 else 0.0,
        "V3: $4,000 while under 3 open": lambda n: 4000.0 if n < 3 else 2000.0,
        "V5: $4,000 while under 5 open": lambda n: 4000.0 if n < 5 else 2000.0,
    }
    for exit_label, options in (("15 sessions", {}), ("20-day exit", {"ema": 20})):
        trades = so.build(a50, fund, keep=keep, **options)
        print(exit_label)
        for label, size in sizes.items():
            describe(label, trades, size)


if __name__ == "__main__":
    main()
