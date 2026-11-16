"""Buy an early recovery from a discount to that morning's premarket trades."""

import numpy as np

from kinn.core.types import Signal
from kinn.data.universe import Universe
from kinn.engine.intraday.data import DayView, SymbolDay
from kinn.engine.intraday.strategy import FeatureValues


def recovery_minute(view: DayView, bars: SymbolDay) -> int | None:
    minutes = bars.minute
    opening = int(minutes.searchsorted(view.open_minute))
    if opening == len(minutes) or minutes[opening] != view.open_minute:
        return None
    start = int(minutes.searchsorted(540))
    price = bars.close[start:opening]
    volume = bars.volume[start:opening]
    valid = np.isfinite(price) & (price > 0) & (volume > 0)
    observed = minutes[start:opening][valid]
    if len(observed) < 4 or observed[-1] < 565:
        return None
    total = np.dot(price[valid], volume[valid])
    if total < 100_000:
        return None
    reference = total / volume[valid].sum()
    if not bars.open[opening] <= 0.92 * reference:
        return None

    earliest = int(minutes.searchsorted(574))
    latest = min(599, view.close_minute - 75)
    end = int(minutes.searchsorted(latest, side="right"))
    if earliest >= end:
        return None
    close = bars.close[earliest:end]
    prior = bars.close[earliest - 1 : end - 1]
    current = minutes[earliest:end]
    previous = minutes[earliest - 1 : end - 1]
    hits = np.flatnonzero(
        (current - previous == 1)
        & np.isfinite(prior)
        & (prior > 0)
        & (close >= 1.01 * prior)
        & (close <= 0.94 * reference)
        & (close * bars.volume[earliest:end] >= 40_000)
    )
    return int(current[hits[0]]) if len(hits) else None


class OpeningPremarketDiscount:
    name = "opening_premarket_discount"
    universe = Universe(name, min_prev_close=3, min_adv20=1_000_000)
    features = ()

    def signals(self, view: DayView, features: FeatureValues) -> list[Signal]:
        found = []
        for symbol, bars in view.symbols.items():
            minute = recovery_minute(view, bars)
            if minute is not None:
                found.append(Signal(symbol, minute, expire_minute=minute + 1, max_hold_minutes=60))
        return found


def build(params: dict) -> OpeningPremarketDiscount:
    if params:
        raise ValueError("opening_premarket_discount accepts no parameters")
    return OpeningPremarketDiscount()
