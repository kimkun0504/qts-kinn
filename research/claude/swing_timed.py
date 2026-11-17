"""Family 24 (addendum of 2026-11-17 15:33 ET in strategies/swing_search/HYPOTHESIS.md): the
earnings rule read on the session the report could first move the stock, by the SEC's
acceptance time.

    cd research/claude
    uv run python swing_timed.py table     # the reaction session of every earnings 8-K
    uv run python swing_timed.py measure
"""

from __future__ import annotations

import bisect
import csv
import gzip
import io
import json
import re
import sys
import zipfile
from collections import defaultdict
from datetime import UTC, date, datetime
from zoneinfo import ZoneInfo

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq

import swing_overnight as so
from kinn.core.settings import load_settings
from kinn.data.store import DataStore

NEW_YORK = ZoneInfo("America/New_York")
SPANS = (("2005-09", lambda y: y <= 2009), ("2010-17", lambda y: 2010 <= y <= 2017),
         ("2018-23", lambda y: y >= 2018), ("2018-23 ex-2020", lambda y: y >= 2018 and y != 2020))  # fmt: skip


def table() -> None:
    """(stock, R) for every earnings 8-K: R is the first session whose close comes after the
    SEC accepted the filing."""
    settings = load_settings()
    sessions = DataStore(settings).sessions(date(2004, 12, 1), date(2023, 11, 8))
    is_session = set(sessions)
    raw = max((settings.raw_dir / "sharadar").iterdir())
    numbers = defaultdict(set)
    with zipfile.ZipFile(next(raw.glob("SHARADAR_TICKERS_*.zip"))) as z, z.open(z.namelist()[0]) as handle:
        for row in csv.DictReader(io.TextIOWrapper(handle, "utf-8")):
            match = re.search(r"CIK=0*(\d+)", row.get("secfilings") or "")
            if match and row["table"] == "SEP":
                numbers[int(match.group(1))].add(int(row["permaticker"]))
    found = set()
    with gzip.open(settings.raw_dir / "sec" / "filing_times" / "8k.jsonl.gz", "rt") as handle:
        for line in handle:
            row = json.loads(line)
            if (row["form"] != "8-K" or row["cik"] not in numbers or not row["accepted"]
                    or "2.02" not in row["items"].split(",")):  # fmt: skip
                continue
            when = datetime.strptime(row["accepted"][:19], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=UTC)
            local = when.astimezone(NEW_YORK)
            day, minute = local.date(), local.hour * 60 + local.minute
            if day in is_session and minute < 960:
                session = day
            else:
                at = bisect.bisect_right(sessions, day)
                if at >= len(sessions) or (sessions[at] - day).days > 5:
                    continue
                session = sessions[at]
            for permaticker in numbers[row["cik"]]:
                found.add((permaticker, session))
    out = settings.data_dir / "research" / "swing" / "timed.parquet"
    pq.write_table(pa.table({"permaticker": [k[0] for k in found], "day": [k[1] for k in found]}), out)
    print(f"{len(found)} earnings reports with their reaction session, to {out}")


def spans(label: str, trades) -> None:
    rows = so.per_trade(trades)
    cells = [f"{name} {100 * np.mean([r for y, r in rows if ok(y)]):5.2f}% ({sum(ok(y) for y, _ in rows):4d})"
             for name, ok in SPANS]  # fmt: skip
    print(f"{label:34} " + "   ".join(cells))


def measure() -> None:
    a50, t50, fund = so.load("A50"), so.load("T50"), so.index()
    keep = so.GROUPS["up or net debt"]
    # The same event: T50's session R is A50's signal day, or the session before it.
    days = sorted({t["day"] for t in a50} | {t["day"] for t in t50})
    following = {d: days[i + 1] if i + 1 < len(days) else None for i, d in enumerate(days)}
    a50_keys = {(t["symbol"], t["day"]) for t in a50}
    same = sum((t["symbol"], t["day"]) in a50_keys for t in t50)
    earlier = sum((t["symbol"], t["day"]) not in a50_keys and (t["symbol"], following[t["day"]]) in a50_keys
                  for t in t50)  # fmt: skip
    print(f"A50: {len(a50)} signals. T50: {len(t50)} signals; {same} are A50's on the same day, "
          f"{earlier} are A50's a session earlier, {len(t50) - same - earlier} A50 does not take")
    print("\nA trade, auction basis:")
    spans("A50", so.build(a50, fund))
    spans("T50", so.build(t50, fund))
    spans("A50Q", so.build(a50, fund, keep=keep))
    spans("T50Q", so.build(t50, fund, keep=keep))
    print("\nBooks, 10 positions of $2,000:")
    so.describe("A50Q", so.build(a50, fund, keep=keep))
    so.describe("T50Q", so.build(t50, fund, keep=keep))
    so.describe("A50Q, 20-day exit", so.build(a50, fund, keep=keep, ema=20))
    so.describe("T50Q, 20-day exit", so.build(t50, fund, keep=keep, ema=20))
    so.by_year("T50Q", so.build(t50, fund, keep=keep))


if __name__ == "__main__":
    {"table": table, "measure": measure}[sys.argv[1]]()
