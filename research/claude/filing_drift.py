"""strategies/filing_drift/HYPOTHESIS.md: rule A50's test on the session after a 10-Q or 10-K
of a company with no results 8-K in the ten sessions before.

    cd research/claude
    uv run python filing_drift.py events
    uv run python filing_drift.py search
    uv run python filing_drift.py test q50
"""

from __future__ import annotations

import bisect
import sys
from datetime import date

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
from swing_early import report, trades
from swing_earnings import weekly

import sec_times
from kinn.core.settings import load_settings

SEALED = date(2023, 11, 9)


def path():
    return load_settings().data_dir / "research" / "swing" / "filings10.parquet"


def events() -> None:
    stocks, days = sec_times.numbers(), sec_times.sessions()
    found = set()
    for row in sec_times.filings("other_forms.jsonl.gz"):
        if row["form"] not in ("10-Q", "10-K") or row["cik"] not in stocks:
            continue
        when = sec_times.accepted(row)
        if not when or when[0] >= SEALED:
            continue
        i = bisect.bisect_right(days, when[0])
        if i < len(days):
            for permaticker in stocks[row["cik"]]:
                found.add((permaticker, days[i]))
    pq.write_table(pa.table({"permaticker": [f[0] for f in found], "day": [f[1] for f in found]}), path())
    print(len(found), "filing sessions")


BASE = "ret2 >= {jump} and dvr2 >= 5 and mcap >= {lo} and mcap < {hi} and (esince > 10 or esince is null)"
CELLS = {
    "q50": BASE.format(jump=0.15, lo=5e7, hi=3e8),
    "q50_10": BASE.format(jump=0.10, lo=5e7, hi=3e8),
    "q50_mid": BASE.format(jump=0.15, lo=3e8, hi=2e9),
}


def rule(cell: str) -> str:
    return CELLS[cell] + f" and exists (select 1 from '{path()}' x where x.permaticker = d.permaticker and x.day = d.day)"


def summary(d, label):
    net = d["g"] - d["cost"]
    years = np.array([int(x[:4]) for x in d["day"]])
    _, t, _ = weekly(net, d["week"])
    pos = sum(net[years == y].mean() > 0 for y in set(years))
    print(f"{label:22} {len(net):>5} trades  net {100 * net.mean():>6.2f}%  median {100 * np.median(net):>6.2f}%  "
          f"t {t:>5.2f}  yrs {pos} of {len(set(years))}  winners {100 * (net > 0).mean():.0f}%")  # fmt: skip
    return years, net


def search() -> None:
    for cell in CELLS:
        d = trades(rule(cell), "search")
        keep = np.array([2010 <= int(x[:4]) <= 2017 for x in d["day"]])
        summary({k: v[keep] for k, v in d.items()}, cell)


def test(cell) -> None:
    early = trades(rule(cell), "early")
    years, net = summary(early, f"{cell} 2005-2009")
    print("    " + "  ".join(f"{y} {100 * net[years == y].mean():.2f}% ({(years == y).sum()})" for y in sorted(set(years))))
    d = trades(rule(cell), "search")
    keep = np.array([2018 <= int(x[:4]) <= 2022 for x in d["day"]])
    years, net = summary({k: v[keep] for k, v in d.items()}, f"{cell} 2018-2022")
    print("    " + "  ".join(f"{y} {100 * net[years == y].mean():.2f}% ({(years == y).sum()})" for y in sorted(set(years))))


if __name__ == "__main__":
    if sys.argv[1] == "events":
        events()
    elif sys.argv[1] == "search":
        search()
    else:
        test(sys.argv[2])
