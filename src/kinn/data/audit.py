"""Audit a data build: coverage, identity matching, price agreement, calendar, sessions.

Everything here reads processed data (already cut at the seal) through DuckDB and returns plain
numbers. ``render`` turns them into the Markdown report.
"""

from __future__ import annotations

import json
from pathlib import Path

import duckdb

from kinn.core.settings import Settings
from kinn.data import raw
from kinn.data.store import DataStore
from kinn.data.universe import COMMON_STOCK


def _rows(con: duckdb.DuckDBPyConnection, sql: str) -> list[dict]:
    result = con.execute(sql)
    names = [d[0] for d in result.description]
    return [dict(zip(names, row, strict=True)) for row in result.fetchall()]


def run(settings: Settings) -> dict:
    store = DataStore(settings)
    root, bars_root = store.root, store.bars_root
    con = duckdb.connect()
    con.execute("set memory_limit='1500MB'")
    con.execute(f"create view panel as select * from read_parquet('{root}/panel/*.parquet')")
    con.execute(f"create view daily as select * from read_parquet('{bars_root}/daily/*.parquet')")
    con.execute(f"create view sec as select * from '{root}/master/security_master.parquet'")
    con.execute(f"create view hist as select * from '{root}/master/symbol_history.parquet'")
    con.execute(
        f"""create view sep as select s.permaticker, s.category, e.date, e.closeunadj
            from '{root}/sharadar/sep.parquet' e join sec s using (ticker)"""
    )
    common = ", ".join(f"'{c}'" for c in COMMON_STOCK)
    out: dict = {"build": store.info}

    minute_raw = raw.massive_files(settings.raw_dir, "minute")
    converted = len(list((bars_root / "minute").glob("*/*.parquet")))
    out["files"] = {
        "raw_daily_files": len(raw.massive_files(settings.raw_dir, "day")),
        "raw_minute_files": len(minute_raw),
        "minute_files_converted": converted,
        "first_session": str(minute_raw[0].day),
        "last_session": str(minute_raw[-1].day),
    }
    out["tables"] = _rows(
        con,
        f"""select 'security_master' as name, count(*) as rows from sec
            union all select 'symbol_history', count(*) from hist
            union all select 'splits', count(*) from '{root}/master/splits.parquet'
            union all select 'sharadar events', count(*) from '{root}/sharadar/events.parquet'
            union all select 'sharadar market cap', count(*) from '{root}/sharadar/daily.parquet'
            union all select 'daily bars', count(*) from daily
            union all select 'panel', count(*) from panel""",
    )
    out["security_master"] = _rows(
        con,
        """select category, count(*) as companies, sum(delisted::int) as delisted_before_seal
           from sec group by 1 order by 2 desc""",
    )
    out["symbol_conflicts"] = _rows(
        con,
        """select count(*) as overlapping_pairs from hist a join hist b
             on a.symbol = b.symbol and a.permaticker < b.permaticker
            and a.valid_from < b.valid_to and b.valid_from < a.valid_to""",
    )[0]

    # Identity gate: of Sharadar's common-stock company-days, how many found a Massive bar,
    # and how often do the two vendors' unadjusted closes agree?
    out["match_by_year"] = _rows(
        con,
        f"""select year(e.date) as year, count(*) as sharadar_days,
                   round(100.0 * count(p.permaticker) / count(*), 2) as matched_pct,
                   round(100.0 * count(*) filter (abs(p.close / e.closeunadj - 1) <= 0.01)
                         / nullif(count(p.permaticker), 0), 2) as close_within_1pct
            from sep e left join panel p using (permaticker, date)
            where e.category in ({common}) and e.date >= DATE '{out["files"]["first_session"]}'
              and e.closeunadj > 0
            group by 1 order by 1""",
    )
    out["panel_by_year"] = _rows(
        con,
        f"""select year(date) as year, count(distinct date) as sessions,
                   round(count(*) / count(distinct date)) as companies_per_day,
                   round(count(*) filter (category in ({common})) / count(distinct date))
                     as common_per_day,
                   round(100.0 * count(*) filter (marketcap_prev is null and sessions_prior > 0
                         and category in ({common}))
                         / count(*) filter (sessions_prior > 0 and category in ({common})), 2)
                     as common_without_marketcap_pct
            from panel group by 1 order by 1""",
    )
    out["unmatched_symbols"] = _rows(
        con,
        """with u as (select d.symbol, d.date from daily d anti join panel p using (date, symbol))
           select case when symbol like '%p%' then 'preferred (p)'
                       when symbol like '%.WS%' or symbol like '%w' then 'warrant'
                       when symbol like '%.%' then 'other dotted (class, unit, right)'
                       when regexp_matches(symbol, '[a-z]') then 'other lower-case suffix'
                       else 'plain symbol (ETF, fund, or unmatched stock)' end as shape,
                  count(*) as rows, count(distinct symbol) as symbols
           from u group by 1 order by 2 desc""",
    )
    # Splits: a big overnight gap with no split on record suggests a missed adjustment.
    out["overnight_gaps"] = _rows(
        con,
        f"""select split_ratio <> 1 as split_on_record, count(*) as rows,
                   count(*) filter (abs(open / prev_close - 1) > 0.4) as gap_over_40pct
            from panel where prev_close > 0 and open > 0 and category in ({common})
            group by 1 order by 1""",
    )
    out["split_check"] = _rows(
        con,
        """select symbol, date, split_ratio, round(prev_close, 2) as prev_close_adjusted,
                  open from panel
           where (symbol, date) in (('AAPL', DATE '2020-08-31'), ('TSLA', DATE '2022-08-25'),
                                    ('AAPL', DATE '2014-06-09'), ('GOOGL', DATE '2022-07-18'))
           order by date""",
    )

    calendars = list((bars_root / "calendar").glob("*.parquet"))
    out["calendar_years_built"] = len(calendars)
    if calendars:
        con.execute(
            f"create view cal as select * from read_parquet('{bars_root}/calendar/*.parquet')"
        )
        out["sessions_by_year"] = _rows(
            con,
            """select year(date) as year, count(*) as sessions,
                      count(*) filter (close_minute_et = 780) as early_closes,
                      round(avg(bars)) as bars_per_day, round(avg(symbols)) as symbols_per_day,
                      min(first_minute_et) as earliest_minute_et,
                      max(last_minute_et) as latest_minute_et,
                      round(100.0 * sum(premarket_volume) / sum(regular_volume), 2)
                        as premarket_pct_of_regular,
                      round(100.0 * sum(postmarket_volume) / sum(regular_volume), 2)
                        as postmarket_pct_of_regular
               from cal group by 1 order by 1""",
        )
        out["early_closes"] = [
            str(r["date"])
            for r in _rows(con, "select date from cal where close_minute_et = 780 order by 1")
        ]
        out["calendar_vs_sharadar"] = _rows(
            con,
            """with s as (select date, count(*) as n from sep group by 1 having count(*) > 1000)
               select (select count(*) from cal) as massive_sessions,
                      (select count(*) from s join cal using (date)) as in_both,
                      (select count(*) from cal anti join s using (date)) as massive_only,
                      (select count(*) from s anti join cal using (date)
                        where s.date between (select min(date) from cal)
                                         and (select max(date) from cal)) as sharadar_only""",
        )[0]
    con.close()
    return json.loads(json.dumps(out, default=str))


def _table(rows: list[dict]) -> str:
    if not rows:
        return "*(no rows)*\n"
    heads = list(rows[0])
    lines = ["| " + " | ".join(heads) + " |", "|" + "---|" * len(heads)]
    for row in rows:
        lines.append("| " + " | ".join("" if row[h] is None else str(row[h]) for h in heads) + " |")
    return "\n".join(lines) + "\n"


def render(a: dict) -> str:
    b, f = a["build"], a["files"]
    parts = [
        f"# Data audit: build `{b['build_id']}`\n",
        f"Generated by `kinn data audit`. Bars `{b['bars_id']}`, Sharadar snapshot "
        f"{b['sharadar_snapshot']}, holdout from {b['holdout_start']} (nothing on or after it "
        "was read, except the ticker-change events of decision 0009).\n",
        "## Files\n",
        f"- Raw Massive files before the seal: {f['raw_daily_files']} daily, "
        f"{f['raw_minute_files']} minute, {f['first_session']} to {f['last_session']}.",
        f"- Minute files converted to Parquet: {f['minute_files_converted']} of "
        f"{f['raw_minute_files']}.\n",
        "## Tables\n",
        _table(a["tables"]),
        "## Security master\n",
        _table(a["security_master"]),
        f"Symbol intervals claimed by two companies at once: "
        f"{a['symbol_conflicts']['overlapping_pairs']} pairs (such bars are dropped).\n",
        "## Identity match: Sharadar common-stock days found in Massive, and close agreement\n",
        _table(a["match_by_year"]),
        "## Panel by year\n",
        _table(a["panel_by_year"]),
        "## Massive daily rows not attached to a company\n",
        _table(a["unmatched_symbols"]),
        "## Overnight gaps over 40% (common stock), with and without a split on record\n",
        _table(a["overnight_gaps"]),
        "Known splits, prior close adjusted to the new share basis:\n",
        _table(a["split_check"]),
    ]
    if a.get("sessions_by_year"):
        parts += [
            f"## Sessions and hours ({a['calendar_years_built']} years of minute bars built)\n",
            _table(a["sessions_by_year"]),
            "Early closes detected (13:00 New York): " + ", ".join(a["early_closes"]) + "\n",
            "Massive sessions against Sharadar trading dates:\n",
            _table([a["calendar_vs_sharadar"]]),
        ]
    else:
        parts.append("## Sessions and hours\n\nMinute bars are not converted yet.\n")
    return "\n".join(parts)


def write(settings: Settings) -> Path:
    result = run(settings)
    root = DataStore(settings).root
    (root / "audit.json").write_text(json.dumps(result, indent=2) + "\n")
    path = root / "audit.md"
    path.write_text(render(result))
    return path
