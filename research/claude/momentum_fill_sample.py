"""Windows for the fill measurement of the opening range breakout
(strategies/intraday_momentum/HYPOTHESIS.md, addendum of 2026-11-16 01:10 ET): 45 trades a
year at random from the development trades, 20 minutes of ticks from the entry bar. Writes a
windows.csv for tools/owner/download_quotes.py. Reads no ticks and starts no run."""

from __future__ import annotations

import csv
import glob
import random
from collections import defaultdict

import pyarrow as pa
import pyarrow.parquet as pq

from kinn.core.settings import load_settings
from kinn.data import quotes

PER_YEAR, MINUTES, NAME = 45, 20, "momentum_fills"


def main() -> None:
    settings = load_settings()
    base = settings.data_dir / "research" / "momentum"
    files = [pq.read_table(f) for f in sorted(glob.glob(str(base / "trades" / "*.parquet")))]
    trades = pa.concat_tables([f for f in files if f.num_columns], promote_options="default")
    by_year = defaultdict(list)
    for row in trades.to_pylist():
        if row["range"] == "or5":
            by_year[row["day"].year].append(row)
    rng = random.Random(0)
    out = settings.data_dir / "quotes_sample" / NAME
    out.mkdir(parents=True, exist_ok=True)
    chosen = []
    for year in sorted(by_year):
        rows = sorted(by_year[year], key=lambda r: (r["day"], r["symbol"]))
        chosen += rng.sample(rows, min(PER_YEAR, len(rows)))
    with open(out / "windows.csv", "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=[*quotes.WINDOW_FIELDS, "direction", "atr"])
        writer.writeheader()
        for r in sorted(chosen, key=lambda r: (r["day"], r["symbol"])):
            start = quotes.minute_ns(r["day"], r["entry_minute"])
            writer.writerow(
                {
                    "day": r["day"].isoformat(),
                    "symbol": r["symbol"],
                    "signal_minute": r["entry_minute"] - 1,
                    "entry_minute": r["entry_minute"],
                    "entry_price": r["entry"],
                    "adv20_prev": "",
                    "start_ns": start,
                    "entry_ns": start,
                    "end_ns": start + MINUTES * 60 * 1_000_000_000,
                    "bucket": "stocks in play",
                    "period": "2003–2016",
                    "direction": r["direction"],
                    "atr": r["atr"],
                }  # fmt: skip
            )
    print(f"{len(chosen)} windows -> {out / 'windows.csv'}")


if __name__ == "__main__":
    main()
