"""strategies/big_prints, follow-up 17 (b): how often the research skipped a session as an index
day (5% or more of eligible small stocks with a footprint of 2+), by year; and the same share
counted over every stock with $250,000 a day and $2 or more (what the paper ledger counts).

    cd research/claude
    uv run python big_prints_skipdays.py
"""

from __future__ import annotations

import tempfile

import duckdb

from kinn.core.settings import load_settings
from kinn.data.store import DataStore


def main() -> None:
    store = DataStore(load_settings())
    bars = store.bars_roots[0] / "daily"
    tmp = tempfile.mkdtemp()
    con = duckdb.connect()
    con.execute(f"set threads=3; set memory_limit='2200MB'; set temp_directory='{tmp}'; set preserve_insertion_order=false")
    con.execute(
        f"""copy (
            with b as (select date, symbol, close, volume, transactions,
                              ln(volume / transactions) as la, close * volume as dv
                       from read_parquet('{bars}/*.parquet')
                       where date between DATE '2004-06-01' and DATE '2023-11-08' and transactions > 0 and volume > 0),
            w as (select date, symbol, exp(la - avg(la) over x) as fp, count(*) over x as n,
                         median(dv) over (partition by symbol order by date rows between 20 preceding and 1 preceding) as adv,
                         lag(close) over (partition by symbol order by date) as prev_close
                  from b window x as (partition by symbol order by date rows between 60 preceding and 1 preceding))
            select w.date, w.symbol, w.fp, w.adv, w.prev_close, p.marketcap_prev as mcap, p.category
            from w left join read_parquet('{store.root}/panel/*.parquet') p on p.symbol = w.symbol and p.date = w.date
            where w.n = 60 and w.date >= DATE '2005-01-03'
        ) to '{tmp}/s.parquet' (format parquet)"""
    )
    print(con.sql(
        f"""with d as (
                select date,
                       avg(case when fp >= 2 then 1.0 else 0 end) filter (where category like '%Common Stock%'
                           and mcap >= 5e7 and mcap < 3e8 and adv >= 250000 and prev_close >= 2) as small_share,
                       avg(case when fp >= 2 then 1.0 else 0 end) filter (where adv >= 250000 and prev_close >= 2) as all_share
                from '{tmp}/s.parquet' group by 1)
            select year(date) as yr, count(*) as days,
                   round(100 * avg(case when small_share >= 0.05 then 1.0 else 0 end), 1) as pct_skipped_research,
                   round(100 * avg(case when all_share >= 0.05 then 1.0 else 0 end), 1) as pct_skipped_all_stocks,
                   round(100 * median(small_share), 2) as median_small, round(100 * median(all_share), 2) as median_all
            from d group by 1 order by 1"""
    ).fetchall())


if __name__ == "__main__":
    main()
