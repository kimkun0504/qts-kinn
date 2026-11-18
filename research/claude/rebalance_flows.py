"""strategies/rebalance_flows/HYPOTHESIS.md: stocks against bonds at month end.

    cd research/claude
    uv run python rebalance_flows.py funds
    uv run python rebalance_flows.py measure search
"""

from __future__ import annotations

import csv
import io
import sys
import zipfile
from collections import defaultdict
from datetime import date

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq

from kinn.core.settings import load_settings

TICKERS = ("SPY", "TLT", "IEF", "IWM", "AGG")
SEALED = date(2023, 11, 9)
COST = 0.0006
PERIODS = {"search": (2010, 2017), "early": (2005, 2009), "late": (2018, 2022), "check": (2023, 2023)}


def path():
    out = load_settings().data_dir / "research" / "rebalance_flows"
    out.mkdir(parents=True, exist_ok=True)
    return out / "funds.parquet"


def funds() -> None:
    raw = max((load_settings().raw_dir / "sharadar").iterdir())
    rows = []
    with zipfile.ZipFile(next(raw.glob("SHARADAR_SFP_*.zip"))) as z, z.open(z.namelist()[0]) as handle:
        for row in csv.DictReader(io.TextIOWrapper(handle, "utf-8")):
            if row["ticker"] in TICKERS and row["date"] < SEALED.isoformat():
                rows.append((row["ticker"], date.fromisoformat(row["date"]), float(row["closeadj"])))
    pq.write_table(pa.table({"ticker": [r[0] for r in rows], "day": [r[1] for r in rows], "close": [r[2] for r in rows]}), path())
    print(len(rows), "rows")


def load(stock="SPY", bond="TLT"):
    by = defaultdict(dict)
    for r in pq.read_table(path()).to_pylist():
        by[r["ticker"]][r["day"]] = r["close"]
    days = sorted(set(by[stock]) & set(by[bond]))
    return days, np.array([by[stock][d] for d in days]), np.array([by[bond][d] for d in days])


def trades(stock="SPY", bond="TLT"):
    """One row a month: the month, R, the last-days spread (bonds minus stocks) and the
    first-days spread of the next month."""
    days, s, b = load(stock, bond)
    ends = [i for i in range(len(days) - 1) if days[i + 1].month != days[i].month]
    out = []
    for k in range(1, len(ends)):
        e, prev = ends[k], ends[k - 1]
        sig = e - 3
        if sig <= prev or e + 2 >= len(days):
            continue
        r = (s[sig] / s[prev] - 1) - (b[sig] / b[prev] - 1)
        last_days = (b[e] / b[sig] - 1) - (s[e] / s[sig] - 1)  # bonds minus stocks
        first_days = (b[e + 2] / b[e] - 1) - (s[e + 2] / s[e] - 1)
        long_only = (b[e] / b[sig] - 1) if r > 0 else (s[e] / s[sig] - 1)
        both = 0.5 * ((b[e] / b[sig] - 1) + (s[e] / s[sig] - 1))
        out.append((days[e], r, last_days, first_days, long_only, both))
    return out


def measure(*periods, stock="SPY", bond="TLT") -> None:
    rows = trades(stock, bond)
    month = np.array([r[0] for r in rows])
    years = np.array([d.year for d in month])
    r = np.array([x[1] for x in rows])
    last_days, first_days = np.array([x[2] for x in rows]), np.array([x[3] for x in rows])
    long_only, both = np.array([x[4] for x in rows]), np.array([x[5] for x in rows])
    for period in periods:
        a, b = PERIODS[period]
        span = (years >= a) & (years <= b)
        for window, values, sign in (("last days", last_days, 1), ("first days", first_days, -1)):
            for threshold in (0.0, 0.03):
                keep = span & (np.abs(r) > threshold)
                net = sign * np.sign(r[keep]) * values[keep] - COST
                if len(net) < 3:
                    print(f"{period} {window} {threshold}: {len(net)}")
                    continue
                t = net.mean() / (net.std(ddof=1) / len(net) ** 0.5)
                y = years[keep]
                pos = sum(net[y == v].mean() > 0 for v in set(y))
                extra = ""
                if window == "last days":
                    extra = f"  long-only {100 * (long_only[keep].mean() - both[keep].mean()):+.2f}% over half and half"
                print(f"{period:6} {window:10} |R|>{100 * threshold:.0f}%  {len(net):>3} trades  net {100 * net.mean():>6.2f}%  "
                      f"t {t:>5.2f}  yrs {pos} of {len(set(y))}  wins {100 * (net > 0).mean():.0f}%{extra}")  # fmt: skip
                if period != "search":
                    print("      " + "  ".join(f"{v} {100 * net[y == v].mean():.2f}%" for v in sorted(set(y))))


if __name__ == "__main__":
    if sys.argv[1] == "funds":
        funds()
    else:
        measure(*sys.argv[2:])
