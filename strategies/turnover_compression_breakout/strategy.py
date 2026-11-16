"""Buy a confirmed breakout from a narrow range with unusually high turnover."""

import numpy as np

from kinn.core.types import Signal
from kinn.data.universe import Universe
from kinn.engine.intraday.data import DayView, SymbolDay
from kinn.engine.intraday.strategy import FeatureValues
from kinn.features import library as f


def breakout_minute(view: DayView, bars: SymbolDay, prior_close: float, adv: float) -> int | None:
    regular = (bars.minute >= view.open_minute) & (bars.minute < view.close_minute)
    minutes = bars.minute[regular]
    if not len(minutes) or minutes[0] != view.open_minute:
        return None
    opening = bars.open[regular][0]
    if not 0.95 * prior_close <= opening <= 1.05 * prior_close:
        return None

    length = view.close_minute - view.open_minute
    close = np.full(length, np.nan)
    turnover = np.zeros(length)
    price = bars.close[regular]
    valid = np.isfinite(price) & (price > 0)
    offset = minutes[valid] - view.open_minute
    close[offset] = price[valid]
    turnover[offset] = price[valid] * bars.volume[regular][valid]

    first = max(601 - view.open_minute, 31)
    last = min(810, view.close_minute - 75) - view.open_minute
    current = np.arange(first, last + 1)
    previous = close[current - 1]
    before_breakout = close[current - 2]
    possible = (
        (close[current] > previous)
        & (turnover[current] >= 40_000)
        & (~np.isfinite(before_breakout) | (previous >= 1.03 * before_breakout))
    )
    for minute in current[possible]:
        start, stop = minute - 31, minute - 1
        window = close[start:stop]
        observed = window[np.isfinite(window)]
        if len(observed) < 28:
            continue
        high = observed.max()
        if high > 1.02 * observed.min() or close[minute - 1] < 1.03 * high:
            continue
        if turnover[start:stop].sum() >= 0.30 * adv:
            return int(minute + view.open_minute)
    return None


class TurnoverCompressionBreakout:
    name = "turnover_compression_breakout"
    universe = Universe(name, min_prev_close=3, min_adv20=5e6, max_marketcap=2e9)
    features = (f.PREV_CLOSE, f.ADV20, f.MARKETCAP)

    def signals(self, view: DayView, features: FeatureValues) -> list[Signal]:
        signals = []
        for symbol, bars in view.symbols.items():
            prior = features[symbol]
            cap = prior[f.MARKETCAP.name]
            prior_close = prior[f.PREV_CLOSE.name]
            adv = prior[f.ADV20.name]
            if not 0 < cap < 2e9 or not prior_close >= 3 or not adv >= 5e6:
                continue
            minute = breakout_minute(view, bars, prior_close, adv)
            if minute is not None:
                signals.append(
                    Signal(symbol, minute, expire_minute=minute + 1, max_hold_minutes=60)
                )
        return signals


def build(params: dict) -> TurnoverCompressionBreakout:
    if params:
        raise ValueError("turnover_compression_breakout accepts no parameters")
    return TurnoverCompressionBreakout()
