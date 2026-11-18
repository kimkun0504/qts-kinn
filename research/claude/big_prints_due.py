"""strategies/big_prints/HYPOTHESIS.md, follow-up 10: the passed cell with a results report
expected inside the hold (the last results 8-K reacted 63 to 91 days before the signal).

    cd research/claude
    uv run python big_prints_due.py
"""

from __future__ import annotations

import bisect

import duckdb
import numpy as np

import sec_times
from big_prints import folder
from swing_earnings import weekly


def main(low: int = 63, high: int = 91, labels: tuple = ("report due", "not due")) -> None:
    stocks, days = sec_times.numbers(), sec_times.sessions()
    reports: dict = {}
    for row in sec_times.filings("8k.jsonl.gz"):
        if row["cik"] not in stocks or row["filed"] >= "2023-11-09":
            continue
        if "2.02" not in (row.get("items") or "").split(","):
            continue
        when = sec_times.accepted(row)
        d = sec_times.reaction_session(days, when) if when else None
        if d:
            for p in stocks[row["cik"]]:
                reports.setdefault(p, []).append(d)
    for p in reports:
        reports[p].sort()
    t = duckdb.sql(
        f"""select signal_day, permaticker, year(signal_day) as yr,
                   (date_diff('day', DATE '2003-12-29', signal_day) // 7) as week, g20 - all20 as over
            from '{folder()}/events_v9.parquet'
            where ret >= 0 and size = 'small' and fp >= 3 and quiet and signal_day <= DATE '2023-10-13'"""
    ).fetchall()
    rows = []
    for day, p, yr, week, over in t:
        got = reports.get(p, [])
        i = bisect.bisect_right(got, day) - 1  # the last results reaction on or before the signal
        due = i >= 0 and low <= (day - got[i]).days <= high
        rows.append((yr, week, over, due))
    yr, wk, o, due = (np.array(c) for c in zip(*rows, strict=True))
    for name, (a, b) in {"2010-2017": (2010, 2017), "2005-2009": (2005, 2009), "2018-2022": (2018, 2022),
                         "2023": (2023, 2023)}.items():  # fmt: skip
        k = (yr >= a) & (yr <= b)
        out = []
        for label, m in (("passed cell", k), (labels[0], k & due), (labels[1], k & ~due)):
            _, tt, _ = weekly(o[m], wk[m])
            years = yr[m]
            pos = sum(o[m][years == y].mean() > 0 for y in set(years))
            out.append(f"{label} {m.sum()} {100 * o[m].mean():+.2f}% (t {tt:.2f}; {pos} of {len(set(years))})")
        print(f"{name}: " + "; ".join(out))


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "after":
        main(5, 30, ("after results", "later"))
    else:
        main()
