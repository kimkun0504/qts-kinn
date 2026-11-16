"""Buy a confirmed recovery from a large decline on a first observed session."""

from datetime import date

import numpy as np

from kinn.core.types import Signal
from kinn.data.universe import Universe
from kinn.engine.intraday.data import DayView, SymbolDay
from kinn.engine.intraday.strategy import FeatureValues

FIRST_SIGNAL_DATE = date(2004, 1, 2)


class FirstSessionUniverse(Universe):
    def where(self) -> str:
        return f"({super().where()}) and sessions_prior = 0"


def reversal_minute(view: DayView, bars: SymbolDay) -> int | None:
    start = int(bars.minute.searchsorted(view.open_minute))
    if start == len(bars.minute):
        return None
    first_minute = int(bars.minute[start])
    opening = bars.open[start]
    if first_minute > 750 or not np.isfinite(opening) or opening < 5:
        return None

    latest = min(first_minute + 89, view.close_minute - 60)
    end = int(bars.minute.searchsorted(latest, side="right"))
    if end - start < 2:
        return None
    minutes = bars.minute[start:end]
    close = bars.close[start:end]
    valid = np.isfinite(close) & (close > 0)
    observed = np.cumsum(valid)[1:]
    elapsed = minutes[1:] - first_minute + 1
    turnover = np.zeros(len(minutes))
    np.multiply(close, bars.volume[start:end], out=turnover, where=valid)
    qualifies = (
        (elapsed >= 15)
        & (6 * observed >= 5 * elapsed)
        & (np.diff(minutes) == 1)
        & valid[:-1]
        & valid[1:]
        & (close[1:] <= 0.90 * opening)
        & (close[1:] >= 1.01 * close[:-1])
        & (np.cumsum(turnover)[1:] >= 2_000_000)
        & (turnover[1:] >= 40_000)
    )
    hits = np.flatnonzero(qualifies)
    return int(minutes[hits[0] + 1]) if len(hits) else None


class FirstSessionReversal:
    name = "first_session_reversal"
    universe = FirstSessionUniverse(name, min_sessions_prior=0)
    features = ()

    def signals(self, view: DayView, features: FeatureValues) -> list[Signal]:
        if view.day < FIRST_SIGNAL_DATE:
            return []
        found = []
        for symbol, bars in view.symbols.items():
            minute = reversal_minute(view, bars)
            if minute is not None:
                found.append(Signal(symbol, minute, expire_minute=minute + 1))
        return found


def build(params: dict) -> FirstSessionReversal:
    if params:
        raise ValueError("first_session_reversal accepts no parameters")
    return FirstSessionReversal()
