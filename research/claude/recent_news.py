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


def cut(column: str, edges: list[float]) -> str:
    parts = [
        f"when {column} is null then null",
        f"when {column} < {edges[0]} then '<{edges[0] * 100:g}'",
    ]
    for a, b in zip(edges, edges[1:], strict=False):
        parts.append(f"when {column} < {b} then '{a * 100:g}..{b * 100:g}'")
    return "case " + " ".join(parts) + f" else '>={edges[-1] * 100:g}' end"


def grid(con, source: str, keys: dict[str, str], ret: str, cost: str, title: str) -> int:
    """Every cell of `keys` over `source` (search years only): trades, gross, net at 2x, t on
    daily means, the short side for information, and 2021 and 2022 apart."""
    names = list(keys)
    exprs = ", ".join(f"{expr} as {name}" for name, expr in keys.items())
    group = ", ".join(names)
    rows = con.execute(
        f"""with x as (select {exprs}, day, yr, ({ret}) as r, ({cost}) as cost
                       from {source} where yr <= 2022),
            d as (select {group}, day, any_value(yr) as yr, count(*) as n, avg(r - cost) as net,
                         avg(r) as gross, avg(-r - cost) as short
                  from x where r is not null group by {group}, day)
            select {group}, sum(n), sum(gross * n) / sum(n), sum(net * n) / sum(n),
                   avg(net) / nullif(stddev_samp(net) / sqrt(count(*)), 0),
                   sum(short * n) / sum(n),
                   sum(net * n) filter (yr = 2021) / nullif(sum(n) filter (yr = 2021), 0),
                   sum(net * n) filter (yr = 2022) / nullif(sum(n) filter (yr = 2022), 0)
            from d group by {group}"""
    ).fetchall()
    k = len(names)
    rows = [r for r in rows if all(v is not None for v in r[:k])]
    big = [r for r in rows if r[k] >= 150]

    def both(r) -> bool:
        return all(v is not None and v > 0 for v in r[k + 5 :])

    good = [r for r in big if r[k + 2] >= 0.03 and (r[k + 3] or 0) >= 4 and both(r)]
    near = [r for r in big if 0.015 <= r[k + 2] < 0.03 and (r[k + 3] or 0) >= 4 and both(r)]
    print(f"\n=== {title}: {len(rows)} cells, {len(big)} with 150+ trades; "
          f"shortlisted {len(good)}, near misses {len(near)}")  # fmt: skip
    head = "".join(f"{n:>10}" for n in names)
    print(f"{head}{'trades':>8}{'gross%':>8}{'net%':>8}{'t':>6}{'short%':>8}{'2021':>7}{'2022':>7}")

    def line(r, mark: str = "") -> None:
        label = "".join(f"{str(v):>10}" for v in r[:k])
        n, gross, net, t, short, y1, y2 = r[k:]
        print(f"{label}{n:>8.0f}{100 * gross:>8.2f}{100 * net:>8.2f}{t or 0:>6.1f}"
              f"{100 * short:>8.2f}{100 * (y1 or 0):>7.1f}{100 * (y2 or 0):>7.1f} {mark}")  # fmt: skip

    for r in good:
        line(r, "<- SHORTLIST")
    for r in near:
        line(r, "<- near")
    for r in sorted(big, key=lambda r: -r[k + 2])[:6]:
        line(r)
    print("  best short cells (information)")
    for r in sorted(big, key=lambda r: -r[k + 4])[:4]:
        line(r)
    return len(rows)


def measure() -> None:
    _, base = paths()
    con = duckdb.connect()
    con.execute("set threads=3; set memory_limit='2500MB'")
    con.execute(f"create view b as select * from read_parquet('{base}/base_*.parquet')")
    con.execute(
        f"""create view early as
            select b.*, v.grp, v.m, v.timing, v.quiet_days, {CAP} as cap
            from (select day, symbol, arg_min(grp, et) as grp, min(m) as m,
                         arg_min(timing, et) as timing, max(quiet_days) as quiet_days
                  from '{base}/news_events.parquet'
                  where timing <> 'session' group by 1, 2) v
            join b using (day, symbol)"""
    )
    total = grid(
        con, "(select * from early where ok575)",
        {"news": "grp", "gap": cut("gap", [-0.10, -0.03, 0.03, 0.10]), "cap": "cap"},
        "r575", "2 * (2 * half_spread + commission)",
        "11a released before the open: buy 09:35, sell at the close")  # fmt: skip
    con.execute(
        f"""create view pre as
            select e.*, case when timing = 'overnight' or m <= 420 then 420
                             when m <= 480 then 480 when m <= 540 then 540 end as t,
                   p.* exclude (day, symbol)
            from early e join read_parquet('{base}/premarket/*.parquet') p using (day, symbol)"""
    )
    entry = "case t when 420 then e420 when 480 then e480 else e540 end"
    entered = "case t when 420 then em420 when 480 then em480 else em540 end"
    seen = "case t when 420 then c420 when 480 then c480 else c540 end"
    source = (f"(select *, ({entry}) as e, ({seen}) / prev_close - 1 as sofar from pre "
              f"where t is not null and ({entered}) <= t + 15 and ({entered}) < 570)")  # fmt: skip
    for name, price in (("the open", "open_px"),
                        ("10:00", "case when ok600 then official_close / (1 + r600) end"),
                        ("the close", "official_close")):  # fmt: skip
        total += grid(
            con,
            source,
            {"news": "grp", "sofar": cut("sofar", [-0.10, -0.03, 0.03, 0.10, 0.30])},
            f"({price}) / e - 1",
            "6 * half_spread + 2 * commission",
            f"11a bought at the premarket checkpoint after the release, sold at {name}",
        )
    con.execute(
        f"""create view live as
            select b.*, v.grp, v.m, {CAP} as cap, n.* exclude (id, symbol, day)
            from (select * from '{base}/news_events.parquet'
                  where timing = 'session' and m between 575 and 900) v
            join read_parquet('{base}/news_bars/*.parquet') n using (id, symbol, day)
            join b using (day, symbol)"""
    )
    for delay, e, m_e, exits in (
        (1, "e1", "e1_m", {"15 min": "a16", "60 min": "a61", "close": "official_close"}),
        (5, "e5", "e5_m", {"15 min": "b20", "60 min": "b65", "close": "official_close"}),
    ):
        for name, price in exits.items():
            total += grid(
                con,
                f"(select * from live where {m_e} <= m + {delay + 5} and before > 0)",
                {"news": "grp", "reaction": cut(f"{e} / before - 1", [-0.05, -0.01, 0.01, 0.05])},
                f"{price} / {e} - 1",
                "4 * half_spread + 2 * commission",
                f"11b released in the session: buy {delay} min after, sell {name}",
            )
    print(f"\ncells measured: {total}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("what", choices=("events", "bars", "measure"))
    parser.add_argument("--budget", type=float, default=120.0)
    a = parser.parse_args()
    if a.what == "events":
        events()
    elif a.what == "bars":
        bars(a.budget)
    else:
        measure()
    sys.stdout.flush()
