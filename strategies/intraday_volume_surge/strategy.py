"""Buy a large regular-session gain confirmed by exceptionally high turnover."""

import numpy as np

from kinn.core.types import Signal
from kinn.data.universe import Universe
from kinn.engine.intraday.data import DayView
from kinn.engine.intraday.strategy import FeatureValues
from kinn.features import library as f


class IntradayVolumeSurge:
    name = "intraday_volume_surge"
    universe = Universe(name, min_prev_close=3, min_adv20=1_000_000, max_marketcap=2_000_000_000)
    features = (
        f.PREV_CLOSE,
        f.ADV20,
        f.SESSION_OPEN,
        f.CUM_DOLLAR_VOLUME,
        f.PREMARKET_DOLLAR_VOLUME,
    )

    def signals(self, view: DayView, features: FeatureValues) -> list[Signal]:
        signals = []
        for symbol, bars in view.symbols.items():
            opening = bars.minute.searchsorted(view.open_minute)
            if opening == len(bars.minute) or bars.minute[opening] != view.open_minute:
                continue
            values = features[symbol]
            open_price = values[f.SESSION_OPEN.name][opening]
            prior_close = values[f.PREV_CLOSE.name]
            if not 0.95 * prior_close <= open_price <= 1.05 * prior_close:
                continue

            above = bars.close >= 1.20 * open_price
            turnover = values[f.CUM_DOLLAR_VOLUME.name] - values[f.PREMARKET_DOLLAR_VOLUME.name]
            minute = bars.minute[1:]
            hits = np.flatnonzero(
                (minute >= 584)
                & (minute <= 719)
                & (np.diff(bars.minute) == 1)
                & above[:-1]
                & above[1:]
                & (turnover[1:] >= values[f.ADV20.name])
            )
            if len(hits):
                decision = int(minute[hits[0]])
                signals.append(Signal(symbol, decision, expire_minute=decision + 5))
        return signals


def build(params: dict) -> IntradayVolumeSurge:
    if params:
        raise ValueError("intraday_volume_surge accepts no parameters")
    return IntradayVolumeSurge()
