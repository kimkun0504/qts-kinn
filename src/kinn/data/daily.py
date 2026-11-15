"""Daily data for multi-day books: one row per session, one column per company.

Two kinds of array, and the difference is the lookahead rule:

- **Outcomes** (``open``, ``close``, ``ret``, ``dollar_volume``) of a session are known only
  after it. A view of session ``t`` can read them for sessions before ``t`` only.
- **Pre-open** values (``prev_close``, ``split``, ``dividend``, ``adv_prev``,
  ``marketcap_prev``, ``eligible`` and fundamentals) are known before the open of ``t``.

``ret`` is the total return from the company's previous close: price change, split-adjusted,
plus any cash dividend going ex that day.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

import numpy as np
import pyarrow as pa

from kinn.data.store import DataStore
from kinn.data.universe import Universe

OUTCOMES = ("open", "close", "ret", "dollar_volume")
PRE_OPEN = ("prev_close", "split", "dividend", "adv_prev", "marketcap_prev", "eligible")
_EPOCH = date(1970, 1, 1)


@dataclass
class DailyData:
    dates: list[date]
    permatickers: np.ndarray  # (N,) sorted
    symbols: list[str]
    sector: np.ndarray  # (N,) integer codes into ``sector_names``
    sector_names: list[str]
    open: np.ndarray  # (T, N) from here on
    close: np.ndarray
    ret: np.ndarray
    dollar_volume: np.ndarray
    prev_close: np.ndarray
    split: np.ndarray
    dividend: np.ndarray
    adv_prev: np.ndarray
    marketcap_prev: np.ndarray
    eligible: np.ndarray
    fundamentals: dict[str, np.ndarray] = field(default_factory=dict)  # pre-open, (T, N)

    def view(self, i: int) -> DailyView:
        return DailyView(self, i)

    def window(self, i: int, lookback: int) -> DailyData:
        """A copy of sessions ``[i - lookback, i]`` in which session ``i``'s outcomes are
        erased. Whatever an alpha computes from a view of this copy cannot have used them."""
        lo = max(0, i - lookback)
        cut = {}
        for name in OUTCOMES + PRE_OPEN:
            block = getattr(self, name)[lo : i + 1].copy()
            if name in OUTCOMES:
                block[-1] = np.nan
            cut[name] = block
        funds = {k: v[lo : i + 1].copy() for k, v in self.fundamentals.items()}
        return DailyData(
            dates=self.dates[lo : i + 1], permatickers=self.permatickers, symbols=self.symbols,
            sector=self.sector, sector_names=self.sector_names, fundamentals=funds, **cut,
        )  # fmt: skip


class DailyView:
    """What is known before the open of one session. Alphas and risk models get only this."""

    def __init__(self, data: DailyData, i: int):
        self._data = data
        self._i = i

    @property
    def day(self) -> date:
        return self._data.dates[self._i]

    @property
    def permatickers(self) -> np.ndarray:
        return self._data.permatickers

    @property
    def sector(self) -> np.ndarray:
        return self._data.sector

    @property
    def eligible(self) -> np.ndarray:
        return self._data.eligible[self._i]

    def today(self, name: str) -> np.ndarray:
        """A pre-open value for this session."""
        if name not in PRE_OPEN:
            raise KeyError(f"{name!r} is not known before the open")
        return getattr(self._data, name)[self._i]

    def fundamental(self, name: str) -> np.ndarray:
        """The latest value filed before this session (NaN where none)."""
        return self._data.fundamentals[name][self._i]

    def history(self, name: str, sessions: int) -> np.ndarray:
        """The last ``sessions`` rows strictly before this session, oldest first."""
        if name not in OUTCOMES + PRE_OPEN:
            raise KeyError(name)
        return getattr(self._data, name)[max(0, self._i - sessions) : self._i]


def _day_numbers(column: pa.ChunkedArray) -> np.ndarray:
    return column.cast(pa.int32()).to_numpy()


def load_daily(
    store: DataStore,
    sessions: list[date],
    universe: Universe,
    *,
    top_by_marketcap: int | None = None,
    include: tuple[int, ...] = (),
    fundamentals: tuple[str, ...] = (),
    dimension: str = "ART",
) -> DailyData:
    """Load ``sessions`` (consecutive) for every company in the universe on any of them."""
    start, end = sessions[0], sessions[-1]
    found = store.daily_candidates(start, end, universe=universe, top_by_marketcap=top_by_marketcap)
    perma = np.array(sorted(set(found) | set(include)), dtype=np.int64)
    days = np.array([(d - _EPOCH).days for d in sessions], dtype=np.int32)
    shape = (len(sessions), len(perma))
    arrays = {
        "open": np.full(shape, np.nan), "close": np.full(shape, np.nan),
        "dollar_volume": np.full(shape, np.nan, dtype=np.float32),
        "prev_close": np.full(shape, np.nan),
        "split": np.ones(shape, dtype=np.float32),
        "dividend": np.zeros(shape, dtype=np.float32),
        "adv_prev": np.full(shape, np.nan, dtype=np.float32),
        "marketcap_prev": np.full(shape, np.nan, dtype=np.float32),
        "eligible": np.zeros(shape, dtype=bool),
    }  # fmt: skip
    columns = {"open": "open", "close": "close", "dollar_volume": "dollar_volume",
               "prev_close": "prev_close", "split": "split_ratio", "adv_prev": "adv20_prev",
               "marketcap_prev": "marketcap_prev", "eligible": "eligible"}  # fmt: skip
    ids = perma.tolist()
    for year in range(start.year, end.year + 1):
        lo, hi = max(start, date(year, 1, 1)), min(end, date(year, 12, 31))
        if lo > hi:
            continue
        table = store.daily_long(
            lo, hi, universe=universe, permatickers=ids, top_by_marketcap=top_by_marketcap
        )
        rows = np.searchsorted(days, _day_numbers(table["date"]))
        cols = np.searchsorted(perma, table["permaticker"].to_numpy())
        for name, column in columns.items():
            values = table[column].to_numpy(zero_copy_only=False)
            arrays[name][rows, cols] = values
    table = store.dividends(start, end)
    day_numbers = _day_numbers(table["date"])
    rows = np.searchsorted(days, day_numbers)
    cols = np.searchsorted(perma, table["permaticker"].to_numpy())
    rows_ok = np.minimum(rows, len(days) - 1)
    cols_ok = np.minimum(cols, len(perma) - 1)
    keep = (days[rows_ok] == day_numbers) & (perma[cols_ok] == table["permaticker"].to_numpy())
    arrays["dividend"][rows[keep], cols[keep]] = table["amount"].to_numpy()[keep]
    with np.errstate(invalid="ignore", divide="ignore"):
        ret = (arrays["close"] + arrays["dividend"]) / arrays["prev_close"] - 1.0
    securities = store.securities()
    sector_of = dict(
        zip(securities["permaticker"].to_pylist(), securities["sector"].to_pylist(), strict=True)
    )
    labels = [sector_of.get(p) or "Unknown" for p in ids]
    names = sorted(set(labels))
    symbol_of = store.last_symbols(start, end, ids)
    funds = _as_of(store, days, perma, end, fundamentals, dimension) if fundamentals else {}
    return DailyData(
        fundamentals=funds,
        dates=list(sessions), permatickers=perma, symbols=[symbol_of.get(p, str(p)) for p in ids],
        sector=np.array([names.index(x) for x in labels], dtype=np.int32), sector_names=names,
        ret=ret.astype(np.float32), **arrays,
    )  # fmt: skip


def _as_of(store, days, perma, end, fields, dimension) -> dict[str, np.ndarray]:
    """For each session and company, the latest value filed on an earlier day."""
    table = store.fundamentals(end, fields=tuple(fields), dimension=dimension)
    company = table["permaticker"].to_numpy()
    cols = np.minimum(np.searchsorted(perma, company), len(perma) - 1)
    # First session strictly after the filing date: a filing is usable from the next session.
    rows = np.searchsorted(days, _day_numbers(table["datekey"]), side="right")
    keep = (perma[cols] == company) & (rows < len(days))
    rows, cols = rows[keep], cols[keep]
    out = {}
    for name in fields:
        values = table[name].to_numpy(zero_copy_only=False)[keep].astype(np.float64)
        grid = np.full((len(days), len(perma)), np.nan, dtype=np.float32)
        for r, c, v in zip(rows, cols, values, strict=True):  # in filing order: the last wins
            if v == v:
                grid[r, c] = v
        filled = np.isfinite(grid)
        index = np.where(filled, np.arange(len(days))[:, None], 0)
        np.maximum.accumulate(index, axis=0, out=index)
        carried = grid[index, np.arange(len(perma))]
        out[name] = np.where(filled.cumsum(axis=0) > 0, carried, np.nan).astype(np.float32)
    return out
