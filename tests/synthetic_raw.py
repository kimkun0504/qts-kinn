"""A tiny, fully synthetic raw-data folder in the vendors' formats, for tests.

It contains every trap the data layer must handle: a rename before the seal, a rename after
it, a reused symbol, a split, a delisting, a listing after the seal, and holdout-dated files
and rows carrying a POISON marker that must never reach processed data.
"""

from __future__ import annotations

import csv
import gzip
import io
import zipfile
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

NEW_YORK = ZoneInfo("America/New_York")
FIRST, LAST_OPEN = date(2023, 9, 25), date(2023, 11, 8)
HOLDOUT_DAYS = [date(2023, 11, 9), date(2023, 11, 10)]
EARLY_CLOSE_DAY = date(2023, 10, 27)
RENAME_DAY, SPLIT_DAY = date(2023, 10, 16), date(2023, 10, 23)
DEAD_LAST, REUSE_FIRST = date(2023, 10, 20), date(2023, 10, 30)
DIVIDEND_DAY = date(2023, 10, 18)
# LATE's split is listed two sessions before its price changes; GONE's never shows in prices.
LATE_SPLIT_LISTED, LATE_SPLIT_REAL, PHANTOM_SPLIT = (
    date(2023, 10, 24),
    date(2023, 10, 26),
    date(2023, 10, 11),
)


SF1_HEADER = ["ticker", "dimension", "calendardate", "datekey", "reportperiod", "equityusd",
              "revenueusd", "gp", "opinc", "ebitusd", "netinccmnusd", "assets", "liabilities",
              "debtusd", "cashnequsd", "ncfo", "capex", "fcf", "sharesbas", "shareswa", "epsusd",
              "bvps", "dps"]  # fmt: skip
FILING_DAY = date(2023, 10, 16)


def sf1_row(ticker, dimension, period, filed, equity):
    return [ticker, dimension, period, filed, period, equity] + [1.0] * (len(SF1_HEADER) - 6)


def sessions(last: date = LAST_OPEN) -> list[date]:
    days, day = [], FIRST
    while day <= last:
        if day.weekday() < 5:
            days.append(day)
        day += timedelta(days=1)
    return days


def daily_rows(day: date, index: int) -> list[tuple[str, int, float]]:
    """(symbol, volume, price) for one session."""
    rows = [
        ("AAA", 1000 + 10 * index, 10.0),
        ("PRE", 500, 30.0),
        ("GONE", 800, 7.0),
        ("SPY", 9000, 400.0),
    ]
    rows.append(("OLD" if day < RENAME_DAY else "NEW", 700, 20.0))
    if day <= DEAD_LAST:
        rows.append(("DEAD", 300, 2.0))
    if day >= REUSE_FIRST:
        rows.append(("DEAD", 400, 50.0))
    rows.append(("SPLT", 600, 40.0) if day < SPLIT_DAY else ("SPLT", 1200, 20.0))
    rows.append(("LATE", 600, 60.0) if day < LATE_SPLIT_REAL else ("LATE", 1200, 30.0))
    return rows


def _ns(day: date, minute_et: int) -> int:
    local = datetime(day.year, day.month, day.day, tzinfo=NEW_YORK) + timedelta(minutes=minute_et)
    return int(local.timestamp()) * 1_000_000_000


def _gz(path: Path, rows: list[list]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(path, "wt", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            ["ticker", "volume", "open", "close", "high", "low", "window_start", "transactions"]
        )
        writer.writerows(rows)


def _zip(folder: Path, table: str, header: list[str], rows: list[list]) -> None:
    text = io.StringIO()
    writer = csv.writer(text)
    writer.writerow(header)
    writer.writerows(rows)
    with zipfile.ZipFile(folder / f"SHARADAR_{table}_2_abc.zip", "w") as archive:
        archive.writestr(f"SHARADAR_{table}_2_abc.csv", text.getvalue())


def make_raw(root: Path, *, last: date = LAST_OPEN, with_holdout: bool = True) -> Path:
    base = root / "massive" / "us_stocks_sip"
    days = sessions(last)
    all_days = [(d, False) for d in days] + (
        [(d, True) for d in HOLDOUT_DAYS] if with_holdout else []
    )
    for index, (day, holdout) in enumerate(all_days):
        rows = [("POISON", 1, 1.0)] if holdout else daily_rows(day, index)
        name = f"{day.year}/{day.month:02d}/{day.isoformat()}.csv.gz"
        _gz(base / "day_aggs_v1" / name, [[s, v, p, p, p, p, _ns(day, 0), 5] for s, v, p in rows])
        minutes = [480, 570, 571, 700] + ([] if day == EARLY_CLOSE_DAY else [959])
        _gz(
            base / "minute_aggs_v1" / name,
            [[s, v // 5, p, p, p, p, _ns(day, m), 1] for s, v, p in rows for m in minutes],
        )

    snapshot = root / "sharadar" / "2026-11-09"
    snapshot.mkdir(parents=True, exist_ok=True)
    listed, still = "2020-01-02", "2026-11-09"
    tick_header = [
        "table",
        "permaticker",
        "ticker",
        "name",
        "exchange",
        "isdelisted",
        "category",
        "siccode",
        "sector",
        "industry",
        "scalemarketcap",
        "currency",
        "location",
        "lastupdated",
        "firstpricedate",
        "lastpricedate",
    ]

    def tick(perma, ticker, first=listed, last_price=still, delisted="N", table="SEP"):
        return [
            table,
            perma,
            ticker,
            f"{ticker} INC",
            "NYSE",
            delisted,
            "Domestic Common Stock",
            "1000",
            "Tech",
            "Software",
            "6 - Mega",
            "USD",
            "U.S.A",
            still,
            first,
            last_price,
        ]

    _zip(
        snapshot,
        "TICKERS",
        tick_header,
        [
            tick(1001, "AAA"),
            tick(1002, "NEW"),
            tick(1003, "POST"),
            tick(1004, "DEAD1", last_price=DEAD_LAST.isoformat(), delisted="Y"),
            tick(1005, "DEAD", first=REUSE_FIRST.isoformat()),
            tick(1006, "SPLT"),
            tick(1007, "FUT", first="2024-01-05"),
            tick(1008, "GONE", last_price="2025-05-05", delisted="Y"),
            tick(1009, "LATE"),
            tick(1001, "AAA", table="SF1"),
        ],
    )
    act_header = ["date", "action", "ticker", "name", "value", "contraticker", "contraname"]
    _zip(
        snapshot,
        "ACTIONS",
        act_header,
        [
            [RENAME_DAY.isoformat(), "tickerchangefrom", "NEW", "NEW INC", "", "OLD", "N/A"],
            ["2024-03-01", "tickerchangefrom", "POST", "POST INC", "", "PRE", "N/A"],
            [DEAD_LAST.isoformat(), "tickerchangefrom", "DEAD1", "DEAD1 INC", "", "DEAD", "N/A"],
            [SPLIT_DAY.isoformat(), "split", "SPLT", "SPLT INC", "2.0", "", ""],
            # Stated on the snapshot's share basis (half the shares after a later 2-for-1).
            [DIVIDEND_DAY.isoformat(), "dividend", "NEW", "NEW INC", "0.25", "", ""],
            [LATE_SPLIT_LISTED.isoformat(), "split", "LATE", "LATE INC", "2.0", "", ""],
            [PHANTOM_SPLIT.isoformat(), "split", "GONE", "GONE INC", "2.0", "", ""],
            ["2025-01-10", "split", "AAA", "AAA INC", "3.0", "", ""],
            ["2025-05-05", "delisted", "GONE", "GONE INC", "", "", ""],
        ],
    )
    dated = days + (HOLDOUT_DAYS if with_holdout else [])
    _zip(
        snapshot,
        "DAILY",
        ["ticker", "date", "lastupdated", "ev", "marketcap"],
        [
            [t, d.isoformat(), still, 1, cap + i]
            for i, d in enumerate(dated)
            for t, cap in (("AAA", 100.0), ("NEW", 200.0), ("POST", 300.0), ("SPLT", 400.0))
        ],
    )
    _zip(
        snapshot,
        "SEP",
        ["ticker", "date", "open", "close", "closeunadj", "lastupdated"],
        [["AAA", d.isoformat(), 10, 10, 10, still] for d in dated]
        + [["NEW", d.isoformat(), 10, 10, 20, still] for d in dated],
    )
    _zip(
        snapshot,
        "EVENTS",
        ["ticker", "date", "eventcodes"],
        [["AAA", "2023-10-10", "22|91"]] + ([["AAA", "2024-02-02", "13"]] if with_holdout else []),
    )
    _zip(
        snapshot,
        "SF1",
        SF1_HEADER,
        [
            sf1_row("AAA", "ART", "2023-06-30", "2023-08-10", 400.0),
            sf1_row("AAA", "ART", "2023-09-30", FILING_DAY.isoformat(), 500.0),
            sf1_row("AAA", "MRT", "2023-09-30", "2023-09-30", 999.0),  # restated: never kept
        ]
        + ([sf1_row("AAA", "ART", "2023-12-31", "2023-11-09", 777.0)] if with_holdout else []),
    )
    return root


def make_random_walk_raw(root: Path, *, symbols: int = 20, days: int = 40, seed: int = 0) -> Path:
    """Liquid random-walk stocks with a bar every regular-session minute. No edge by design."""
    import random

    rng = random.Random(seed)
    names = [f"RW{k:02d}" for k in range(symbols)]
    all_days = sessions()[:days]
    price = dict.fromkeys(names, 20.0)
    base = root / "massive" / "us_stocks_sip"
    for day in all_days:
        daily, minute = [], []
        for name in names:
            first = price[name]
            high = low = first
            for m in range(570, 960):
                o = price[name]
                c = round(o * (1 + rng.gauss(0, 0.0002)), 4)
                minute.append([name, 50_000, o, c, max(o, c), min(o, c), _ns(day, m), 50])
                price[name] = c
                high, low = max(high, o, c), min(low, o, c)
            daily.append([name, 50_000 * 390, first, price[name], high, low, _ns(day, 0), 9000])
        name = f"{day.year}/{day.month:02d}/{day.isoformat()}.csv.gz"
        _gz(base / "day_aggs_v1" / name, daily)
        _gz(base / "minute_aggs_v1" / name, minute)
    snapshot = root / "sharadar" / "2026-11-09"
    snapshot.mkdir(parents=True, exist_ok=True)
    head = [
        "table",
        "permaticker",
        "ticker",
        "name",
        "exchange",
        "category",
        "siccode",
        "sector",
        "industry",
        "currency",
        "location",
        "firstpricedate",
        "lastpricedate",
    ]
    _zip(
        snapshot,
        "TICKERS",
        head,
        [
            [
                "SEP",
                2000 + k,
                n,
                n,
                "NYSE",
                "Domestic Common Stock",
                "1",
                "S",
                "I",
                "USD",
                "US",
                "2020-01-02",
                "2026-11-09",
            ]
            for k, n in enumerate(names)
        ],
    )
    _zip(
        snapshot,
        "ACTIONS",
        ["date", "action", "ticker", "name", "value", "contraticker", "contraname"],
        [["2021-01-04", "dividend", names[0], names[0], "0.1", "", ""]],
    )
    _zip(
        snapshot,
        "DAILY",
        ["ticker", "date", "marketcap"],
        [[n, d.isoformat(), 1000.0] for d in all_days for n in names],
    )
    _zip(
        snapshot,
        "SEP",
        ["ticker", "date", "close", "closeunadj"],
        [[n, d.isoformat(), 20.0, 20.0] for d in all_days for n in names],
    )
    _zip(snapshot, "EVENTS", ["ticker", "date", "eventcodes"], [[names[0], "2021-01-04", "22"]])
    _zip(snapshot, "SF1", SF1_HEADER, [sf1_row(names[0], "ART", "2020-12-31", "2021-01-04", 1.0)])
    return root
