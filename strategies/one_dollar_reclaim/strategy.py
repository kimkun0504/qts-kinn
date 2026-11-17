"""Buy a reversal across a fixed nominal dollar level."""

from math import isfinite

import numpy as np

from kinn.core.types import Signal
from kinn.data.universe import Universe
from kinn.engine.intraday.data import DayView, SymbolDay
from kinn.engine.intraday.strategy import FeatureValues


def reclaim_minute(view: DayView, bars: SymbolDay, reference: float) -> int | None:
    start = int(bars.minute.searchsorted(view.open_minute))
    if start == len(bars.minute) or bars.minute[start] != view.open_minute:
        return None
    opened = bars.open[start]
    if not isfinite(opened) or not reference <= opened < 1.50 * reference:
        return None

    last = min(14 * 60 + 45, view.close_minute - 1)
    end = int(bars.minute.searchsorted(last, side="right"))
    minute = bars.minute[start:end]
    close = bars.close[start:end]
    candidates = 1 + np.flatnonzero(
        (minute[1:] >= view.open_minute + 5)
        & (np.diff(minute) == 1)
        & (close[:-1] > 0)
        & (close[:-1] < reference)
        & (close[1:] >= 1.01 * reference)
        & (close[1:] <= 1.08 * reference)
        & (close[1:] * bars.volume[start + 1 : end] >= 20_000)
    )
    for index in candidates:
        t = int(minute[index])
        window_start = int(minute.searchsorted(t - 30))
        history = close[window_start:index]
        if ((history > 0) & (history <= 0.97 * reference)).any():
            return t
    return None


class OneDollarReclaim:
    name = "one_dollar_reclaim"
    features = ()

    def __init__(self, reference: float):
        self.reference = reference
        self.universe = Universe(
            self.name, min_prev_close=reference, max_prev_close=1.50 * reference, min_adv20=500_000
        )

    def signals(self, view: DayView, features: FeatureValues) -> list[Signal]:
        signals = []
        for symbol, bars in view.symbols.items():
            minute = reclaim_minute(view, bars, self.reference)
            if minute is not None:
                signals.append(Signal(symbol, minute, expire_minute=minute + 1))
        return signals


def build(params: dict) -> OneDollarReclaim:
    reference = params.get("reference")
    if set(params) != {"reference"} or reference not in (1.0, 1.2):
        raise ValueError("one_dollar_reclaim requires a registered reference of 1.0 or 1.2")
    return OneDollarReclaim(float(reference))
