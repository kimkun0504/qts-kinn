"""A small in-memory stand-in for the sealed DataStore, for the Lab's tests.

It holds a few stocks' daily bars and answers the same queries the Lab makes, with the same
columns, using DuckDB over Arrow tables (so a universe's SQL is evaluated for real)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta

import duckdb
import numpy as np
import pyarrow as pa

from kinn.data.universe import COMMON_STOCK

START = date(2013, 11, 1)
END = date(2015, 12, 31)


def business_days(start: date = START, end: date = END) -> list[date]:
    days, day = [], start
    while day <= end:
        if day.weekday() < 5:
            days.append(day)
        day += timedelta(days=1)
    return days


@dataclass
class Stock:
    ticker: str
    close: np.ndarray  # one per session; NaN = no bar that day
    open: np.ndarray | None = None
    high: np.ndarray | None = None
    low: np.ndarray | None = None
    volume: float = 200_000.0
    transactions: float = 400.0
    split: dict[int, float] = field(default_factory=dict)  # session row -> ratio (2 = 2-for-1)
    market_cap: float = 1e9
    sector: str = "Technology"
    category: str = COMMON_STOCK[0]
    siccode: str = "7372"


def walk(rows: int, start: float, drift: float, seed: int, noise: float = 0.01) -> np.ndarray:
    rng = np.random.default_rng(seed)
    return start * np.exp(np.cumsum(drift + noise * rng.standard_normal(rows)))


class FakeStore:
    build_id = "fake-build"

    def __init__(
        self,
        stocks: list[Stock],
        sessions: list[date] | None = None,
        *,
        events: list[tuple[date, str, str]] = (),
        fundamentals: list[tuple[str, date, dict]] = (),
    ) -> None:
        self.days = sessions or business_days()
        self.stocks = stocks
        rows = []
        for perm, s in enumerate(stocks, start=1001):
            close = np.asarray(s.close, dtype=float)
            open_ = close if s.open is None else np.asarray(s.open, dtype=float)
            high = np.maximum(open_, close) * 1.01 if s.high is None else np.asarray(s.high)
            low = np.minimum(open_, close) * 0.99 if s.low is None else np.asarray(s.low)
            prior, last_close, last_day = 0, None, None
            for t, day in enumerate(self.days):
                if not np.isfinite(close[t]):
                    continue
                ratio = s.split.get(t, 1.0)
                rows.append(
                    {
                        "date": day,
                        "permaticker": perm,
                        "symbol": s.ticker,
                        "open": open_[t],
                        "high": high[t],
                        "low": low[t],
                        "close": close[t],
                        "volume": s.volume,
                        "dollar_volume": s.volume * close[t],
                        "transactions": s.transactions,
                        "prev_close": None if last_close is None else last_close / ratio,
                        "prev_date": last_day,
                        "adv20_prev": s.volume * close[t],
                        "marketcap_prev": s.market_cap,
                        "category": s.category,
                        "sessions_prior": prior,
                    }
                )
                prior, last_close, last_day = prior + 1, close[t], day
        self.panel = pa.Table.from_pylist(rows)
        self.master = pa.Table.from_pylist(
            [
                {
                    "permaticker": perm,
                    "ticker": s.ticker,
                    "name": f"{s.ticker} Inc",
                    "sector": s.sector,
                    "industry": "Software",
                    "exchange": "NASDAQ",
                    "siccode": s.siccode,
                    "category": s.category,
                }
                for perm, s in enumerate(stocks, start=1001)
            ]
        )
        perm_of = {s.ticker: p for p, s in enumerate(stocks, start=1001)}
        self.events_table = pa.Table.from_pylist(
            [{"permaticker": perm_of[t], "date": d, "eventcodes": c} for d, t, c in events],
            schema=pa.schema(
                [("permaticker", pa.int64()), ("date", pa.date32()), ("eventcodes", pa.string())]
            ),
        )
        self.fundamental_rows = [(perm_of[t], d, values) for t, d, values in fundamentals]
        spy = walk(len(self.days), 200.0, 0.0003, seed=99)
        self.spy = pa.Table.from_pylist(
            [
                {"date": d, "symbol": "SPY", "close": float(c), "transactions": 1e5}
                for d, c in zip(self.days, spy, strict=True)
            ]
        )

    def _sql(self, sql: str, params: list, **tables) -> pa.Table:
        con = duckdb.connect()
        try:
            for name, table in tables.items():
                con.register(name, table)
            return con.sql(sql, params=params).to_arrow_table()
        finally:
            con.close()

    def sessions(self, start: date, end: date) -> list[date]:
        return [d for d in self.days if start <= d <= end]

    def securities(self) -> pa.Table:
        return self.master

    def universe_members(self, start, end, universe) -> list[int]:
        out = self._sql(
            f"select distinct permaticker from panel where date between ? and ? "
            f"and {universe.where()} order by 1",
            [start, end],
            panel=self.panel,
        )
        return out["permaticker"].to_pylist()

    def panel_of(self, start, end, *, permatickers, columns) -> pa.Table:
        return self._sql(
            f"select {columns} from panel where date between ? and ? "
            "and permaticker in (select unnest(?)) order by date, permaticker",
            [start, end, permatickers],
            panel=self.panel,
        )

    def daily(self, start, end, *, symbols) -> pa.Table:
        bars = self.panel.select(["date", "symbol", "close", "transactions"])
        both = pa.concat_tables([bars, self.spy.cast(bars.schema)])
        return self._sql(
            "select * from bars where date between ? and ? and symbol in (select unnest(?)) "
            "order by date, symbol",
            [start, end, symbols],
            bars=both,
        )

    def events(self, start, end) -> pa.Table:
        return self._sql(
            "select * from e where date between ? and ? order by date, permaticker",
            [start, end],
            e=self.events_table,
        )

    def fundamentals(self, end, *, fields) -> pa.Table:
        rows = [
            {"permaticker": p, "datekey": d, **{f: values.get(f) for f in fields}}
            for p, d, values in self.fundamental_rows
            if d <= end
        ]
        schema = pa.schema(
            [
                ("permaticker", pa.int64()),
                ("datekey", pa.date32()),
                *[(f, pa.float64()) for f in fields],
            ]
        )
        return pa.Table.from_pylist(rows, schema=schema)


def standard(rows: int | None = None) -> FakeStore:
    """Five ordinary stocks over 2013-11 to 2015-12: up, down, flat, a 2-for-1 split and one
    that stops trading."""
    days = business_days()
    n = rows or len(days)
    split_row = days.index(date(2015, 3, 2))
    stopped = days.index(date(2015, 6, 1))
    splitter = walk(n, 80.0, 0.0005, seed=3)
    splitter[split_row:] /= 2
    gone = walk(n, 30.0, -0.0002, seed=4)
    gone[stopped:] = np.nan
    return FakeStore(
        [
            Stock("UPP", walk(n, 50.0, 0.001, seed=1)),
            Stock("DWN", walk(n, 40.0, -0.001, seed=2), sector="Energy"),
            Stock("SPL", splitter, split={split_row: 2.0}),
            Stock("GON", gone, sector="Energy"),
            Stock("FLT", walk(n, 20.0, 0.0, seed=5), transactions=50.0),
        ],
        days,
        events=[(date(2015, 2, 10), "UPP", "22|91"), (date(2015, 4, 7), "DWN", "13")],
        fundamentals=[
            ("UPP", date(2015, 2, 10), {"revenueusd": 1e8, "epsusd": 1.5}),
            ("UPP", date(2015, 5, 8), {"revenueusd": 1.2e8, "epsusd": 1.7}),
        ],
    )
