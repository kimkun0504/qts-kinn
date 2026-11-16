"""Buy a large first-hour gain after a near-flat open and a recent filing."""

from kinn.core.types import Signal
from kinn.data.universe import Universe
from kinn.engine.intraday.data import DayView
from kinn.engine.intraday.strategy import FeatureValues
from kinn.features import library as f


class FilingSessionMomentum:
    name = "filing_session_momentum"
    universe = Universe(name, min_prev_close=5, min_adv20=2_000_000)
    features = (
        f.FILINGS_SINCE_PRIOR_SESSION,
        f.PREV_CLOSE,
        f.SESSION_OPEN,
        f.CUM_DOLLAR_VOLUME,
        f.PREMARKET_DOLLAR_VOLUME,
    )

    def signals(self, view: DayView, features: FeatureValues) -> list[Signal]:
        decision_bar = view.open_minute + 59
        signals = []
        for symbol, bars in view.symbols.items():
            values = features[symbol]
            if not values[f.FILINGS_SINCE_PRIOR_SESSION.name] >= 1:
                continue
            i = bars.minute.searchsorted(decision_bar)
            if i == len(bars.minute) or bars.minute[i] != decision_bar:
                continue
            opening = bars.minute.searchsorted(view.open_minute)
            if bars.minute[opening] != view.open_minute:
                continue
            prior = values[f.PREV_CLOSE.name]
            open_price = values[f.SESSION_OPEN.name][i]
            if not 0.97 * prior <= open_price <= 1.03 * prior:
                continue
            turnover = (
                values[f.CUM_DOLLAR_VOLUME.name][i] - values[f.PREMARKET_DOLLAR_VOLUME.name][i]
            )
            if bars.close[i] >= 1.06 * open_price and turnover >= 200_000:
                signals.append(Signal(symbol, decision_bar, expire_minute=decision_bar + 5))
        return signals


def build(params: dict) -> FilingSessionMomentum:
    if params:
        raise ValueError("filing_session_momentum accepts no parameters")
    return FilingSessionMomentum()
