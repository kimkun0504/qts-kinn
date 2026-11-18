"""strategies/friday_reports/HYPOTHESIS.md: rule A50's test on results first read on a Friday.

    cd research/claude
    uv run python swing_timed.py table          # the reaction sessions (family 24)
    uv run python friday_reports.py fridays
    uv run python friday_reports.py search
    uv run python friday_reports.py test 15 small
"""

from __future__ import annotations

import sys

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
from swing_early import trades
from swing_earnings import weekly

from kinn.core.settings import load_settings
from kinn.data.store import DataStore

SIZES = {"small": (5e7, 3e8), "mid": (3e8, 2e9)}


def base():
    return load_settings().data_dir / "research" / "swing"


def fridays() -> None:
    """Reaction sessions that are the last session of their week (a Friday, or before a holiday)."""
    store = DataStore(load_settings())
    from datetime import date

    days = store.sessions(date(2004, 12, 1), date(2023, 11, 8))
    last = {d for d, n in zip(days, days[1:], strict=False) if (n - d).days > 1 and d.weekday() >= 3}
    timed = pq.read_table(base() / "timed.parquet").to_pylist()
    rows = [r for r in timed if r["day"] in last]
    pq.write_table(pa.table({"permaticker": [r["permaticker"] for r in rows], "day": [r["day"] for r in rows]}), base() / "fridays.parquet")
    print(len(rows), "of", len(timed), "reaction sessions are the last of their week")


def rule(jump, size, friday=True) -> str:
    lo, hi = SIZES[size]
    exists = "exists" if friday else "not exists"
    return (f"ret2 >= {jump / 100} and dvr2 >= 5 and mcap >= {lo} and mcap < {hi}"
            f" and exists (select 1 from '{base()}/timed.parquet' t where t.permaticker = d.permaticker and t.day = d.prev_date)"
            f" and {exists} (select 1 from '{base()}/fridays.parquet' f where f.permaticker = d.permaticker and f.day = d.prev_date)")  # fmt: skip


def line(d, keep, label):
    net = (d["g"] - d["cost"])[keep]
    if len(net) < 3:
        return f"{label:30} {len(net)}"
    years = np.array([int(x[:4]) for x in d["day"]])[keep]
    _, t, _ = weekly(net, d["week"][keep])
    pos = sum(net[years == y].mean() > 0 for y in set(years))
    return f"{label:30} {len(net):>5} trades  net {100 * net.mean():>6.2f}%  median {100 * np.median(net):>6.2f}%  t {t:>5.2f}  yrs {pos} of {len(set(years))}"


def span(d, a, b):
    years = np.array([int(x[:4]) for x in d["day"]])
    return (years >= a) & (years <= b)


def search() -> None:
    for size in SIZES:
        for jump in (15, 10):
            d = trades(rule(jump, size), "search")
            print(line(d, span(d, 2010, 2017), f"friday {jump} {size}"))
            o = trades(rule(jump, size, friday=False), "search")
            print(line(o, span(o, 2010, 2017), f"  other days {jump} {size}"))


def test(jump, size) -> None:
    early = trades(rule(int(jump), size), "early")
    print(line(early, span(early, 2005, 2009), f"friday {jump} {size} 2005-2009"))
    d = trades(rule(int(jump), size), "search")
    print(line(d, span(d, 2018, 2022), f"friday {jump} {size} 2018-2022"))
    for name, x, a, b in (("2005-2009", early, 2005, 2009), ("2018-2022", d, 2018, 2022)):
        years = np.array([int(v[:4]) for v in x["day"]])
        net = x["g"] - x["cost"]
        print(f"    {name}: " + "  ".join(f"{y} {100 * net[years == y].mean():.1f}% ({(years == y).sum()})" for y in range(a, b + 1) if (years == y).any()))


if __name__ == "__main__":
    if sys.argv[1] == "fridays":
        fridays()
    elif sys.argv[1] == "search":
        search()
    else:
        test(*sys.argv[2:4])
