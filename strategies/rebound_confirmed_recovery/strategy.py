"""Enter the intraday rebound after a deep close and an observable recovery."""

from math import inf

import numpy as np

from kinn.core.types import Signal
from kinn.data.universe import Universe
from kinn.engine.intraday.data import DayView
from kinn.engine.intraday.strategy import FeatureValues
from kinn.features import library as f


class ReboundConfirmedRecovery:
    name = "rebound_confirmed_recovery"
    universe = Universe(name, min_prev_close=1.0, min_adv20=250_000, min_sessions_prior=20)
    features = (
        f.PREV_CLOSE,
        f.ADV20,
        f.SESSION_OPEN,
        f.PREMARKET_DOLLAR_VOLUME,
        f.FILINGS_SINCE_PRIOR_SESSION,
    )

    def signals(self, view: DayView, features: FeatureValues) -> list[Signal]:
        signals = []
        for symbol, bars in view.symbols.items():
            values = features[symbol]
            if values[f.FILINGS_SINCE_PRIOR_SESSION.name] != 0:
                continue
            prior = values[f.PREV_CLOSE.name]
            regular = (bars.minute >= view.open_minute) & (bars.minute < view.close_minute)
            crossed = np.flatnonzero(regular & (bars.close <= 0.90 * prior))
            if not len(crossed):
                continue
            event = int(crossed[0])
            minute = int(bars.minute[event])
            if not 575 <= minute <= 900:
                continue
            if values[f.SESSION_OPEN.name][event] < 0.95 * prior:
                continue
            if values[f.PREMARKET_DOLLAR_VOLUME.name][event] >= 0.05 * values[f.ADV20.name]:
                continue

            price = float(bars.close[event])
            reference = round(0.96 * price, 2 if price >= 1 else 4)
            last = min(minute + 10, view.close_minute - 1)
            end = int(bars.minute.searchsorted(last, side="right"))
            low_close = inf
            for i in range(event + 1, end):
                close = float(bars.close[i])
                if 1.01 * low_close <= close <= reference:
                    confirmation = int(bars.minute[i])
                    signals.append(Signal(symbol, confirmation, expire_minute=confirmation + 1))
                    break
                low_close = min(low_close, close)
        return signals


def build(params: dict) -> ReboundConfirmedRecovery:
    if params:
        raise ValueError("rebound_confirmed_recovery accepts no parameters")
    return ReboundConfirmedRecovery()
