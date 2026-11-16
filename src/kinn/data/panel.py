"""The daily panel: one row per company per session, with what was known before that session.

Columns ending in ``_prev`` (and ``sessions_prior``) use only earlier sessions, so they are
available before the open of ``date``. ``filings_prev`` counts 8-K filings dated from the prior
session up to, not including, ``date``. ``filings_today`` is an outcome (a filing later today is
not knowable during the session). Universes may filter on those and on static labels only.
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
TREND_WINDOW = 60  # sessions of the price return that ends at the previous close
SPLIT_VISIBLE = 0.18  # |ln ratio|: splits this large can be checked against the price
SPLIT_WINDOW = 20  # calendar days either side of the listed date
SPLIT_TOLERANCE = 0.12  # allowed |ln| gap between the price change and the ratio ...
SPLIT_TOLERANCE_SHARE = 0.35  # ... or this share of |ln ratio|, whichever is larger

_FITS = f"miss <= greatest({SPLIT_TOLERANCE}, {SPLIT_TOLERANCE_SHARE} * abs(ln(ratio)))"


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
        con.execute(f"create view listed_splits as select * from '{master}/splits.parquet'")
        con.execute(
            f"""create view filings as
                select s.permaticker, e.date from '{shar}/events.parquet' e
                join sec s using (ticker)"""
        )
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
        split_stats = _align_splits(con, master)
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
                        from bars window w as (partition by permaticker order by date)),
                    returned as (
                        select l.*, coalesce(sp.ratio, 1) as ratio,
                               case when l.prev_close_raw > 0 and l.close > 0
                                    then ln(l.close * coalesce(sp.ratio, 1) / l.prev_close_raw)
                               end as log_return
                        from lagged l
                        left join splits sp
                          on sp.permaticker = l.permaticker and sp.date = l.date),
                    trended as (
                        select *, sum(log_return) over t as trend, count(log_return) over t
                                 as trend_days
                        from returned window t as (
                            partition by permaticker order by date
                            rows between {TREND_WINDOW} preceding and 1 preceding)),
                    filed as (
                        select l.permaticker, l.date,
                               count(*) filter (f.date < l.date) as filings_prev,
                               count(*) filter (f.date = l.date) as filings_today
                        from trended l join filings f
                          on f.permaticker = l.permaticker and f.date >= l.prev_date
                         and f.date <= l.date
                        group by 1, 2)
                    select l.date, l.permaticker, l.symbol, s.ticker, s.category, s.exchange,
                           l.open, l.high, l.low, l.close, l.volume, l.dollar_volume,
                           l.prev_close_raw / l.ratio as prev_close,
                           l.prev_date, l.ratio as split_ratio,
                           l.adv20_prev, l.sessions_prior, mc.marketcap as marketcap_prev,
                           coalesce(fd.filings_prev, 0)::integer as filings_prev,
                           coalesce(fd.filings_today, 0)::integer as filings_today,
                           case when l.trend_days = {TREND_WINDOW} then exp(l.trend) - 1 end
                             as ret60_prev
                    from trended l
                    left join filed fd on fd.permaticker = l.permaticker and fd.date = l.date
                    join sec s on s.permaticker = l.permaticker
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
        "splits": split_stats,
    }


def _align_splits(con: duckdb.DuckDBPyConnection, master: Path) -> dict:
    """Create table ``splits``: each listed split on the session the price actually changed.

    Sharadar sometimes dates a split by its record or pay date, days away from the session the
    price changed. Left alone, that puts a false jump on one day and a false crash on another.
    For splits large enough to see (18% or more), the effective session is the
    one within 20 days whose close-to-close change best matches the ratio (counting any cash or
    spun-off shares paid that day, since breakups often come with a reverse split). A large
    split with no matching change is dropped (and counted): the prices show no split. Smaller
    ones cannot be checked against daily noise and keep their listed date.
    """
    con.execute(
        f"""create table near as
            select s.permaticker, s.date as listed, s.ratio, i.date, d.close,
                   coalesce(v.amount, 0) as paid
            from listed_splits s
            join ident i on i.permaticker = s.permaticker
             and i.date between s.date - {SPLIT_WINDOW + 7} and s.date + {SPLIT_WINDOW}
            join daily d on d.date = i.date and d.symbol = i.symbol
            left join '{master}/dividends.parquet' v
              on v.permaticker = i.permaticker and v.date = i.date
            where abs(ln(s.ratio)) >= {SPLIT_VISIBLE}"""
    )
    con.execute(
        f"""create table matched as
            with moves as (
                select *, abs(ln((close + paid) / lag(close) over (
                    partition by permaticker, listed order by date) * ratio)) as miss
                from near)
            select permaticker, listed, ratio, arg_min(date, miss) as date, min(miss) as miss
            from moves
            where miss is not null
              and date between listed - {SPLIT_WINDOW} and listed + {SPLIT_WINDOW}
            group by 1, 2, 3"""
    )
    con.execute(
        f"""create table splits as
            select permaticker, date, exp(sum(ln(ratio))) as ratio from (
                select permaticker, date, ratio from listed_splits
                where abs(ln(ratio)) < {SPLIT_VISIBLE}
                union all
                select permaticker, date, ratio from matched where {_FITS})
            group by 1, 2"""
    )
    tmp = master / "splits_effective.tmp"
    con.execute(f"copy (select * from splits order by 1, 2) to '{tmp}' (format parquet)")
    os.replace(tmp, master / "splits_effective.parquet")
    listed, small, moved, dropped, unseen = con.execute(
        f"""select (select count(*) from listed_splits),
                   (select count(*) from listed_splits where abs(ln(ratio)) < {SPLIT_VISIBLE}),
                   (select count(*) from matched where {_FITS} and date <> listed),
                   (select count(*) from matched where not ({_FITS})),
                   (select count(*) from listed_splits s where abs(ln(s.ratio)) >= {SPLIT_VISIBLE}
                      and not exists (select 1 from matched m
                                      where m.permaticker = s.permaticker and m.listed = s.date))"""
    ).fetchone()
    con.execute("drop table near")
    return {"listed": listed, "too_small_to_check": small, "date_moved": moved,
            "dropped_no_price_change": dropped, "no_bars_nearby": unseen}  # fmt: skip
