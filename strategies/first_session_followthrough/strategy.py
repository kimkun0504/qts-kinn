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


def decision_minute(view: DayView, bars: SymbolDay) -> int | None:
    start = int(bars.minute.searchsorted(view.open_minute))
    if start == len(bars.minute):
        return None
    first_minute = int(bars.minute[start])
    opening = bars.open[start]
    decision = first_minute + 29
    if first_minute > 750 or decision > view.close_minute - 60:
        return None
    if not np.isfinite(opening) or opening < 5:
        return None

    end = int(bars.minute.searchsorted(decision, side="right"))
    minutes = bars.minute[start:end]
    if len(minutes) < 25 or minutes[-1] != decision or minutes[-2] != decision - 1:
        return None
    close = bars.close[start:end]
    valid = np.isfinite(close) & (close > 0)
    if valid.sum() < 25 or not valid[-2:].all() or not (close[-2:] >= 1.05 * opening).all():
        return None
    turnover = close[valid] * bars.volume[start:end][valid]
    if turnover.sum() < 2_000_000 or turnover[-1] < 40_000:
        return None
    return decision


class FirstSessionFollowThrough:
    name = "first_session_followthrough"
    universe = FirstSessionUniverse(name, min_sessions_prior=0)
    features = ()

    def signals(self, view: DayView, features: FeatureValues) -> list[Signal]:
        if view.day < FIRST_SIGNAL_DATE:
            return []
        found = []
        for symbol, bars in view.symbols.items():
            minute = decision_minute(view, bars)
            if minute is not None:
                found.append(Signal(symbol, minute, expire_minute=minute + 1))
        return found


def build(params: dict) -> FirstSessionFollowThrough:
    if params:
        raise ValueError("first_session_followthrough accepts no parameters")
    return FirstSessionFollowThrough()
