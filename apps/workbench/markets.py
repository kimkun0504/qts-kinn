"""The Markets page: index, sector, bond, commodity and foreign funds on one session up to the
seal, with their returns over the usual spans, and how many US stocks rose and fell each day.
Fund prices are the vendor's daily bars as traded; a one-day move too large to be a price
(a split or a reverse split) is taken out so the returns run on."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Protocol

import pandas as pd
import pyarrow as pa

from apps.workbench.stocks import FIRST, LAST, continuous

GROUPS: list[tuple[str, list[tuple[str, str]]]] = [
    ("US stocks", [("SPY", "S&P 500"), ("QQQ", "Nasdaq 100"), ("DIA", "Dow Jones industrials"),
                   ("MDY", "S&P mid caps"), ("IWM", "Russell 2000")]),
    ("Sectors", [("XLK", "Technology"), ("XLC", "Communication services"),
                 ("XLY", "Consumer discretionary"), ("XLP", "Consumer staples"),
                 ("XLV", "Health care"), ("XLF", "Financials"), ("XLI", "Industrials"),
                 ("XLE", "Energy"), ("XLB", "Materials"), ("XLRE", "Real estate"),
                 ("XLU", "Utilities")]),
    ("Rates, credit and commodities", [("TLT", "Treasuries, 20 years and more"),
                                       ("IEF", "Treasuries, 7 to 10 years"),
                                       ("HYG", "High-yield bonds"), ("GLD", "Gold"), ("USO", "Oil"),
                                       ("UUP", "US dollar")]),
    ("Abroad", [("EFA", "Developed markets"), ("EEM", "Emerging markets")]),
    ("Volatility", [("VIXY", "VIX futures")]),
]  # fmt: skip
SPANS = {"day": 1, "week": 5, "month": 21, "quarter": 63, "year": 252, "three_years": 756}
BREADTH_DAYS = 400
CORRELATION_DAYS = 252


class Store(Protocol):
    def sessions(self, start: date, end: date) -> list[date]: ...

    def daily(self, start: date, end: date, *, symbols: list[str]) -> pa.Table: ...

    def breadth(self, start: date, end: date) -> pa.Table: ...


def _change(values: list[float | None], back: int) -> float | None:
    if len(values) <= back or values[-1] is None or values[-1 - back] is None:
        return None
    return values[-1] / values[-1 - back] - 1


def _round(value: float | None, digits: int = 6) -> float | None:
    return None if value is None else float(f"{value:.{digits}g}")


def _correlation(by: dict[str, list[tuple[date, float | None]]], day: date) -> dict:
    frame = {}
    for symbol, series in by.items():
        series = sorted(series)
        if not series or series[-1][0] != day:
            continue
        values = continuous([c for _, c in series])
        frame[symbol] = pd.Series(values, index=[d for d, _ in series], dtype="float64")
    if not frame:
        return {"symbols": [], "matrix": [], "sessions": 0}
    prices = pd.DataFrame(frame).sort_index().iloc[-(CORRELATION_DAYS + 1) :]
    moves = prices.pct_change(fill_method=None).iloc[1:]
    order = [s for _, members in GROUPS for s, _ in members if s in moves.columns]
    matrix = moves[order].corr(min_periods=CORRELATION_DAYS // 2)
    return {
        "symbols": order,
        "matrix": [
            [_round(v, 3) if pd.notna(v) else None for v in row] for row in matrix.to_numpy()
        ],
        "sessions": int(len(moves)),
    }


def markets(store: Store, on: date | None = None) -> dict:
    asked = min(max(on or LAST, FIRST), LAST)
    sessions = store.sessions(asked - timedelta(days=14), asked)
    if not sessions:
        raise ValueError(f"no trading session on or before {asked.isoformat()}")
    day = sessions[-1]
    symbols = [s for _, members in GROUPS for s, _ in members]
    bars = store.daily(day - timedelta(days=1200), day, symbols=symbols).to_pylist()
    by: dict[str, list[tuple[date, float | None]]] = {}
    for row in bars:
        by.setdefault(row["symbol"], []).append((row["date"], row["close"]))
    year_start = next((d for d in store.sessions(date(day.year - 1, 12, 20), day)
                       if d.year == day.year), None)  # fmt: skip
    groups = []
    for title, members in GROUPS:
        rows = []
        for symbol, name in members:
            series = sorted(by.get(symbol, []))
            if not series or series[-1][0] != day:
                rows.append({"symbol": symbol, "name": name, "close": None})
                continue
            values = continuous([c for _, c in series])
            dates = [d for d, _ in series]
            since = dates.index(year_start) - 1 if year_start in dates else None
            rows.append({
                "symbol": symbol, "name": name, "close": _round(series[-1][1]),
                **{span: _round(_change(values, n)) for span, n in SPANS.items()},
                "year_to_date": _round(values[-1] / values[since] - 1)
                if since is not None and since >= 0 and values[since] else None,
            })  # fmt: skip
        groups.append({"title": title, "rows": rows})
    breadth = store.breadth(day - timedelta(days=BREADTH_DAYS), day).to_pylist()
    correlation = _correlation(by, day)
    return {
        "schema": "markets-1",
        "on": day.isoformat(),
        "first": FIRST.isoformat(),
        "last": LAST.isoformat(),
        "groups": groups,
        "correlation": correlation,
        "breadth": [{"date": r["date"].isoformat(), "advancing": r["advancing"],
                     "declining": r["declining"], "traded": r["traded"]} for r in breadth],
    }  # fmt: skip
