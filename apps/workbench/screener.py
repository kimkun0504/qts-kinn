"""Every stock that traded on one session up to the seal, with its size, liquidity, returns,
volatility and valuation as of that session, for the Workbench's screener. Prices come from the
sealed DataStore's panel and fundamentals only from filings made before the session."""

from __future__ import annotations

import math
import threading
from collections import OrderedDict
from collections.abc import Callable
from datetime import date, timedelta
from typing import Protocol

import duckdb
import pyarrow as pa

from apps.workbench.stocks import FIRST, LAST, market_value, reports_in_dollars

YEAR = 252
RETURNS = {"ret_1d": 1, "ret_1m": 21, "ret_3m": 63, "ret_6m": 126, "ret_1y": YEAR}
FUNDAMENTALS = ("revenueusd", "netinccmnusd", "equityusd", "fcf")
STALE_FUNDAMENTALS = timedelta(days=500)
COLUMNS = (
    "symbol", "permaticker", "name", "sector", "industry", "category", "exchange", "close",
    "market_cap", "adv20", "ret_1d", "ret_1m", "ret_3m", "ret_6m", "ret_1y", "from_high", "vol_60",
    "pe", "ps", "pb", "fcf_yield", "revenue", "revenue_growth", "net_income", "filed",
)  # fmt: skip
CACHE = 6


class Recent:
    def __init__(self, size: int):
        self._items: OrderedDict[tuple[str, date], dict] = OrderedDict()
        self._size = size
        self._lock = threading.Lock()

    def get(self, key: tuple[str, date], make: Callable[[], dict]) -> dict:
        with self._lock:
            if key in self._items:
                self._items.move_to_end(key)
                return self._items[key]
        value = make()
        with self._lock:
            self._items[key] = value
            self._items.move_to_end(key)
            while len(self._items) > self._size:
                self._items.popitem(last=False)
        return value

    def clear(self) -> None:
        with self._lock:
            self._items.clear()


_screens = Recent(CACHE)


class Store(Protocol):
    build_id: str

    def sessions(self, start: date, end: date) -> list[date]: ...

    def panel(self, start: date, end: date, *, columns: str = "*") -> pa.Table: ...

    def securities(self) -> pa.Table: ...

    def fundamentals_as_of(self, day: date, *, fields: tuple[str, ...]) -> pa.Table: ...

    def daily(self, start: date, end: date, *, symbols: list[str]) -> pa.Table: ...


_first: dict[str, date] = {}


def first_session(store: Store) -> date:
    if store.build_id not in _first:
        days = store.sessions(FIRST, LAST)
        _first[store.build_id] = days[0] if days else FIRST
    return _first[store.build_id]


def session_on(store: Store, on: date) -> tuple[date, list[date]]:
    asked = min(max(on, first_session(store)), LAST)
    days = store.sessions(asked - timedelta(days=420), asked)
    if not days:
        raise ValueError(f"no trading session on or before {asked.isoformat()}")
    return days[-1], days[-(YEAR + 1) :]


RETURN_SQL = ", ".join(
    f"case when max(k) >= {n} then exp(sum(lr) filter (where k < {n})) - 1 end as {name}"
    for name, n in RETURNS.items()
)
MEASURES = f"""
with r as (
    select w.permaticker, c.k, w.close, w.high,
           case when w.prev_close > 0 and w.close > 0
                     and w.close / w.prev_close between 0.02 and 50
                then ln(w.close / w.prev_close) else 0 end as lr
    from w join cal c using (date)),
s as (
    select *, coalesce(sum(lr) over (partition by permaticker order by k
                                     rows between unbounded preceding and 1 preceding), 0)
              as later from r)
select permaticker,
       {RETURN_SQL},
       case when count(*) filter (where k < 60) >= 40
            then stddev_samp(lr) filter (where k < 60) * sqrt({YEAR}) end as vol_60,
       1 / max(case when close > 0 and high > 0 then high * exp(-later) / close end) - 1
           as from_high
from s group by permaticker
"""


def _number(value, digits: int = 6):
    if value is None or (isinstance(value, float) and not math.isfinite(value)):
        return None
    if value == 0:
        return 0.0
    return float(f"{float(value):.{digits}g}")


def _ratio(top, bottom):
    if top is None or bottom is None or bottom <= 0:
        return None
    return top / bottom


def _rows(store: Store, day: date, window: list[date]) -> list[list]:
    today = store.panel(
        day, day,
        columns="permaticker, symbol, category, exchange, close, prev_close, marketcap_prev, "
        "adv20_prev",
    )  # fmt: skip
    bars = store.panel(window[0], day, columns="date, permaticker, close, high, prev_close")
    cal = pa.table(
        {"date": pa.array(window, pa.date32()), "k": list(range(len(window) - 1, -1, -1))}
    )
    con = duckdb.connect()
    try:
        con.register("w", bars)
        con.register("cal", cal)
        measured = {r["permaticker"]: r for r in con.sql(MEASURES).to_arrow_table().to_pylist()}
    finally:
        con.close()
    companies = {r["permaticker"]: r for r in store.securities().to_pylist()}
    books = {
        r["permaticker"]: r
        for r in store.fundamentals_as_of(day, fields=FUNDAMENTALS).to_pylist()
        if r["calendardate"] and r["calendardate"] >= day - STALE_FUNDAMENTALS
    }
    rows = []
    for row in today.to_pylist():
        perm = row["permaticker"]
        company = companies.get(perm, {})
        m = measured.get(perm, {})
        book = books.get(perm, {})
        cap = market_value(row)
        category = row["category"] or company.get("category")
        fcf = book.get("fcf") if reports_in_dollars(category) else None
        revenue, income = book.get("revenueusd"), book.get("netinccmnusd")
        growth = _ratio(revenue, book.get("revenueusd_year_ago"))
        values = {
            "symbol": row["symbol"] or company.get("ticker"),
            "permaticker": perm,
            "name": company.get("name"),
            "sector": company.get("sector"),
            "industry": company.get("industry"),
            "category": category,
            "exchange": row["exchange"] or company.get("exchange"),
            "close": _number(row["close"]),
            "market_cap": _number(cap),
            "adv20": _number(row["adv20_prev"]),
            **{name: _number(m.get(name)) for name in (*RETURNS, "vol_60", "from_high")},
            "pe": _number(_ratio(cap, income)),
            "ps": _number(_ratio(cap, revenue)),
            "pb": _number(_ratio(cap, book.get("equityusd"))),
            "fcf_yield": _number(fcf / cap) if fcf is not None and cap else None,
            "revenue": _number(revenue),
            "revenue_growth": _number(growth - 1) if growth is not None else None,
            "net_income": _number(income),
            "filed": book["datekey"].isoformat() if book.get("datekey") else None,
        }
        rows.append([values[name] for name in COLUMNS])
    rows.sort(key=lambda r: -(r[COLUMNS.index("market_cap")] or 0))
    return rows


def screen(store: Store, on: date | None = None) -> dict:
    day, window = session_on(store, on or LAST)
    return _screens.get(
        (store.build_id, day),
        lambda: {
            "schema": "screen-1",
            "on": day.isoformat(),
            "first": first_session(store).isoformat(),
            "last": LAST.isoformat(),
            "columns": list(COLUMNS),
            "rows": _rows(store, day, window),
        },
    )


FORWARD = {"next_1m": 21, "next_3m": 63, "next_6m": 126, "next_1y": YEAR}
FORWARD_SQL = ", ".join(
    f"exp(sum(lr) filter (where k between 1 and {n})) - 1 as {name}" for name, n in FORWARD.items()
)
AHEAD = f"""
with r as (
    select w.permaticker, c.k,
           case when w.prev_close > 0 and w.close > 0
                     and w.close / w.prev_close between 0.02 and 50
                then ln(w.close / w.prev_close) else 0 end as lr
    from w join cal c using (date))
select permaticker, {FORWARD_SQL}, max(k) as last_k
from r group by permaticker having min(k) = 0
"""
_ahead = Recent(CACHE)


def _spy(store: Store, days: list[date]) -> dict:
    try:
        rows = store.daily(days[0], days[-1], symbols=["SPY"]).to_pylist()
    except (KeyError, ValueError, duckdb.Error):
        return {}
    close = {r["date"]: r["close"] for r in rows}
    start = close.get(days[0])
    return {
        name: _number(close[days[n]] / start - 1)
        for name, n in FORWARD.items()
        if start and n < len(days) and close.get(days[n])
    }


def ahead(store: Store, on: date) -> dict:
    day, _ = session_on(store, on)
    return _ahead.get((store.build_id, day), lambda: _what_came_next(store, day))


def _what_came_next(store: Store, day: date) -> dict:
    days = store.sessions(day, min(LAST, day + timedelta(days=400)))[: YEAR + 1]
    bars = store.panel(day, days[-1], columns="date, permaticker, close, prev_close")
    cal = pa.table({"date": pa.array(days, pa.date32()), "k": list(range(len(days)))})
    con = duckdb.connect()
    try:
        con.register("w", bars)
        con.register("cal", cal)
        rows = con.sql(AHEAD).to_arrow_table().to_pylist()
    finally:
        con.close()
    known = {name: n < len(days) for name, n in FORWARD.items()}
    return {
        "schema": "screen-ahead-1",
        "on": day.isoformat(),
        "through": days[-1].isoformat(),
        "known": known,
        "spy": _spy(store, days),
        "columns": ["permaticker", *FORWARD, "stopped"],
        "rows": [
            [r["permaticker"],
             *[_number(r[name]) if known[name] else None for name in FORWARD],
             days[r["last_k"]].isoformat() if r["last_k"] < len(days) - 1 else None]
            for r in rows
        ],
    }  # fmt: skip
