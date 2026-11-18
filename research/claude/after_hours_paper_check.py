"""Check that the paper ledger's code (src/kinn/after_hours_paper.py) reproduces the research
short on real data: the 2022 and 2023 events, read from the minute bars with the ledger's own
functions, against the research figures.

    cd research/claude
    uv run python after_hours_paper_check.py
"""

from __future__ import annotations

from collections import defaultdict

import duckdb
import numpy as np
import pyarrow.parquet as pq

import after_hours as ah
from kinn import after_hours_paper as ahp
from kinn.core.settings import load_settings
from kinn.data.store import DataStore


def main() -> None:
    store = DataStore(load_settings())
    out = ah.folder()
    events = [r for r in pq.read_table(out / "events.parquet").to_pylist()
              if r["timing"] == "after" and r["day"].year in (2022, 2023) and 3e8 <= r["mcap"] < 2e9]  # fmt: skip
    nxt = dict(duckdb.sql(
        f"""select e.symbol || e.day::varchar, p.open from (select unnest(?::varchar[]) as symbol, unnest(?::date[]) as day) e
            join read_parquet('{store.root}/panel/*.parquet') p on p.symbol = e.symbol
              and p.date = (select min(date) from read_parquet('{store.root}/panel/*.parquet') q where q.symbol = e.symbol and q.date > e.day)""",
        params=[[e["symbol"] for e in events], [e["day"] for e in events]],
    ).fetchall())  # fmt: skip
    by_day = defaultdict(list)
    for e in events:
        by_day[e["day"]].append(e)
    found = []
    for day, items in sorted(by_day.items()):
        bars = store.minute(day, symbols=[e["symbol"] for e in items], columns="symbol, minute_et, high, low, close, volume")
        sym = bars.column("symbol").to_pylist()
        cols = {n: bars.column(n).to_pylist() for n in ("minute_et", "high", "low", "close", "volume")}
        for e in items:
            mine = [ahp.MinuteBar(int(cols["minute_et"][i]), float(cols["high"][i]), float(cols["low"][i]),
                                  float(cols["close"][i]), float(cols["volume"][i]))
                    for i, s in enumerate(sym) if s == e["symbol"]]  # fmt: skip
            read = ahp.reading(mine, e["minute"])
            ok, _ = ahp.is_signal(read, e["mcap"], e["adv"])
            opened = nxt.get(e["symbol"] + e["day"].isoformat())
            if ok and opened:
                found.append((day.year, ahp.settle(read["entry"], float(opened), e["adv"])["net"]))
    for year in (2022, 2023):
        net = np.array([n for y, n in found if y == year])
        print(f"ledger code, {year}: {len(net)} signals, {100 * net.mean():.2f}% a trade after costs")
    d = ah.load_short()
    for year in (2022, 2023):
        keep = ah.pick(d, "after", "mid", "down15", "late" if year == 2022 else "check", ah.SHORT_REACTIONS) & (d["yr"] == year)
        net = d["g_open"][keep].astype(float) - d["cost"][keep]
        print(f"research,    {year}: {keep.sum()} signals, {100 * net.mean():.2f}% a trade after costs")


if __name__ == "__main__":
    main()
