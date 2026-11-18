"""strategies/big_prints/HYPOTHESIS.md, follow-up 13: large pieces in sector funds.

    cd research/claude
    uv run python big_prints_funds.py <period>
"""

from __future__ import annotations

import sys

import duckdb

from dividend_signal import PERIODS
from kinn.core.settings import load_settings
from kinn.data.store import DataStore
from swing_earnings import weekly

FUNDS = ("XLB XLE XLF XLI XLK XLP XLU XLV XLY SMH XBI IBB KRE KBE XRT XHB ITB IYR VNQ GDX XME OIH XOP IYT "
         "ITA KIE XSD IGV").split()  # fmt: skip


def main(period: str) -> None:
    bars = DataStore(load_settings()).bars_roots[0] / "daily"
    names = ", ".join(f"'{f}'" for f in FUNDS + ["SPY"])
    t = duckdb.sql(
        f"""with b as (select symbol, date, open, close, volume, transactions, close * volume as dv
                       from read_parquet('{bars}/*.parquet')
                       where symbol in ({names}) and date <= DATE '2023-11-08' and transactions > 0 and volume > 0),
            w as (select *, lag(close) over x as prev_close,
                         (volume / transactions) / exp(avg(ln(volume / transactions)) over (partition by symbol order by date
                             rows between 60 preceding and 1 preceding)) as fp,
                         count(*) over (partition by symbol order by date rows between 60 preceding and 1 preceding) as n,
                         median(dv) over (partition by symbol order by date rows between 20 preceding and 1 preceding) as adv,
                         lead(open) over x as o1, lead(close, 20) over x as c20, lead(date) over x as d1, lead(date, 20) over x as d20
                  from b window x as (partition by symbol order by date)),
            spy as (select date, close / prev_close - 1 as r, open, close from w where symbol = 'SPY'),
            day_share as (select date, avg(case when fp >= 2 then 1.0 else 0 end) as share from w
                          where symbol != 'SPY' and n = 60 group by 1)
            select w.date, year(w.date) as yr, (date_diff('day', DATE '2003-12-29', w.date) // 7) as week, w.symbol,
                   w.c20 / w.o1 - 1 - (s20.close / s1.open - 1) as over, w.c20 / w.o1 - 1 - 0.0004 - 2 * 0.000175 as net
            from w join spy s on s.date = w.date
            join spy s1 on s1.date = w.d1 join spy s20 on s20.date = w.d20
            join day_share h on h.date = w.date
            where w.symbol != 'SPY' and w.n = 60 and w.fp >= 2 and w.dv >= 1.5 * w.adv
              and (w.close / w.prev_close - 1) - s.r between 0 and 0.02 and h.share < 0.25
              and w.date between DATE '2005-01-03' and DATE '2023-10-13'"""
    ).fetchnumpy()
    first, last = PERIODS[period]
    k = (t["yr"] >= first) & (t["yr"] <= last)
    over, net = t["over"][k], t["net"][k]
    _, tt, _ = weekly(over, t["week"][k])
    years = t["yr"][k]
    yearly = {int(y): over[years == y].mean() for y in sorted(set(years))}
    pos = sum(v > 0 for v in yearly.values())
    bar = (150, 0.01, 3, 6) if period == "search" else (0, 0.005, 2.5, 4)
    ok = len(over) >= bar[0] and over.mean() >= bar[1] and tt >= bar[2] and pos >= bar[3] and net.mean() > 0
    print(f"funds {period}: {len(over)} trades, over SPY {100 * over.mean():+.2f}% (t {tt:.2f}; {pos} of {len(yearly)}), "
          f"after costs {100 * net.mean():+.2f}%" + ("  MEETS THE BAR" if ok else ""))  # fmt: skip
    if period != "search":
        print("    " + "  ".join(f"{y} {100 * v:.2f}%" for y, v in yearly.items()))


if __name__ == "__main__":
    main(sys.argv[1])
