"""strategies/first_report/HYPOTHESIS.md: A50's test on a new listing's first results.

    cd research/claude
    uv run python first_report.py spacs
    uv run python first_report.py search
    uv run python first_report.py test 15 small
"""

from __future__ import annotations

import csv
import io
import sys
import zipfile

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
from swing_early import trades
from swing_earnings import weekly

from kinn.core.settings import load_settings

TESTS = {15: (0.15, 5), 10: (0.10, 3)}
SIZES = {"small": (5e7, 3e8), "mid": (3e8, 2e9)}


def spac_path():
    return load_settings().data_dir / "research" / "swing" / "spacs.parquet"


def spacs() -> None:
    raw = max((load_settings().raw_dir / "sharadar").iterdir())
    found = []
    with zipfile.ZipFile(next(raw.glob("SHARADAR_TICKERS_*.zip"))) as z, z.open(z.namelist()[0]) as handle:
        for row in csv.DictReader(io.TextIOWrapper(handle, "utf-8")):
            if row["table"] == "SEP" and row["siccode"] == "6770":
                found.append(int(row["permaticker"]))
    pq.write_table(pa.table({"permaticker": found}), spac_path())
    print(len(found), "blank-check companies")


def firsts_path():
    return load_settings().data_dir / "research" / "swing" / "first_earn.parquet"


def firsts() -> None:
    """Each stock's first results event in the data (A50's event flag)."""
    import duckdb

    base = load_settings().data_dir / "research" / "swing"
    duckdb.execute(
        f"""copy (select permaticker, min(day) as day from (
                select permaticker, day from '{base}/earn.parquet' union all
                select permaticker, day from '{base}/earn_early.parquet') group by 1
        ) to '{firsts_path()}' (format parquet)"""
    )
    print(duckdb.sql(f"select count(*) from '{firsts_path()}'").fetchall())


def rule(test: int, size: str, year: bool = False) -> str:
    jump, volume = TESTS[test]
    lo, hi = SIZES[size]
    if year:
        return (f"earn and age <= 400 and ret2 >= {jump} and dvr2 >= {volume} and mcap >= {lo} and mcap < {hi}"
                f" and exists (select 1 from '{firsts_path()}' f where f.permaticker = d.permaticker"
                f"             and f.day >= d.day - 600)"
                f" and d.permaticker not in (select permaticker from '{spac_path()}')")  # fmt: skip
    return (f"earn and age <= 150 and ret2 >= {jump} and dvr2 >= {volume} and mcap >= {lo} and mcap < {hi}"
            f" and exists (select 1 from '{firsts_path()}' f where f.permaticker = d.permaticker and f.day = d.day)"
            f" and d.permaticker not in (select permaticker from '{spac_path()}')")  # fmt: skip


def summary(d, label, a, b):
    years = np.array([int(x[:4]) for x in d["day"]])
    k = (years >= a) & (years <= b)
    net = (d["g"] - d["cost"])[k]
    if len(net) < 3:
        print(f"{label:24} {len(net)}")
        return
    _, t, _ = weekly(net, d["week"][k])
    yearly = {y: net[years[k] == y].mean() for y in sorted(set(years[k]))}
    print(f"{label:24} {len(net):>4} trades  net {100 * net.mean():6.2f}%  median {100 * np.median(net):6.2f}%  "
          f"t {t:5.2f}  yrs {sum(v > 0 for v in yearly.values())} of {len(yearly)}")  # fmt: skip
    return yearly


def search(year: bool = False) -> None:
    for test in TESTS:
        for size in SIZES:
            summary(trades(rule(test, size, year), "search"), f"{'year' if year else 'first'} {test}% {size}", 2010, 2017)


def test(t, size, year: bool = False) -> None:
    for label, period, a, b in (("2005-2009", "early", 2005, 2009), ("2018-2022", "search", 2018, 2022)):
        yearly = summary(trades(rule(int(t), size, year), period), f"{'year' if year else 'first'} {t}% {size} {label}", a, b)
        if yearly:
            print("    " + "  ".join(f"{y} {100 * v:.2f}%" for y, v in yearly.items()))


if __name__ == "__main__":
    if sys.argv[1] == "spacs":
        spacs()
    elif sys.argv[1] == "firsts":
        firsts()
    elif sys.argv[1] == "search":
        search()
    elif sys.argv[1] == "search_year":
        search(year=True)
    elif sys.argv[1] == "test_year":
        test(*sys.argv[2:4], year=True)
    else:
        test(*sys.argv[2:4])
