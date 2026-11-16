"""Where a session's bars come from.

A tape hands the session one closed minute at a time, with a view of every bar known so far.
``ReplayTape`` plays a past session from the research store (so the holdout seal applies). A
live tape, fed by the vendor's real-time stream, will implement the same three members.
"""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from datetime import date
from typing import Protocol

import numpy as np

from kinn.data.store import DataStore
from kinn.data.universe import Universe
from kinn.engine.intraday.data import DayView, load_day


class Tape(Protocol):
    day: date
    open_minute: int
    close_minute: int

    def minutes(self) -> Iterator[tuple[int, DayView]]:
        """Each regular-session minute that has closed, with the view up to it."""

    def close(self) -> tuple[DayView, Mapping[str, float]]:
        """After the session: the whole day and the official closing prices."""


class ReplayTape:
    """A past session, minute by minute, exactly as the backtest saw it."""

    def __init__(self, store: DataStore, day: date, universe: Universe):
        self.day = day
        self._data = load_day(store, day, universe)  # refuses holdout dates
        self.open_minute = self._data.view.open_minute
        self.close_minute = self._data.view.close_minute
        stamps = [sd.minute for sd in self._data.view.symbols.values() if len(sd.minute)]
        seen = np.unique(np.concatenate(stamps)) if stamps else np.empty(0, dtype=np.int64)
        self._minutes = [int(m) for m in seen if self.open_minute <= m < self.close_minute]

    @property
    def symbols(self) -> int:
        return len(self._data.view.symbols)

    def minutes(self) -> Iterator[tuple[int, DayView]]:
        for minute in self._minutes:
            yield minute, self._data.view.upto(minute)

    def close(self) -> tuple[DayView, Mapping[str, float]]:
        return self._data.view, self._data.official_close
