"""Buy the first opening rotation's recovery after a severe overnight decline."""

from kinn.core.types import Signal
from kinn.data.universe import Universe
from kinn.engine.intraday.data import DayView
from kinn.engine.intraday.strategy import FeatureValues
from kinn.features import library as f


class OpeningGapReclaim:
    name = "opening_gap_reclaim"
    universe = Universe(name, min_prev_close=5, min_adv20=2_000_000)
    features = (f.PREV_CLOSE, f.SESSION_OPEN, f.CUM_DOLLAR_VOLUME, f.PREMARKET_DOLLAR_VOLUME)

    def signals(self, view: DayView, features: FeatureValues) -> list[Signal]:
        decision_bar = view.open_minute + 14
        signals = []
        for symbol, bars in view.symbols.items():
            i = bars.minute.searchsorted(decision_bar)
            if i == len(bars.minute) or bars.minute[i] != decision_bar:
                continue
            opening = bars.minute.searchsorted(view.open_minute)
            if bars.minute[opening] != view.open_minute:
                continue
            values = features[symbol]
            prior = values[f.PREV_CLOSE.name]
            open_price = values[f.SESSION_OPEN.name][i]
            if not 0.60 * prior <= open_price <= 0.85 * prior:
                continue
            if not 1.03 * open_price <= bars.close[i] <= 0.92 * prior:
                continue
            turnover = (
                values[f.CUM_DOLLAR_VOLUME.name][i] - values[f.PREMARKET_DOLLAR_VOLUME.name][i]
            )
            if turnover >= 100_000:
                signals.append(Signal(symbol, decision_bar, expire_minute=decision_bar + 5))
        return signals


def build(params: dict) -> OpeningGapReclaim:
    if params:
        raise ValueError("opening_gap_reclaim accepts no parameters")
    return OpeningGapReclaim()
