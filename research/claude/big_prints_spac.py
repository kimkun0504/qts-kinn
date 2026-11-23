"""strategies/big_prints/HYPOTHESIS.md, follow-up 17: blank-check companies (SIC 6770) in the
passed cell.

    cd research/claude
    uv run python big_prints_spac.py
"""

from __future__ import annotations

import csv
import io
import zipfile

import duckdb
import numpy as np
import pyarrow as pa

from big_prints import folder
from kinn.core.settings import load_settings
from swing_earnings import weekly


def main() -> None:
    raw = max((load_settings().raw_dir / "sharadar").iterdir())
    sic = {}
    with zipfile.ZipFile(next(raw.glob("SHARADAR_TICKERS_*.zip"))) as z, z.open(z.namelist()[0]) as handle:
        for row in csv.DictReader(io.TextIOWrapper(handle, "utf-8")):
            if row["table"] == "SEP" and row.get("siccode"):
                sic[int(row["permaticker"])] = row["siccode"]
    t = duckdb.sql(
        f"""select permaticker, year(signal_day) as yr, (date_diff('day', DATE '2003-12-29', signal_day) // 7) as week,
                   g20 - all20 as over from '{folder()}/events_v10.parquet'
            where ret >= 0 and size = 'small' and fp >= 3 and quiet and signal_day <= DATE '2023-10-13'"""
    ).fetchnumpy()
    blank = np.array([sic.get(int(p), "").startswith("6770") for p in t["permaticker"]])
    for name, (a, b) in {"2005-2009": (2005, 2009), "2010-2017": (2010, 2017), "2018-2022": (2018, 2022),
                         "2023": (2023, 2023)}.items():  # fmt: skip
        k = (t["yr"] >= a) & (t["yr"] <= b)
        out = []
        for label, m in (("passed cell", k), ("without blank checks", k & ~blank), ("blank checks", k & blank)):
            if m.sum() < 3:
                out.append(f"{label} {m.sum()}")
                continue
            _, tt, _ = weekly(t["over"][m], t["week"][m])
            out.append(f"{label} {m.sum()} {100 * t['over'][m].mean():+.2f}% (t {tt:.2f})")
        print(f"{name}: " + "; ".join(out))
    _ = pa


if __name__ == "__main__":
    main()
