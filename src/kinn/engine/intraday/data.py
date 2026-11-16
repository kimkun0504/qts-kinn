"""One session's data, as the simulator and strategies see it."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import date

import numpy as np

from kinn.core.types import RTH_CLOSE, RTH_OPEN
from kinn.data.store import DataStore
from kinn.data.universe import Universe

PRIOR_COLUMNS = (
    "prev_close",
    "adv20_prev",
    "marketcap_prev",
    "sessions_prior",
    "filings_prev",
    "ret60_prev",  # from build data-6; None on older builds
)
_EMPTY_F = np.empty(0, dtype=float)
_EMPTY_I = np.empty(0, dtype=np.int64)


@dataclass(frozen=True)
class SymbolDay:
    """One symbol's minute bars for one session, plus what was known before the open."""

    symbol: str
    permaticker: int
    minute: np.ndarray
    open: np.ndarray
    high: np.ndarray
    low: np.ndarray
    close: np.ndarray
    volume: np.ndarray
    prior: Mapping[str, float] = field(default_factory=dict)

    def upto(self, last_minute: int) -> SymbolDay:
        """The same symbol-day with only bars whose minute is at most ``last_minute``."""
        n = int(np.searchsorted(self.minute, last_minute, side="right"))
        return SymbolDay(
            self.symbol, self.permaticker, self.minute[:n], self.open[:n], self.high[:n],
            self.low[:n], self.close[:n], self.volume[:n], self.prior,
        )  # fmt: skip


@dataclass(frozen=True)
class DayView:
    """What a strategy may see: bars and prior-session columns. No outcomes of the day."""

    day: date
    open_minute: int
    close_minute: int
    symbols: Mapping[str, SymbolDay]

    def upto(self, last_minute: int) -> DayView:
        return DayView(
            self.day,
            self.open_minute,
            self.close_minute,
            {s: sd.upto(last_minute) for s, sd in self.symbols.items()},
        )


@dataclass(frozen=True)
class DayData:
    """A session for the simulator: the strategy's view plus the official closing prices."""

    view: DayView
    official_close: Mapping[str, float]


def make_symbol_day(symbol, permaticker, minute, open_, high, low, close, volume, prior=None):
    return SymbolDay(
        symbol,
        int(permaticker),
        np.asarray(minute, dtype=np.int64),
        np.asarray(open_, dtype=float),
        np.asarray(high, dtype=float),
        np.asarray(low, dtype=float),
        np.asarray(close, dtype=float),
        np.asarray(volume, dtype=np.int64),
        dict(prior or {}),
    )


def load_day(store: DataStore, day: date, universe: Universe) -> DayData:
    """Load the universe's members for ``day`` with their minute bars."""
    calendar = store.calendar(day, day).to_pylist()
    close_minute = calendar[0]["close_minute_et"] if calendar else RTH_CLOSE
    built = set(store.panel_columns())
    panel = store.panel(
        day,
        day,
        universe=universe,
        columns="symbol, permaticker, close, "
        + ", ".join(c if c in built else f"null as {c}" for c in PRIOR_COLUMNS),
    ).to_pylist()
    members = {row["symbol"]: row for row in panel}
    symbols: dict[str, SymbolDay] = {}
    if members:
        bars = store.minute(
            day,
            symbols=list(members),
            columns="symbol, minute_et, open, high, low, close, volume",
        )
        names = bars["symbol"].to_numpy(zero_copy_only=False)
        minute = bars["minute_et"].to_numpy().astype(np.int64)
        cols = [bars[c].to_numpy() for c in ("open", "high", "low", "close", "volume")]
        if len(names):
            starts = np.flatnonzero(np.r_[True, names[1:] != names[:-1]])
            ends = np.r_[starts[1:], len(names)]
            for a, b in zip(starts, ends, strict=True):
                row = members[names[a]]
                symbols[names[a]] = SymbolDay(
                    names[a],
                    row["permaticker"],
                    minute[a:b],
                    cols[0][a:b],
                    cols[1][a:b],
                    cols[2][a:b],
                    cols[3][a:b],
                    cols[4][a:b].astype(np.int64),
                    {k: row[k] for k in PRIOR_COLUMNS},
                )
    for symbol, row in members.items():
        if symbol not in symbols:  # a member with no trade today
            symbols[symbol] = SymbolDay(
                symbol, row["permaticker"], _EMPTY_I, _EMPTY_F, _EMPTY_F, _EMPTY_F, _EMPTY_F,
                _EMPTY_I, {k: row[k] for k in PRIOR_COLUMNS},
            )  # fmt: skip
    view = DayView(day, RTH_OPEN, int(close_minute), dict(sorted(symbols.items())))
    return DayData(view, {s: r["close"] for s, r in members.items() if r["close"] is not None})
