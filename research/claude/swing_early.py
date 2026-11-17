"""The out-of-sample test of two fixed rules on 2005 to 2009 (addendum of 2026-11-16 in
strategies/swing_search/HYPOTHESIS.md), and the same rules on the search years for comparison.

    uv run python research/claude/swing_early.py A early     # or B; early, search or check
"""

from __future__ import annotations

import sys
import tempfile

import duckdb
import numpy as np
from swing_earnings import AUCTION, weekly

from kinn.core.settings import load_settings

RULES = {
    "A": "earn and ret2 >= 0.15 and dvr2 >= 5 and mcap < 3e8",
    "B": "m5 <= -0.07 and ret5 <= -0.20 and mcap >= 2e9",
    # Family 18's cells (chosen on 2010-2017): rule A with a $50M floor, and the wider one.
    "A50": "earn and ret2 >= 0.15 and dvr2 >= 5 and mcap >= 5e7 and mcap < 3e8",
    "A2": "earn and ret2 >= 0.10 and dvr2 >= 5 and mcap >= 5e7 and mcap < 3e8",
    # Family 19: an earnings 8-K dated the day of the jump itself, read on that day's move
    # (needs the join to earn0 that swing_overnight.load makes).
    "S50": "e0.p0 is not null and ret1 >= 0.15 and dvr >= 5 and mcap >= 5e7 and mcap < 3e8",
    # Family 4's cell: a pullback in a small winner.
    "C": """ret120 >= 0.50 and ret120 < 1.00 and ret5 <= -0.05 and ret5 >= -0.10
            and history >= 120 and mcap >= 3e8 and mcap < 2e9""",
}
PERIODS = {
    "early": ("early", "day between DATE '2005-01-03' and DATE '2009-12-08'"),
    "search": ("wide", "day between DATE '2010-01-04' and DATE '2022-11-30'"),
    "check": ("wide", "day between DATE '2023-01-03' and DATE '2023-10-13'"),
}


def trades(rule: str, period: str, hold: int = 15) -> dict[str, np.ndarray]:
    settings = load_settings()
    base = settings.data_dir / "research" / "swing"
    name, dates = PERIODS[period]
    market = "market_early" if name == "early" else "market"
    con = duckdb.connect()
    con.execute(
        f"set threads=3; set memory_limit='1500MB'; set temp_directory='{tempfile.mkdtemp()}'"
    )
    table = con.sql(
        f"""select day::varchar as day, symbol, yr, adv, mcap, close,
                   (date_diff('day', DATE '2003-12-29', day) // 7) as week,
                   exp(first_day + c_exit{hold} - c_next) - 1 as g,
                   exp(first_day + c_low{hold} - c_next) - 1 as low,
                   m.mk{hold} as mk, {AUCTION} as cost,
                   2 * (2 * half_spread + commission) as cost2, (ahead < {hold})::int as gone
            from read_parquet('{base}/{name}_*.parquet') d
            left join '{base}/{market}.parquet' m using (day)
            where {dates} and next_open is not null and ({RULES.get(rule, rule)})"""
    ).to_arrow_table()
    return {n: table.column(n).to_numpy(zero_copy_only=False) for n in table.column_names}


def report(d: dict[str, np.ndarray], label: str) -> None:
    g, net = d["g"], d["g"] - d["cost"]
    mean, t, weeks = weekly(net, d["week"])
    _, xt, _ = weekly(g - d["mk"], d["week"])
    print(f"{label}: {len(g)} trades in {weeks} weeks, {len(set(d['day']))} days")
    print(f"  gross {100 * g.mean():.2f}%  auction basis {100 * net.mean():.2f}%  "
          f"spread crossed twice over {100 * (g - d['cost2']).mean():.2f}%  "
          f"over all stocks {100 * (g - d['mk']).mean():.2f}%")  # fmt: skip
    print(f"  weekly: mean {100 * mean:.2f}%, t {t:.2f}; over all stocks t {xt:.2f}; "
          f"winners {100 * (net > 0).mean():.0f}%; median {100 * np.median(net):.2f}%; "
          f"mean worst point {100 * d['low'].mean():.1f}%; "
          f"stopped trading {100 * d['gone'].mean():.1f}%")  # fmt: skip
    for y in sorted(set(d["yr"])):
        m = d["yr"] == y
        print(f"  {y}: {m.sum():5d} trades on {len(set(d['day'][m])):3d} days  "
              f"auction basis {100 * net[m].mean():6.2f}%  gross {100 * g[m].mean():6.2f}%  "
              f"winners {100 * (net[m] > 0).mean():3.0f}%  "
              f"worst point {100 * d['low'][m].mean():6.1f}%")  # fmt: skip


if __name__ == "__main__":
    rule, period = sys.argv[1], sys.argv[2]
    hold = int(sys.argv[3]) if len(sys.argv) > 3 else 15
    report(trades(rule, period, hold), f"rule {rule[:60]}, {period}, hold {hold}")
