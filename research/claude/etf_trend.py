"""strategies/etf_trend/HYPOTHESIS.md: two fixed monthly rules on nine asset-class funds.

    cd research/claude
    uv run python etf_trend.py funds      # read the fund prices (before the seal) from Sharadar's file
    uv run python etf_trend.py measure
"""

from __future__ import annotations

import csv
import io
import math
import sys
import zipfile
from collections import defaultdict
from datetime import date

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq

import swing_overnight as so
from kinn.core.settings import HOLDOUT_START, load_settings

FUNDS = ["SPY", "IWM", "EFA", "EEM", "TLT", "IEF", "GLD", "DBC", "VNQ"]
CASH = "SHY"
COST = 0.0005
FIRST, LAST = date(2007, 3, 1), date(2023, 9, 29)
ACCOUNT, IDLE = 20000.0, 13000.0


def path():
    out = load_settings().data_dir / "research" / "etf"
    out.mkdir(parents=True, exist_ok=True)
    return out / "funds.parquet"


def funds() -> None:
    raw = max((load_settings().raw_dir / "sharadar").iterdir())
    wanted = {*FUNDS, CASH}
    rows = []
    with zipfile.ZipFile(next(raw.glob("SHARADAR_SFP_*.zip"))) as z, z.open(z.namelist()[0]) as handle:
        for row in csv.DictReader(io.TextIOWrapper(handle, "utf-8")):
            if row["ticker"] in wanted and row["date"] < HOLDOUT_START.isoformat():
                rows.append((row["ticker"], date.fromisoformat(row["date"]), float(row["closeadj"])))
    pq.write_table(pa.table({"ticker": [r[0] for r in rows], "date": [r[1] for r in rows],
                             "close": [r[2] for r in rows]}), path())  # fmt: skip
    print(f"{len(rows)} rows for {len({r[0] for r in rows})} funds")


def load():
    """Sessions every fund traded, and each fund's adjusted close on them."""
    table = pq.read_table(path()).to_pylist()
    by = defaultdict(dict)
    for r in table:
        by[r["ticker"]][r["date"]] = r["close"]
    days = sorted(set.intersection(*(set(v) for v in by.values())))
    return days, {t: np.array([by[t][d] for d in days]) for t in by}


def month_ends(days):
    return [i for i in range(len(days) - 1) if days[i].month != days[i + 1].month]


def weights_t1(close, ends, k):
    w = defaultdict(float)
    for fund in FUNDS:
        history = [close[fund][e] for e in ends[: k + 1]][-10:]
        held = fund if len(history) == 10 and close[fund][ends[k]] > np.mean(history) else CASH
        w[held] += 1 / len(FUNDS)
    return w


def weights_t2(close, ends, k):
    w = defaultdict(float)
    if k < 12:
        return {CASH: 1.0}
    year = {t: close[t][ends[k]] / close[t][ends[k - 12]] - 1 for t in [*FUNDS, CASH]}
    for fund in sorted(FUNDS, key=lambda t: -year[t])[:3]:
        w[fund if year[fund] > year[CASH] else CASH] += 1 / 3
    return w


def fixed(shares):
    return lambda close, ends, k: dict(shares)


def run(days, close, rule):
    """Daily returns of a rule: decided at each month end, traded at the next session's close."""
    names = [*FUNDS, CASH]
    daily = {t: np.r_[0.0, close[t][1:] / close[t][:-1] - 1] for t in names}
    ends = month_ends(days)
    change = {e + 1: k for k, e in enumerate(ends)}  # the session at whose close the new weights start
    w = {CASH: 1.0}
    out = np.zeros(len(days))
    for i in range(1, len(days)):
        out[i] = sum(share * daily[t][i] for t, share in w.items())
        if i in change:
            new = rule(close, ends, change[i])
            out[i] -= COST * sum(abs(new.get(t, 0.0) - w.get(t, 0.0)) for t in names)
            w = new
    return out, daily[CASH]


def stats(days, r, cash, first, last):
    keep = np.array([first <= d <= last for d in days])
    x, c = r[keep], cash[keep]
    growth = np.cumprod(1 + x)
    years = (np.array(days)[keep][-1] - np.array(days)[keep][0]).days / 365.25
    excess = x - c
    by = defaultdict(lambda: 1.0)
    for d, v in zip(np.array(days)[keep], x, strict=True):
        by[d.year] *= 1 + v
    return {"a_year": growth[-1] ** (1 / years) - 1, "sharpe": excess.mean() / excess.std(ddof=1) * math.sqrt(252),
            "drawdown": (1 - growth / np.maximum.accumulate(growth)).max(),
            "worst": min((v - 1, y) for y, v in by.items()), "by": {y: v - 1 for y, v in by.items()}}  # fmt: skip


def monthly(days, values, first, last):
    out = defaultdict(float)
    for d, v in zip(days, values, strict=True):
        if first <= d <= last:
            out[(d.year, d.month)] += v
    return out


def measure() -> None:
    days, close = load()
    print(f"{len(days)} sessions from {days[0]} to {days[-1]}; results {FIRST} to {LAST}")
    rules = {"T1 each on its own trend": weights_t1, "T2 the strongest three": weights_t2,
             "all nine held": fixed({t: 1 / 9 for t in FUNDS}), "60% SPY, 40% IEF": fixed({"SPY": 0.6, "IEF": 0.4})}  # fmt: skip
    a50, fund = so.load("A50"), so.index()
    book, _ = so.run_book(so.build(a50, fund, keep=so.GROUPS["up or net debt"]), "auction")
    book_m = monthly(sorted(book), [book[d] for d in sorted(book)], FIRST, LAST)
    months = sorted({(d.year, d.month) for d in days if FIRST <= d <= LAST})
    b = np.array([book_m.get(m, 0.0) for m in months])
    by_year = defaultdict(float)
    for m, v in zip(months, b, strict=True):
        by_year[m[0]] += v
    print(f"earnings book alone, by month: ${b.sum() / len(months) * 12:,.0f} a year, Sharpe "
          f"{b.mean() / b.std(ddof=1) * math.sqrt(12):.2f}, worst year {min(by_year, key=by_year.get)} ${min(by_year.values()):,.0f}")
    for name, rule in rules.items():
        r, cash = run(days, close, rule)
        whole = stats(days, r, cash, FIRST, LAST)
        a, c = stats(days, r, cash, FIRST, date(2014, 12, 31)), stats(days, r, cash, date(2015, 1, 1), LAST)
        print(f"\n{name}")
        print(f"  whole: {100 * whole['a_year']:.1f}% a year, Sharpe over cash {whole['sharpe']:.2f}, worst drawdown "
              f"{100 * whole['drawdown']:.1f}%, worst year {whole['worst'][1]} {100 * whole['worst'][0]:.1f}%, "
              f"2008 {100 * whole['by'][2008]:.1f}%, 2022 {100 * whole['by'][2022]:.1f}%")
        print(f"  2007-2014: {100 * a['a_year']:.1f}% a year, Sharpe {a['sharpe']:.2f}, drawdown {100 * a['drawdown']:.1f}% | "
              f"2015-2023: {100 * c['a_year']:.1f}% a year, Sharpe {c['sharpe']:.2f}, drawdown {100 * c['drawdown']:.1f}%")
        print("  by year: " + " ".join(f"{y % 100:02d}:{100 * v:.0f}" for y, v in sorted(whole["by"].items())))
        sleeve_m = monthly(days, r * IDLE, FIRST, LAST)
        s = np.array([sleeve_m.get(m, 0.0) for m in months])
        both = b + s
        year_both = defaultdict(float)
        for m, v in zip(months, both, strict=True):
            year_both[m[0]] += v
        print(f"  beside the earnings book: correlation by month {np.corrcoef(b, s)[0, 1]:.2f}; together ${both.sum() / len(months) * 12:,.0f} a year, "
              f"Sharpe {both.mean() / both.std(ddof=1) * math.sqrt(12):.2f}, worst year {min(year_both, key=year_both.get)} ${min(year_both.values()):,.0f}")


if __name__ == "__main__":
    {"funds": funds, "measure": measure}[sys.argv[1]]()
