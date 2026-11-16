"""Windows for the auction-fill measurement of rule A of the swing search
(strategies/swing_search/HYPOTHESIS.md): 150 of its trades from 2015 on at random, with the
ticks around the open of the entry day (09:25 to 09:40) and the close of the exit day (15:50
to 16:02). Writes a windows.csv for tools/owner/download_quotes.py. Reads no ticks.

    uv run python research/claude/swing_fill_sample.py
"""

from __future__ import annotations

import csv
import random

import pyarrow as pa
import pyarrow.parquet as pq

from kinn.core.settings import load_settings
from kinn.data import quotes, seal

TRADES, NAME = 150, "swing_auction"
OPEN = (565, 570, 580)  # window start, the auction, window end (minutes after midnight, ET)
CLOSE = (950, 959, 962)


def main() -> None:
    settings = load_settings()
    base = settings.data_dir / "research" / "swing" / "reprice"
    rows = pa.concat_tables(
        [pq.read_table(base / f"A_{p}.parquet") for p in ("search", "check")]
    ).to_pylist()
    rows = [r for r in rows if r["day_in"].year >= 2015 and r["dollars_out"] is not None]
    rows.sort(key=lambda r: (r["day"], r["symbol"]))
    chosen = random.Random(0).sample(rows, TRADES)
    out = settings.data_dir / "quotes_sample" / NAME
    out.mkdir(parents=True, exist_ok=True)
    windows = []
    for r in chosen:
        for side, day, symbol, price, (start, at, end) in (
            ("entry", r["day_in"], r["symbol_in"], r["open_in"], OPEN),
            ("exit", r["day_out"], r["symbol_out"], r["close_out"], CLOSE),
        ):
            seal.check_range(day, day, source="swing_fill_sample")
            windows.append(
                {
                    "day": day.isoformat(),
                    "symbol": symbol,
                    "signal_minute": at,
                    "entry_minute": at,
                    "entry_price": price,
                    "adv20_prev": r["adv"],
                    "start_ns": quotes.minute_ns(day, start),
                    "entry_ns": quotes.minute_ns(day, at),
                    "end_ns": quotes.minute_ns(day, end),
                    "bucket": "ADV under $1M" if r["adv"] < 1e6 else "ADV $1–10M",
                    "period": "2017–2023",
                    "side": side,
                    "signal_day": r["day"].isoformat(),
                }
            )
    with open(out / "windows.csv", "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=[*quotes.WINDOW_FIELDS, "side", "signal_day"])
        writer.writeheader()
        writer.writerows(sorted(windows, key=lambda w: (w["day"], w["symbol"])))
    print(f"{len(windows)} windows for {TRADES} trades -> {out / 'windows.csv'}")


if __name__ == "__main__":
    main()
