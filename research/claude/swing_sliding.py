"""Sliding-window choice of the earnings rule's thresholds, and the rule by market cycle
(addendum of 2026-11-16 in strategies/swing_search/HYPOTHESIS.md; owner's question).

    uv run python research/claude/swing_sliding.py
"""

from __future__ import annotations

import itertools
from datetime import date

import numpy as np

import swing_news as news
from swing_early import trades
from swing_earnings import weekly

CYCLES = [
    ("2005 to Oct 2007: rising market", "2005-01-01", "2007-10-09"),
    ("Oct 2007 to Mar 2009: financial crisis", "2007-10-10", "2009-03-09"),
    ("Mar 2009 to Apr 2011: recovery", "2009-03-10", "2011-04-29"),
    ("May to Dec 2011: debt-ceiling sell-off", "2011-05-01", "2011-12-31"),
    ("2012 to mid-2015: rising market", "2012-01-01", "2015-07-31"),
    ("Aug 2015 to Feb 2016: sell-off", "2015-08-01", "2016-02-11"),
    ("Feb 2016 to Sep 2018: rising market", "2016-02-12", "2018-09-30"),
    ("Oct to Dec 2018: sell-off", "2018-10-01", "2018-12-31"),
    ("2019 to Feb 2020: rising market", "2019-01-01", "2020-02-19"),
    ("Feb to Mar 2020: pandemic crash", "2020-02-20", "2020-03-23"),
    ("Mar 2020 to 2021: boom", "2020-03-24", "2021-12-31"),
    ("2022: falling market", "2022-01-01", "2022-12-31"),
    ("2023 to Oct: recovery", "2023-01-01", "2023-10-13"),
]


def everything() -> dict[str, np.ndarray]:
    news.PERIODS["all_early"] = ("early", "d.day between DATE '2005-01-03' and DATE '2009-12-08'")
    news.PERIODS["all_wide"] = ("wide", "d.day between DATE '2010-01-04' and DATE '2023-10-13'")
    parts = [news.rows("all_early"), news.rows("all_wide")]
    return {k: np.concatenate([p[k] for p in parts]) for k in parts[0]}


def sliding(d: dict[str, np.ndarray]) -> None:
    days = np.array([date.fromisoformat(x) for x in d["day"]])
    grid = list(itertools.product(news.KINDS, news.JUMPS, news.VOLUMES, news.FLOORS, news.HOLDS))
    fixed = ("earnings-next", 0.15, 5.0, 5e7, 15)
    print(
        "year | fixed rule A50      | chosen on the 5 years before        | chosen on all years before"
    )
    totals = {"fixed": [], "five": [], "all": []}
    for year in range(2010, 2024):
        test = np.array([x.year == year for x in days])
        line = f"{year} |"
        for label, first in (("fixed", None), ("five", year - 5), ("all", 2005)):
            cell = fixed
            if first is not None:
                train = (days >= date(first, 1, 1)) & (days <= date(year - 1, 12, 8))
                best = None
                for c in grid:
                    keep = news.pick(d, *c[:4]) & train
                    if keep.sum() < 150:
                        continue
                    net = d[f"g{c[4]}"][keep] - d["cost"][keep]
                    t = weekly(net, d["week"][keep])[1]
                    if net.mean() >= 0.02 and (best is None or t > best[0]):
                        best = (t, c)
                if best is None:
                    line += f" {'nothing qualified':36}|"
                    continue
                cell = best[1]
            keep = news.pick(d, *cell[:4]) & test
            net = d[f"g{cell[4]}"][keep] - d["cost"][keep]
            totals[label].append(net)
            name = (
                ""
                if first is None
                else (
                    f" {cell[0][9:]:4} {100 * cell[1]:.0f}% {cell[2]:.0f}x "
                    f"${cell[3] / 1e6:.0f}M {cell[4]}d"
                )
            )
            line += f" {100 * net.mean():6.2f}% ({keep.sum():3d}){name:22}|"
        print(line)
    for label, parts in totals.items():
        net = np.concatenate(parts)
        print(f"{label:6}: {len(net)} trades, mean {100 * net.mean():.2f}% a trade, "
              f"sum of returns {net.sum():.1f}")  # fmt: skip


def cycles() -> None:
    parts = [trades("A50", p) for p in ("early", "search", "check")]
    d = {k: np.concatenate([p[k] for p in parts]) for k in parts[0]}
    net = d["g"] - d["cost"]
    print("\nA50 by market cycle (auction basis; the market column is all stocks, same holds)")
    for name, a, b in CYCLES:
        m = (d["day"] >= a) & (d["day"] <= b)
        if m.sum():
            print(f"  {name:42} {m.sum():4d} trades  mean {100 * net[m].mean():6.2f}%  "
                  f"winners {100 * (net[m] > 0).mean():3.0f}%  market {100 * d['mk'][m].mean():6.2f}%")  # fmt: skip


if __name__ == "__main__":
    sliding(everything())
    cycles()
