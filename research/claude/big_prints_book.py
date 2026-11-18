"""strategies/big_prints: the passed cell as a book with a cap on open positions (a description,
not a test). $2,000 a position; each session the day's signals are taken largest footprint
first while fewer than the cap are open; each is held 20 sessions (stopped stocks at their last
close).

    cd research/claude
    uv run python big_prints_book.py
"""

from __future__ import annotations

from collections import defaultdict

import duckdb

from big_prints import folder
from kinn.core.settings import load_settings
from kinn.data.store import DataStore


def main() -> None:
    store = DataStore(load_settings())
    sessions = [r[0] for r in duckdb.sql(
        f"select distinct date from read_parquet('{store.root}/panel/*.parquet') where date <= DATE '2023-11-08' order by 1"
    ).fetchall()]  # fmt: skip
    index = {d: i for i, d in enumerate(sessions)}
    rows = duckdb.sql(
        f"""select signal_day, fp, g20 - cost as net, g20 - all20 - cost as hedged from '{folder()}/events_v8.parquet'
            where ret >= 0 and size = 'small' and fp >= 3 and quiet and signal_day <= DATE '2023-10-13'
            order by signal_day, fp desc"""
    ).fetchall()
    for cap in (10, 20, 30, 1000):
        busy_until: list[int] = []
        years = defaultdict(lambda: [0, 0.0, 0.0])
        for day, _, net, hedged in rows:
            k = index[day]
            busy_until = [e for e in busy_until if e >= k + 1]
            if len(busy_until) >= cap:
                continue
            busy_until.append(k + 20)
            y = years[day.year]
            y[0] += 1
            y[1] += 2000 * net
            y[2] += 2000 * hedged
        total = sum(v[1] for v in years.values())
        line = "  ".join(f"{y} {v[1]:+,.0f}" for y, v in sorted(years.items()))
        pos = sum(v[1] > 0 for v in years.values())
        hpos = sum(v[2] > 0 for v in years.values())
        label = "no cap" if cap == 1000 else f"cap {cap}"
        print(f"{label}: {sum(v[0] for v in years.values())} trades, ${total:,.0f} in all, "
              f"{pos} of {len(years)} years positive ({hpos} against the average)\n    {line}")


if __name__ == "__main__":
    main()
