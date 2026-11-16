"""Buy early demand on the first session observed for a security."""

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


def decision_minute(view: DayView, bars: SymbolDay, turnover_timing: bool) -> int | None:
    start = int(bars.minute.searchsorted(view.open_minute))
    if start == len(bars.minute):
        return None
    first_minute = int(bars.minute[start])
    opening = bars.open[start]
    if first_minute > 750 or not np.isfinite(opening) or opening < 5:
        return None

    deadline = first_minute + 29
    latest = min(deadline, view.close_minute - 60)
    end = int(bars.minute.searchsorted(latest, side="right"))
    if end - start < 5:
        return None
    minutes = bars.minute[start:end]
    close = bars.close[start:end]
    valid = np.isfinite(close) & (close > 0)
    observed = np.cumsum(valid)[1:]
    elapsed = minutes[1:] - first_minute + 1
    turnover = np.zeros(len(minutes))
    np.multiply(close, bars.volume[start:end], out=turnover, where=valid)
    above = valid & (close >= 1.05 * opening)
    qualifies = (
        (observed >= 5)
        & (6 * observed >= 5 * elapsed)
        & (np.diff(minutes) == 1)
        & above[:-1]
        & above[1:]
        & (np.cumsum(turnover)[1:] >= 2_000_000)
        & (turnover[1:] >= 40_000)
    )
    if not turnover_timing:
        qualifies &= minutes[1:] == deadline
    hits = np.flatnonzero(qualifies)
    return int(minutes[hits[0] + 1]) if len(hits) else None


class FirstSessionFollowThrough:
    name = "first_session_followthrough"
    universe = FirstSessionUniverse(name, min_sessions_prior=0)
    features = ()

    def __init__(self, turnover_timing: bool = False):
        self.turnover_timing = turnover_timing

    def signals(self, view: DayView, features: FeatureValues) -> list[Signal]:
        if view.day < FIRST_SIGNAL_DATE:
            return []
        found = []
        for symbol, bars in view.symbols.items():
            minute = decision_minute(view, bars, self.turnover_timing)
            if minute is not None:
                found.append(Signal(symbol, minute, expire_minute=minute + 1))
        return found


def build(params: dict) -> FirstSessionFollowThrough:
    turnover_timing = params.get("turnover_timing", False)
    if params.keys() - {"turnover_timing"} or not isinstance(turnover_timing, bool):
        raise ValueError("first_session_followthrough accepts only boolean turnover_timing")
    return FirstSessionFollowThrough(turnover_timing)
