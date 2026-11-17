"""One session's data, as the simulator and strategies see it."""

from __future__ import annotations

import dataclasses
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import date

import numpy as np

from kinn.core.types import RTH_CLOSE, RTH_OPEN, CurrentReport, Disclosure
from kinn.data.inputs import EARNINGS_CODE, FORM8K_ITEMS, item
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
    # Insider (Form 4) disclosures by symbol, for strategies that declare the ``form4`` input:
    # only filings dated before ``day``, so all of it was public before the open.
    disclosures: Mapping[str, tuple[Disclosure, ...]] = field(default_factory=dict)
    # 8-K filings by symbol, oldest first, for strategies that declare the ``form8k`` input:
    # again only filings dated before ``day``.
    reports: Mapping[str, tuple[CurrentReport, ...]] = field(default_factory=dict)

    def upto(self, last_minute: int) -> DayView:
        return DayView(
            self.day,
            self.open_minute,
            self.close_minute,
            {s: sd.upto(last_minute) for s, sd in self.symbols.items()},
            self.disclosures,
            self.reports,
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


def load_disclosures(
    store: DataStore, day: date, sessions: int, members: Mapping[str, object]
) -> dict[str, tuple[Disclosure, ...]]:
    """Form 4 disclosures available on ``day`` for the session's members, matched by the
    trading symbol on the filing."""
    names = [f.name for f in dataclasses.fields(Disclosure)]
    found: dict[str, list[Disclosure]] = {}
    for row in store.form4(day, sessions=sessions).select(names).to_pylist():
        if row["symbol"] in members:
            found.setdefault(row["symbol"], []).append(Disclosure(**row))
    return {symbol: tuple(rows) for symbol, rows in sorted(found.items())}


def load_reports(
    store: DataStore, day: date, sessions: int, members: Mapping[str, Mapping]
) -> dict[str, tuple[CurrentReport, ...]]:
    """8-K filings available on ``day`` for the session's members, matched by company
    (permaticker) and keyed by the symbol the company trades under that day."""
    symbol_of = {row["permaticker"]: symbol for symbol, row in members.items()}
    found: dict[str, list[CurrentReport]] = {}
    for row in store.form8k(day, sessions=sessions).to_pylist():
        symbol = symbol_of.get(row["permaticker"])
        if symbol is None:
            continue
        codes = tuple(sorted({int(c) for c in row["eventcodes"].split("|") if c.isdigit()}))
        found.setdefault(symbol, []).append(
            CurrentReport(
                symbol,
                int(row["permaticker"]),
                row["filed"],
                codes,
                tuple(item(c) for c in codes if c in FORM8K_ITEMS),
                EARNINGS_CODE in codes,
            )
        )
    return {symbol: tuple(rows) for symbol, rows in sorted(found.items())}


def load_day(
    store: DataStore,
    day: date,
    universe: Universe,
    *,
    form4_sessions: int = 0,
    form8k_sessions: int = 0,
) -> DayData:
    """Load the universe's members for ``day`` with their minute bars, and, when asked for,
    that many sessions of insider disclosures (``form4_sessions``) and of 8-K filings
    (``form8k_sessions``)."""
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
    disclosures = load_disclosures(store, day, form4_sessions, members) if form4_sessions else {}
    reports = load_reports(store, day, form8k_sessions, members) if form8k_sessions else {}
    view = DayView(
        day, RTH_OPEN, int(close_minute), dict(sorted(symbols.items())), disclosures, reports
    )
    return DayData(view, {s: r["close"] for s, r in members.items() if r["close"] is not None})
