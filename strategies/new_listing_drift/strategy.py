"""Test high-turnover continuation in the first ten observed stock sessions."""

from datetime import date

from kinn.core.types import Signal
from kinn.data.universe import Universe
from kinn.engine.intraday.data import DayView
from kinn.engine.intraday.strategy import FeatureValues
from kinn.features import library as f

FIRST_SIGNAL_DATE = date(2003, 11, 3)


class NewlyObservedUniverse(Universe):
    def where(self) -> str:
        return f"({super().where()}) and sessions_prior <= 9"


class NewListingDrift:
    name = "new_listing_drift"
    universe = NewlyObservedUniverse(
        name, min_prev_close=5, min_adv20=5_000_000, min_sessions_prior=1
    )
    features = (
        f.PREV_CLOSE,
        f.SESSION_OPEN,
        f.ADV20,
        f.CUM_DOLLAR_VOLUME,
        f.PREMARKET_DOLLAR_VOLUME,
    )

    def signals(self, view: DayView, features: FeatureValues) -> list[Signal]:
        if view.day < FIRST_SIGNAL_DATE:
            return []

        decision = view.open_minute + 29
        found = []
        for symbol, bars in view.symbols.items():
            i = bars.minute.searchsorted(decision)
            if i == len(bars.minute) or bars.minute[i] != decision:
                continue
            opening = bars.minute.searchsorted(view.open_minute)
            if bars.minute[opening] != view.open_minute:
                continue
            values = features[symbol]
            prior = values[f.PREV_CLOSE.name]
            open_price = values[f.SESSION_OPEN.name][i]
            if not 0.95 * prior <= open_price <= 1.05 * prior:
                continue
            traded_dollars = (
                values[f.CUM_DOLLAR_VOLUME.name][i] - values[f.PREMARKET_DOLLAR_VOLUME.name][i]
            )
            if bars.close[i] >= 1.06 * open_price and traded_dollars >= 0.25 * values[f.ADV20.name]:
                found.append(Signal(symbol, decision, expire_minute=decision + 1))
        return found


def build(params: dict) -> NewListingDrift:
    if params:
        raise ValueError("new_listing_drift accepts no parameters")
    return NewListingDrift()
