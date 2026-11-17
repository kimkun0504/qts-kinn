"""strategies/foreign_drift/HYPOTHESIS.md: rule A50 in companies that report on 6-K.

    cd research/claude
    uv run python foreign_drift.py table       # needs the owner's --what other download
    uv run python foreign_drift.py measure
    uv run python foreign_drift.py selfcheck   # the same pipeline on earnings 8-Ks: A50's count
"""

from __future__ import annotations

import bisect
import sys
import tempfile
from collections import defaultdict
from datetime import date, timedelta

import duckdb
import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
from swing_earnings import AUCTION, weekly

import sec_times
from kinn.core.settings import load_settings

SPANS = (("2005-09", 2005, 2009), ("2010-17", 2010, 2017), ("2018-23", 2018, 2023), ("all", 2005, 2023))
DATES = "d.day between DATE '2005-01-03' and DATE '2023-10-13'"
RULE = "ret2 >= 0.15 and dvr2 >= 5"
SIZES = {"small": "mcap >= 5e7 and mcap < 3e8", "mid": "mcap >= 3e8 and mcap < 2e9"}
QUALITY = "(ret250 > 0 or netcash_price < 0)"


def out_path(name: str):
    return load_settings().data_dir / "research" / "swing" / f"{name}.parquet"


def table(selfcheck: bool = False) -> None:
    """(stock, S): S is the session after the date of a 6-K from a company with no 8-K in the
    400 days before. With ``selfcheck``, earnings 8-Ks instead, to hold the pipeline to A50."""
    stocks, days = sec_times.numbers(), sec_times.sessions()
    eight = defaultdict(list)
    for row in sec_times.filings("8k.jsonl.gz"):
        if row["form"] == "8-K" and row["cik"] in stocks:
            if not selfcheck or "2.02" in row["items"].split(","):
                eight[row["cik"]].append(date.fromisoformat(row["filed"]))
    for filed in eight.values():
        filed.sort()
    found = set()
    if selfcheck:
        source = ((cik, f) for cik, dates in eight.items() for f in dates)
    else:
        source = ((r["cik"], date.fromisoformat(r["filed"])) for r in sec_times.filings("other_forms.jsonl.gz")
                  if r["form"] == "6-K" and r["cik"] in stocks)  # fmt: skip
    for cik, filed in source:
        if not selfcheck:
            had = eight.get(cik, [])
            at = bisect.bisect_right(had, filed)
            if at and had[at - 1] > filed - timedelta(days=400):
                continue  # an 8-K filer: A50's own ground
        session = sec_times.session_after(days, filed)
        if session:
            for permaticker in stocks[cik]:
                found.add((permaticker, session))
    name = "foreign_selfcheck" if selfcheck else "foreign"
    pq.write_table(pa.table({"permaticker": [k[0] for k in found], "day": [k[1] for k in found]}), out_path(name))
    print(f"{len(found)} (stock, session) pairs written to {out_path(name)}")


def trades(name: str, size: str, quality: bool) -> dict[str, np.ndarray]:
    base = load_settings().data_dir / "research" / "swing"
    con = duckdb.connect()
    con.execute(f"set threads=3; set memory_limit='1500MB'; set temp_directory='{tempfile.mkdtemp()}'")
    parts = []
    for tables in ("early", "wide"):
        parts.append(
            f"""select d.day, d.yr, (date_diff('day', DATE '2003-12-29', d.day) // 7) as week,
                       exp(first_day + c_exit15 - c_next) - 1 as g, {AUCTION} as cost,
                       (ret250 is not null)::int as has_year, (netcash_price is not null)::int as has_balance
                from read_parquet('{base}/{tables}_*.parquet') d
                join '{out_path(name)}' f on f.permaticker = d.permaticker and f.day = d.day
                where {DATES} and next_open is not null and {RULE} and {SIZES[size]}
                  {"and " + QUALITY if quality else ""}"""
        )
    table = con.sql(" union all ".join(parts)).to_arrow_table()
    return {n: table.column(n).to_numpy(zero_copy_only=False) for n in table.column_names}


def show(label: str, d: dict[str, np.ndarray]) -> None:
    net = d["g"] - d["cost"]
    print(f"{label}: {len(net)} trades; the year's return known for {int(d['has_year'].sum())}, "
          f"a balance sheet for {int(d['has_balance'].sum())}")  # fmt: skip
    for name, first, last in SPANS:
        keep = (d["yr"] >= first) & (d["yr"] <= last)
        if keep.sum() < 3:
            print(f"    {name:8} {int(keep.sum()):5}")
            continue
        _, t, _ = weekly(net[keep], d["week"][keep])
        years = sorted(set(d["yr"][keep]))
        positive = sum(net[keep & (d["yr"] == y)].mean() > 0 for y in years)
        print(f"    {name:8} {int(keep.sum()):5}  gross {100 * d['g'][keep].mean():6.2f}%  after costs "
              f"{100 * net[keep].mean():6.2f}%  weekly t {t:5.2f}  years {positive} of {len(years)}  "
              f"winners {100 * (net[keep] > 0).mean():3.0f}%")  # fmt: skip


def measure(name: str = "foreign") -> None:
    show("F50, $50M to $300M", trades(name, "small", False))
    show("F50Q, $50M to $300M", trades(name, "small", True))
    show("F50, $300M to $2B", trades(name, "mid", False))


if __name__ == "__main__":
    command = sys.argv[1]
    if command == "table":
        table()
    elif command == "selfcheck":
        table(selfcheck=True)
        d = trades("foreign_selfcheck", "small", False)
        print(f"earnings 8-Ks through this pipeline: {len(d['g'])} signals (A50 has about 1,551)")
    else:
        measure()
