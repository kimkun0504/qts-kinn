"""Every stock that traded on one session up to the seal, with its size, liquidity, returns,
volatility and valuation as of that session, for the Workbench's screener. Prices come from the
sealed DataStore's panel and fundamentals only from filings made before the session."""

from __future__ import annotations

import math
from collections import OrderedDict
from datetime import date, timedelta
from typing import Protocol

import duckdb
import pyarrow as pa

from apps.workbench.stocks import FIRST, LAST

YEAR = 252
RETURNS = {"ret_1m": 21, "ret_3m": 63, "ret_6m": 126, "ret_1y": YEAR}
FUNDAMENTALS = ("revenueusd", "netinccmnusd", "equityusd", "fcf")
STALE_FUNDAMENTALS = timedelta(days=500)
COLUMNS = (
    "symbol", "permaticker", "name", "sector", "industry", "category", "exchange", "close",
    "market_cap", "adv20", "ret_1m", "ret_3m", "ret_6m", "ret_1y", "from_high", "vol_60",
    "pe", "ps", "pb", "fcf_yield", "revenue", "revenue_growth", "net_income", "filed",
)  # fmt: skip
CACHE = 6
_screens: OrderedDict[tuple[str, date], dict] = OrderedDict()


class Store(Protocol):
    build_id: str

    def sessions(self, start: date, end: date) -> list[date]: ...

    def panel(self, start: date, end: date, *, columns: str = "*") -> pa.Table: ...

    def securities(self) -> pa.Table: ...

    def fundamentals_as_of(self, day: date, *, fields: tuple[str, ...]) -> pa.Table: ...


def session_on(store: Store, on: date) -> tuple[date, list[date]]:
    asked = min(max(on, FIRST), LAST)
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


def _market_value(row: dict) -> float | None:
    cap, close, prev = row.get("marketcap_prev"), row.get("close"), row.get("prev_close")
    if cap is None:
        return None
    if close and prev and close > 0 and prev > 0 and 0.02 < close / prev < 50:
        return cap * close / prev
    return cap


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
        cap = _market_value(row)
        fcf = book.get("fcf") if company.get("currency") in (None, "USD") else None
        revenue, income = book.get("revenueusd"), book.get("netinccmnusd")
        growth = _ratio(revenue, book.get("revenueusd_year_ago"))
        values = {
            "symbol": row["symbol"] or company.get("ticker"),
            "permaticker": perm,
            "name": company.get("name"),
            "sector": company.get("sector"),
            "industry": company.get("industry"),
            "category": row["category"] or company.get("category"),
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
    key = (store.build_id, day)
    if key not in _screens:
        _screens[key] = {
            "schema": "screen-1",
            "on": day.isoformat(),
            "first": FIRST.isoformat(),
            "last": LAST.isoformat(),
            "columns": list(COLUMNS),
            "rows": _rows(store, day, window),
        }
        while len(_screens) > CACHE:
            _screens.popitem(last=False)
    else:
        _screens.move_to_end(key)
    return _screens[key]
