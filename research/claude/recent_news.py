"""Family 11 of the search (strategies/recent_search/HYPOTHESIS.md, addendum of 2026-11-16
12:05 ET): GlobeNewswire releases with a publication time, joined to prices.

    uv run python research/claude/recent_news.py events            # the event table
    uv run python research/claude/recent_news.py bars --budget 120 # prices around intraday news
    uv run python research/claude/recent_news.py measure           # 2021-2022 only
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import duckdb

from kinn.core.settings import load_settings
from kinn.data.store import DataStore

GROUPS = [
    ("law firm", r"class action|investigat|shareholder alert|law offices|lawsuit|deadline|"
                 r"rosen|pomerantz|levi & korsinsky|bragar|faruqi|securities fraud|investors? (who|with)"),
    ("offering", r"offering|registered direct|private placement|at-the-market|warrant|convertible"
                 r"|pricing of|financing"),
    ("results", r"results|earnings|quarter|fiscal|guidance|outlook|preliminary revenue"),
    ("trial", r"fda|phase [1-3i]|clinical|trial|topline|top-line|approval|clearance|patients|"
              r"data (from|presented)|study"),
    ("merger", r"acquire|acquisition|merger|to be acquired|tender offer|definitive agreement|"
               r"strategic alternatives"),
    ("contract", r"contract|award|agreement|partnership|collaborat|order|selected by"),
    ("buyback", r"repurchase|buyback|dividend"),
]  # fmt: skip
CAP = """case when mcap is null then 'cap?' when mcap < 3e8 then 'micro'
              when mcap < 2e9 then 'small' else 'large' end"""


def group_sql() -> str:
    cases = " ".join(
        f"when regexp_matches(lower(title), '{rx}') then '{name}'" for name, rx in GROUPS
    )
    return f"case {cases} else 'other' end"


def paths():
    settings = load_settings()
    return settings, settings.data_dir / "research" / "recent"


def events() -> None:
    settings, base = paths()
    con = duckdb.connect()
    con.execute("set threads=3; set memory_limit='2500MB'")
    con.execute(
        f"""create table sessions as
            select day, row_number() over (order by day) as k
            from (select distinct day from read_parquet('{base}/base_*.parquet'))"""
    )
    con.execute(
        f"""copy (
            with a as (
                select id, title, unnest(tickers) as symbol, len(tickers) as names,
                       published at time zone 'America/New_York' as et, {group_sql()} as grp
                from '{base}/articles.parquet'
                where publisher = 'GlobeNewswire Inc.' and len(tickers) <= 2),
            t as (
                select *, cast(et as date) as d, hour(et) * 60 + minute(et) as m,
                       lag(et) over (partition by symbol order by et) as previous
                from a),
            placed as (
                select t.*, s.day as same_day,
                       (select min(day) from sessions n where n.day > t.d) as next_day
                from t left join sessions s on s.day = t.d)
            select id, title, symbol, names, et, m, grp,
                   coalesce(date_diff('day', previous, et), 999) as quiet_days,
                   case when same_day is not null and m < 960 then same_day else next_day end
                     as day,
                   case when same_day is not null and m >= 570 and m < 960 then 'session'
                        when same_day is not null and m >= 240 and m < 570 then 'premarket'
                        else 'overnight' end as timing
            from placed) to '{base}/news_events.parquet' (format parquet)"""
    )
    e = f"'{base}/news_events.parquet'"
    print(
        con.execute(
            f"select year(day), timing, count(*) from {e} group by 1, 2 order by 1, 2"
        ).fetchall()
    )
    print(con.execute(f"select grp, count(*) from {e} group by 1 order by 2 desc").fetchall())
    si = settings.raw_dir / "massive" / "short_interest"
    con.execute(
        f"""copy (select ticker as symbol, cast(settlement_date as date) + 14 as known,
                         short_interest, days_to_cover
                  from read_json('{si}/*.jsonl.gz', format='newline_delimited')
                  order by 1, 2) to '{base}/short_interest.parquet' (format parquet)"""
    )
    print(
        con.execute(
            f"select count(*), min(known)::varchar, max(known)::varchar from '{base}/short_interest.parquet'"
        ).fetchall()
    )


def bars(budget: float) -> None:
    """Prices around releases made during the session: the last print before, the first print
    1 and 5 minutes after, and prints 15 and 60 minutes after each entry."""
    settings, base = paths()
    store = DataStore(settings)
    out = base / "news_bars"
    out.mkdir(exist_ok=True)
    con = duckdb.connect()
    con.execute("set threads=3; set memory_limit='2200MB'")
    e = f"'{base}/news_events.parquet'"
    months = [r[0] for r in con.execute(
        f"select distinct strftime(day, '%Y-%m') from {e} where timing = 'session' order by 1"
    ).fetchall()]  # fmt: skip
    deadline = time.time() + budget
    for month in months:
        target = out / f"{month}.parquet"
        if target.exists():
            continue
        if time.time() > deadline:
            print("out of time; run again")
            return
        days = [r[0] for r in con.execute(
            f"select distinct day from {e} where timing = 'session' and strftime(day, '%Y-%m') = '{month}'"
        ).fetchall()]  # fmt: skip
        files = ", ".join(
            f"'{store.bars_root}/minute/year={d.year}/{d.isoformat()}.parquet'" for d in days
        )
        offsets = {"e1": 1, "e5": 5, "a16": 16, "a61": 61, "b20": 20, "b65": 65}
        cols = ", ".join(
            f"arg_min(b.open, b.minute_et) filter (b.minute_et >= v.m + {k}) as {name}, "
            f"min(b.minute_et) filter (b.minute_et >= v.m + {k}) as {name}_m"
            for name, k in offsets.items()
        )
        tmp = out / f"{month}.tmp"
        con.execute(
            f"""copy (
                select v.id, v.symbol, v.day,
                       arg_max(b.close, b.minute_et) filter (b.minute_et < v.m) as before,
                       {cols}
                from (select * from {e} where timing = 'session'
                        and strftime(day, '%Y-%m') = '{month}') v
                join read_parquet([{files}]) b
                  on cast(b.bar_start as date) = v.day and b.symbol = v.symbol
                 and b.minute_et between 570 and 959
                group by 1, 2, 3) to '{tmp}' (format parquet)"""
        )
        tmp.replace(target)
    print("bars: all months done")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("what", choices=("events", "bars", "measure"))
    parser.add_argument("--budget", type=float, default=120.0)
    a = parser.parse_args()
    if a.what == "events":
        events()
    elif a.what == "bars":
        bars(a.budget)
    sys.stdout.flush()
