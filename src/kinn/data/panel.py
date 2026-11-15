"""The daily panel: one row per company per session, with what was known before that session.

Columns ending in ``_prev`` (and ``sessions_prior``) use only earlier sessions, so they are
available before the open of ``date``. Universes may filter on those and on static labels only.
The same-day columns (open .. dollar_volume) are outcomes of ``date`` and are not available
until its close.

Built one year at a time, each with the previous calendar year as lookback, so it fits in a
small machine. ``adv20_prev`` is the median dollar volume of the company's last 20 sessions
with a bar, looking back no further than the start of the previous calendar year.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import duckdb

ADV_WINDOW = 20


def build_panel(*, bars_root: Path, build_root: Path, memory_limit: str = "1500MB") -> dict:
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
        # 1. Which company each (date, symbol) is, over the whole history but narrow.
        #    A symbol claimed by two companies on one date, or a company seen under two
        #    symbols on one date, is ambiguous and dropped.
        con.execute(
            """create table claim as
               select d.date, d.symbol, min(h.permaticker) as permaticker
               from daily d join hist h
                 on d.symbol = h.symbol and d.date >= h.valid_from and d.date < h.valid_to
               group by d.date, d.symbol having count(*) = 1"""
        )
        con.execute(
            """create table ident as
               select date, min(symbol) as symbol, permaticker,
                      (row_number() over (partition by permaticker order by date) - 1)::integer
                        as sessions_prior
               from claim group by date, permaticker having count(*) = 1"""
        )
        daily_rows, claimed = con.execute(
            "select (select count(*) from daily), (select count(*) from claim)"
        ).fetchone()
        con.execute("drop table claim")
        panel_rows = con.execute("select count(*) from ident").fetchone()[0]
        years = [
            r[0] for r in con.execute("select distinct year(date) from ident order by 1").fetchall()
        ]
        # 2. Per year: lagged columns per company (so they survive ticker changes), the prior
        #    close split-adjusted to today's share basis, and the previous session's market cap.
        for year in years:
            tmp = out / f"year={year}.tmp"
            con.execute(
                f"""copy (
                    with bars as (
                        select i.permaticker, i.sessions_prior, d.*, d.close * d.volume
                                 as dollar_volume
                        from ident i join daily d using (date, symbol)
                        where year(i.date) in ({year - 1}, {year})
                          and year(d.date) in ({year - 1}, {year})),
                    lagged as (
                        select *, lag(close) over w as prev_close_raw, lag(date) over w
                                 as prev_date,
                               median(dollar_volume) over (
                                   partition by permaticker order by date
                                   rows between {ADV_WINDOW} preceding and 1 preceding)
                                 as adv20_prev
                        from bars window w as (partition by permaticker order by date))
                    select l.date, l.permaticker, l.symbol, s.ticker, s.category, s.exchange,
                           l.open, l.high, l.low, l.close, l.volume, l.dollar_volume,
                           l.prev_close_raw / coalesce(sp.ratio, 1) as prev_close,
                           l.prev_date, coalesce(sp.ratio, 1) as split_ratio,
                           l.adv20_prev, l.sessions_prior, mc.marketcap as marketcap_prev
                    from lagged l
                    join sec s using (permaticker)
                    left join splits sp on sp.permaticker = l.permaticker and sp.date = l.date
                    left join mcap mc on mc.permaticker = l.permaticker and mc.date = l.prev_date
                    where year(l.date) = {year}
                    order by l.date, l.symbol)
                    to '{tmp}' (format parquet, compression zstd)"""
            )
            os.replace(tmp, out / f"year={year}.parquet")
        con.close()
    return {
        "daily_rows": daily_rows,
        "claimed_rows": claimed,
        "panel_rows": panel_rows,
        "years": [years[0], years[-1]] if years else [],
    }
