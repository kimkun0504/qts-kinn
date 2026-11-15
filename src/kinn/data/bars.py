"""Convert Massive flat files to Parquet. Depends only on the raw files, so it is built once.

Layout under ``KINN_DATA_DIR/bars/<bars_id>/``::

    minute/year=YYYY/YYYY-MM-DD.parquet   one file per session, sorted by symbol then time
    daily/year=YYYY.parquet               one file per year
    calendar/year=YYYY.parquet            one row per session: open/close minute, early closes

Prices and volumes are the vendor's, unadjusted. ``bar_start`` is the bar's first instant in UTC;
``minute_et`` is minutes after midnight in New York (570 = 09:30). A bar covers its whole minute,
so its values are known only at ``bar_start`` + 1 minute.
"""

from __future__ import annotations

import os
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from pathlib import Path

import duckdb

from kinn.data.raw import RawFile, fingerprint, massive_files

BARS_SCHEMA_VERSION = "bars-1"
RTH_OPEN, RTH_CLOSE, EARLY_CLOSE = 570, 960, 780  # 09:30, 16:00, 13:00 New York


def bars_id(raw_dir: Path) -> str:
    entries = [
        (f"{kind}/{f.path.name}", f.size)
        for kind in ("day", "minute")
        for f in massive_files(raw_dir, kind)
    ]
    return fingerprint(entries, BARS_SCHEMA_VERSION)


def _connect(threads: int = 1) -> duckdb.DuckDBPyConnection:
    con = duckdb.connect()
    con.execute(f"set threads={threads}; set memory_limit='1500MB'; set timezone='UTC'")
    return con


def _write(con: duckdb.DuckDBPyConnection, select: str, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    tmp = dst.with_suffix(".tmp")
    con.execute(
        f"copy ({select}) to '{tmp}' (format parquet, compression zstd, row_group_size 100000)"
    )
    os.replace(tmp, dst)


def minute_path(root: Path, day: date) -> Path:
    return root / "minute" / f"year={day.year}" / f"{day.isoformat()}.parquet"


def convert_minute(raw: RawFile, root: Path) -> None:
    select = f"""
        select ticker as symbol,
               to_timestamp(window_start / 1000000000)::timestamp as bar_start,
               (date_part('hour', timezone('America/New_York', to_timestamp(window_start / 1e9)))
                * 60 + date_part('minute',
                timezone('America/New_York', to_timestamp(window_start / 1e9))))::smallint
                 as minute_et,
               open, high, low, close, volume, transactions::integer as transactions
        from read_csv('{raw.path}', header = true, columns = {{'ticker': 'varchar',
             'volume': 'bigint', 'open': 'double', 'close': 'double', 'high': 'double',
             'low': 'double', 'window_start': 'bigint', 'transactions': 'bigint'}})
        where ticker is not null
        order by symbol, bar_start"""
    _write(_connect(), select, minute_path(root, raw.day))


def convert_daily_year(files: list[RawFile], root: Path, year: int) -> None:
    paths = [str(f.path) for f in files if f.day.year == year]
    select = f"""
        select strptime(filename[-17:-8], '%Y-%m-%d')::date as date, ticker as symbol,
               open, high, low, close, volume, transactions::integer as transactions
        from read_csv({paths}, header = true, filename = true, columns = {{'ticker': 'varchar',
             'volume': 'bigint', 'open': 'double', 'close': 'double', 'high': 'double',
             'low': 'double', 'window_start': 'bigint', 'transactions': 'bigint'}})
        where ticker is not null
        order by date, symbol"""
    _write(_connect(4), select, root / "daily" / f"year={year}.parquet")


def build_calendar_year(root: Path, year: int) -> None:
    """One row per session, from the minute bars. An early close is detected from volume."""
    files = str(root / "minute" / f"year={year}" / "*.parquet")
    select = f"""
        with m as (
            select strptime(filename[-18:-9], '%Y-%m-%d')::date as date, *
            from read_parquet('{files}', filename = true))
        select date,
               count(*) as bars, count(distinct symbol) as symbols,
               min(minute_et) as first_minute_et, max(minute_et) as last_minute_et,
               {RTH_OPEN}::smallint as open_minute_et,
               case when coalesce(sum(volume) filter (minute_et >= {EARLY_CLOSE + 10}
                                                      and minute_et < {RTH_CLOSE}), 0)
                         < 0.1 * sum(volume) filter (minute_et >= {RTH_OPEN}
                                                     and minute_et < {EARLY_CLOSE})
                    then {EARLY_CLOSE} else {RTH_CLOSE} end::smallint as close_minute_et,
               sum(volume) filter (minute_et < {RTH_OPEN}) as premarket_volume,
               sum(volume) filter (minute_et >= {RTH_OPEN} and minute_et < {RTH_CLOSE})
                 as regular_volume,
               sum(volume) filter (minute_et >= {RTH_CLOSE}) as postmarket_volume
        from m group by date order by date"""
    _write(_connect(4), select, root / "calendar" / f"year={year}.parquet")


def pending_steps(raw_dir: Path, root: Path) -> list[tuple[str, object]]:
    """Steps still to do, as (label, zero-argument function). Finished files are skipped."""
    steps: list[tuple[str, object]] = []
    daily = massive_files(raw_dir, "day")
    minute = massive_files(raw_dir, "minute")
    for year in sorted({f.day.year for f in daily}):
        if not (root / "daily" / f"year={year}.parquet").exists():
            steps.append((f"daily {year}", lambda y=year: convert_daily_year(daily, root, y)))
    todo = [f for f in minute if not minute_path(root, f.day).exists()]
    for raw in todo:
        steps.append((f"minute {raw.day}", lambda r=raw: convert_minute(r, root)))
    unfinished_years = {f.day.year for f in todo}
    for year in sorted({f.day.year for f in minute}):
        if year in unfinished_years:
            continue
        if not (root / "calendar" / f"year={year}.parquet").exists():
            steps.append((f"calendar {year}", lambda y=year: build_calendar_year(root, y)))
    return steps


def run_steps(steps: list[tuple[str, object]], *, budget_seconds: float, workers: int = 4) -> int:
    """Run steps until the time budget is used. Returns how many finished."""
    deadline = time.monotonic() + budget_seconds
    done = 0

    def guarded(step: tuple[str, object]) -> bool:
        if time.monotonic() > deadline:
            return False
        step[1]()
        return True

    with ThreadPoolExecutor(max_workers=workers) as pool:
        for finished in pool.map(guarded, steps):
            done += int(finished)
    return done
