"""strategies/big_prints/HYPOTHESIS.md, follow-up 5: large pieces on a mid-sized company's
results jump (events from busy_day).

    cd research/claude
    uv run python big_prints_jumps.py search
    uv run python big_prints_jumps.py test <period> <hold>
"""

from __future__ import annotations

import sys
import tempfile

import duckdb
import numpy as np

from busy_day import folder as busy
from dividend_signal import BAR, PERIODS
from kinn.core.settings import load_settings
from kinn.data.store import DataStore
from swing_earnings import weekly


def load():
    settings = load_settings()
    store = DataStore(settings)
    bars = store.bars_roots[0] / "daily"
    con = duckdb.connect()
    con.execute(f"set threads=3; set memory_limit='2000MB'; set temp_directory='{tempfile.mkdtemp()}'")
    d = con.sql(
        f"""with e as (select * from '{busy()}/events.parquet'),
            p as (select permaticker, date, symbol from read_parquet('{store.root}/panel/*.parquet')
                  where date <= DATE '2023-11-08' and permaticker in (select permaticker from e)),
            b as (select p.permaticker, p.date, d.volume / d.transactions as ats
                  from p join read_parquet('{bars}/*.parquet') d on d.symbol = p.symbol and d.date = p.date
                  where d.transactions > 0 and d.volume > 0),
            f as (select permaticker, date, ats / exp(avg(ln(ats)) over (partition by permaticker order by date
                         rows between 60 preceding and 1 preceding)) as fp,
                         count(*) over (partition by permaticker order by date
                         rows between 60 preceding and 1 preceding) as n
                  from b)
            select e.*, year(e.day) as yr, (date_diff('day', DATE '2003-12-29', e.day) // 7) as week, f.fp
            from e join f on f.permaticker = e.permaticker and f.date = e.reaction_day where f.n = 60"""
    ).fetchnumpy()
    out = {}
    for name, values in d.items():
        if np.ma.isMaskedArray(values):
            values = values.astype(float).filled(np.nan) if values.dtype.kind in "fiu" else values.filled(None)
        out[name] = values
    return out


def run(period, holds) -> None:
    d = load()
    first, last = PERIODS[period]
    for hold in holds:
        for label, band in (("footprint 1.5+", d["fp"] >= 1.5), ("under 1.5", d["fp"] < 1.5)):
            g, avg = d[f"g{hold}"], d[f"all{hold}"]
            keep = band & (d["yr"] >= first) & (d["yr"] <= last) & ~np.isnan(g) & ~np.isnan(avg)
            over, net = g[keep] - avg[keep], g[keep] - d["cost"][keep]
            _, t, _ = weekly(over, d["week"][keep])
            years = d["yr"][keep]
            yearly = {int(y): over[years == y].mean() for y in sorted(set(years))}
            pos = sum(v > 0 for v in yearly.values())
            bar = (150, BAR[hold], 3, 6) if period == "search" else (0, BAR[hold] / 2, 2.5, 4)
            ok = (label.startswith("footprint") and len(over) >= bar[0] and over.mean() >= bar[1] and t >= bar[2]
                  and pos >= bar[3] and net.mean() > 0)  # fmt: skip
            print(f"{label:15} {hold} {period:7} {len(over):>5} trades  over the average {100 * over.mean():>6.2f}%  "
                  f"t {t:>5.2f}  yrs {pos} of {len(yearly)}  after costs {100 * net.mean():>6.2f}%"
                  + ("  MEETS THE BAR" if ok else ""))  # fmt: skip
            if period != "search":
                print("    " + "  ".join(f"{y} {100 * v:.2f}%" for y, v in yearly.items()))


if __name__ == "__main__":
    if sys.argv[1] == "search":
        run("search", (20, 60))
    else:
        run(sys.argv[2], (int(sys.argv[3]),))
