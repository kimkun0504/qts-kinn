"""Buy the first confirmed pullback after a high-turnover intraday advance."""

import numpy as np

from kinn.core.types import Signal
from kinn.data.universe import Universe
from kinn.engine.intraday.data import DayView, SymbolDay
from kinn.engine.intraday.strategy import FeatureValues
from kinn.features import library as f


def pullback_minute(view: DayView, bars: SymbolDay, prior_close: float, adv: float) -> int | None:
    regular = (bars.minute >= view.open_minute) & (bars.minute < view.close_minute)
    minutes = bars.minute[regular]
    if not len(minutes) or minutes[0] != view.open_minute:
        return None
    opening = bars.open[regular][0]
    if not 0.95 * prior_close <= opening <= 1.05 * prior_close:
        return None

    closes = bars.close[regular]
    turnover = closes * bars.volume[regular]
    above = closes >= 1.20 * opening
    setup = np.flatnonzero(
        (minutes[1:] >= 584)
        & (minutes[1:] <= 719)
        & (np.diff(minutes) == 1)
        & above[:-1]
        & above[1:]
        & (np.cumsum(turnover)[1:] >= adv)
    )
    if not len(setup):
        return None

    first = int(setup[0] + 1)
    after = closes[first:]
    after_minute = minutes[first:]
    decision = after_minute[2:]
    previous_peak = np.maximum.accumulate(after)[1:-1]
    latest = min(885, view.close_minute - 75)
    pullbacks = np.flatnonzero(
        (decision <= latest)
        & (np.diff(after_minute)[1:] == 1)
        & (after[2:] <= 0.92 * previous_peak)
        & (after[2:] >= 1.01 * after[1:-1])
        & (after[2:] > opening)
        & (turnover[first + 2 :] >= 40_000)
    )
    return int(decision[pullbacks[0]]) if len(pullbacks) else None


class VolumeSurgePullback:
    name = "volume_surge_pullback"
    universe = Universe(name, min_prev_close=3, min_adv20=1_000_000, max_marketcap=2e9)
    features = (f.PREV_CLOSE, f.ADV20, f.MARKETCAP)

    def signals(self, view: DayView, features: FeatureValues) -> list[Signal]:
        found = []
        for symbol, bars in view.symbols.items():
            prior = features[symbol]
            cap = prior[f.MARKETCAP.name]
            price = prior[f.PREV_CLOSE.name]
            adv = prior[f.ADV20.name]
            if not 0 < cap < 2e9 or not price >= 3 or not adv >= 1_000_000:
                continue
            minute = pullback_minute(view, bars, price, adv)
            if minute is not None:
                found.append(Signal(symbol, minute, expire_minute=minute + 1, max_hold_minutes=60))
        return found


def build(params: dict) -> VolumeSurgePullback:
    if params:
        raise ValueError("volume_surge_pullback accepts no parameters")
    return VolumeSurgePullback()
