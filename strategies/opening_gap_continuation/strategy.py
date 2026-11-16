"""Buy a large opening gap confirmed by the first 15 minutes of trading."""

from __future__ import annotations

from kinn.core.types import Signal
from kinn.data.universe import Universe
from kinn.engine.intraday.data import DayView
from kinn.engine.intraday.strategy import FeatureValues
from kinn.features import library as f


class OpeningGapContinuation:
    name = "opening_gap_continuation"
    universe = Universe(name, min_prev_close=5, min_adv20=2_000_000)
    features = (f.PREV_CLOSE, f.SESSION_OPEN, f.CUM_DOLLAR_VOLUME, f.PREMARKET_DOLLAR_VOLUME)

    def signals(self, view: DayView, features: FeatureValues) -> list[Signal]:
        confirmation_minute = view.open_minute + 14
        out = []
        for symbol, sd in view.symbols.items():
            opening = sd.minute.searchsorted(view.open_minute)
            confirmation = sd.minute.searchsorted(confirmation_minute)
            if confirmation == len(sd.minute):
                continue
            if (
                sd.minute[opening] != view.open_minute
                or sd.minute[confirmation] != confirmation_minute
            ):
                continue

            values = features[symbol]
            prior_close = values[f.PREV_CLOSE.name]
            open_price = values[f.SESSION_OPEN.name][confirmation]
            if not 1.05 * prior_close <= open_price <= 1.25 * prior_close:
                continue
            turnover = (
                values[f.CUM_DOLLAR_VOLUME.name][confirmation]
                - values[f.PREMARKET_DOLLAR_VOLUME.name][confirmation]
            )
            if sd.close[confirmation] >= 1.01 * open_price and turnover >= 100_000:
                out.append(
                    Signal(symbol, confirmation_minute, expire_minute=confirmation_minute + 1)
                )
        return out


def build(params: dict) -> OpeningGapContinuation:
    if params:
        raise ValueError("opening_gap_continuation has one fixed variant and accepts no parameters")
    return OpeningGapContinuation()
