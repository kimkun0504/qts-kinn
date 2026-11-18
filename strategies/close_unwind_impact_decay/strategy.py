"""First observed after-hours recovery as downside price impact diminishes."""

from kinn.core.types import Signal
from kinn.data.universe import Universe
from kinn.engine.intraday.data import DayView
from kinn.engine.intraday.strategy import FeatureValues
from kinn.features.library import PREV_CLOSE
from strategies.close_unwind_impact_decay.formula import first_candidate


class CloseUnwindImpactDecay:
    name = "close_unwind_impact_decay"
    universe = Universe(
        name,
        min_prev_close=2,
        min_adv20=2e6,
        min_marketcap=50e6,
        max_marketcap=2e9,
        min_sessions_prior=20,
    )
    features = (PREV_CLOSE,)

    def signals(self, view: DayView, features: FeatureValues) -> list[Signal]:
        found = []
        for symbol, bars in view.symbols.items():
            candidate = first_candidate(bars, features[symbol][PREV_CLOSE.name], view.close_minute)
            if candidate is not None:
                minute, _ = candidate
                i = int(bars.minute.searchsorted(minute))
                found.append(
                    Signal(
                        symbol,
                        minute,
                        limit_price=float(bars.close[i]) * 1.005,
                        expire_minute=minute + 1,
                        max_hold_minutes=15,
                    )
                )
        return found


def build(params: dict) -> CloseUnwindImpactDecay:
    if params:
        raise ValueError("close_unwind_impact_decay accepts no parameters")
    return CloseUnwindImpactDecay()
