"""The daily panel: one row per company per session, with what was known before that session.

Columns ending in ``_prev`` (and ``sessions_prior``) use only earlier sessions, so they are
available before the open of ``date``. Universes may filter on those and on static labels only.
The same-day columns (open .. dollar_volume) are outcomes of ``date`` and are not available
until its close.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import duckdb

ADV_WINDOW = 20


def build_panel(*, bars_root: Path, build_root: Path, memory_limit: str = "2GB") -> dict:
    """Write ``panel/year=YYYY.parquet`` under ``build_root``. Returns match statistics."""
    master = build_root / "master"
    shar = build_root / "sharadar"
    out = build_root / "panel"
    out.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as scratch:
        con = duckdb.connect(str(Path(scratch) / "panel.duckdb"))
        con.execute(f"set memory_limit='{memory_limit}'; set temp_directory='{scratch}'")
        con.execute("set preserve_insertion_order=false")
        con.execute(
            f"create view daily as select * from read_parquet('{bars_root}/daily/*.parquet')"
        )
        con.execute(f"create view hist as select * from '{master}/symbol_history.parquet'")
        con.execute(f"create view sec as select * from '{master}/security_master.parquet'")
        con.execute(f"create view splits as select * from '{master}/splits.parquet'")
        con.execute(
            f"""create view mcap as
                select s.permaticker, m.date, m.marketcap * 1e6 as marketcap
                from '{shar}/daily.parquet' m join sec s using (ticker)
                where m.marketcap is not null"""
        )
        # 1. Attach a company to each bar. A (date, symbol) claimed by two companies, or a
        #    company seen under two symbols on one date, is ambiguous and dropped.
        con.execute(
            """create table matched as
               select d.date, h.permaticker, d.symbol, d.open, d.high, d.low, d.close, d.volume,
                      d.close * d.volume as dollar_volume
               from daily d join hist h
                 on d.symbol = h.symbol and d.date >= h.valid_from and d.date < h.valid_to
               qualify count(*) over (partition by d.date, d.symbol) = 1
                   and count(*) over (partition by d.date, h.permaticker) = 1"""
        )
        stats = dict(
            zip(
                ("daily_rows", "matched_rows"),
                con.execute(
                    "select (select count(*) from daily), (select count(*) from matched)"
                ).fetchone(),
                strict=True,
            )
        )
        # 2. Lagged columns, per company (so they survive ticker changes).
        con.execute(
            f"""create table lagged as
                select m.*,
                       lag(m.close) over w as prev_close_raw,
                       lag(m.date) over w as prev_date,
                       median(m.dollar_volume) over (
                           partition by m.permaticker order by m.date
                           rows between {ADV_WINDOW} preceding and 1 preceding) as adv20_prev,
                       count(*) over (
                           partition by m.permaticker order by m.date
                           rows between unbounded preceding and 1 preceding) as sessions_prior
                from matched m
                window w as (partition by m.permaticker order by m.date)"""
        )
        con.execute("drop table matched")
        # 3. Split-adjust the prior close to today's share basis; attach the latest market cap
        #    dated strictly before today, and the static labels.
        con.execute(
            """create table panel as
               select l.date, l.permaticker, l.symbol, s.ticker, s.category, s.exchange,
                      l.open, l.high, l.low, l.close, l.volume, l.dollar_volume,
                      l.prev_close_raw / coalesce(sp.ratio, 1) as prev_close,
                      l.prev_date, coalesce(sp.ratio, 1) as split_ratio,
                      l.adv20_prev, l.sessions_prior,
                      mc.marketcap as marketcap_prev, mc.date as marketcap_date
               from lagged l
               join sec s using (permaticker)
               left join splits sp on sp.permaticker = l.permaticker and sp.date = l.date
               asof left join mcap mc on mc.permaticker = l.permaticker and mc.date < l.date"""
        )
        con.execute("drop table lagged")
        years = [
            r[0] for r in con.execute("select distinct year(date) from panel order by 1").fetchall()
        ]
        for year in years:
            tmp = out / f"year={year}.tmp"
            con.execute(
                f"""copy (select * from panel where year(date) = {year} order by date, symbol)
                    to '{tmp}' (format parquet, compression zstd)"""
            )
            os.replace(tmp, out / f"year={year}.parquet")
        stats["panel_rows"] = con.execute("select count(*) from panel").fetchone()[0]
        con.close()
    return stats
