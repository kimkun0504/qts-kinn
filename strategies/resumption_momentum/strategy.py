"""Buy persistent upward price pressure after a short gap in observed trading."""

from datetime import date

import numpy as np

from kinn.core.types import Signal
from kinn.data.universe import Universe
from kinn.engine.intraday.data import DayView
from kinn.engine.intraday.strategy import FeatureValues
from kinn.features import library as f

FIRST_SIGNAL_DATE = date(2014, 5, 12)


class ResumptionMomentum:
    name = "resumption_momentum"
    universe = Universe(name, min_prev_close=2, min_adv20=1_000_000, max_marketcap=2e9)
    features = (f.MARKETCAP,)

    def signals(self, view: DayView, features: FeatureValues) -> list[Signal]:
        if view.day < FIRST_SIGNAL_DATE:
            return []

        found = []
        for symbol, bars in view.symbols.items():
            if not features[symbol][f.MARKETCAP.name] > 0:
                continue
            distance = np.diff(bars.minute)
            resumed = np.flatnonzero((distance >= 5) & (distance <= 7)) + 1
            for i in resumed:
                if i < 5 or i + 1 == len(bars.minute) or bars.minute[i - 5] < view.open_minute:
                    continue
                j = i + 1
                minute = int(bars.minute[j])
                if not 585 <= minute <= min(885, view.close_minute - 75):
                    continue
                if bars.minute[i] != minute - 1 or np.any(np.diff(bars.minute[i - 5 : i]) != 1):
                    continue
                previous = bars.close[i - 1]
                if previous < 1.08 * bars.close[i - 5]:
                    continue
                close = bars.close[j]
                if (
                    close >= max(previous, 1.01 * bars.close[i])
                    and close * bars.volume[j] >= 40_000
                ):
                    found.append(
                        Signal(symbol, minute, expire_minute=minute + 1, max_hold_minutes=60)
                    )
                    break
        return found


def build(params: dict) -> ResumptionMomentum:
    if params:
        raise ValueError("resumption_momentum accepts no parameters")
    return ResumptionMomentum()
