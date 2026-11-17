"""Buy an early recovery after a decline spread across the morning."""

import numpy as np

from kinn.core.types import Signal
from kinn.data.universe import Universe
from kinn.engine.intraday.data import DayView, SymbolDay
from kinn.engine.intraday.strategy import FeatureValues
from kinn.features.library import PREV_CLOSE

CHECKPOINT_OFFSETS = np.array([0, 14, 29, 44, 59, 74, 89, 94])


def confirms_selloff(bars: SymbolDay, checkpoints: np.ndarray, prior_close: float) -> bool:
    indices = bars.minute.searchsorted(checkpoints)
    if indices[-1] == len(bars.minute) or not np.array_equal(bars.minute[indices], checkpoints):
        return False

    opened = bars.open[indices[0]]
    if not 0.95 * prior_close <= opened <= 1.05 * prior_close:
        return False
    prices = np.r_[opened, bars.close[indices[1:]]]
    if not (np.isfinite(prices) & (prices > 0)).all():
        return False
    end_of_selloff, decision_close = prices[-2:]
    if (
        end_of_selloff > 0.90 * opened
        or decision_close < 1.01 * end_of_selloff
        or decision_close * bars.volume[indices[-1]] < 40_000
    ):
        return False

    declines = -np.diff(prices[:-1])
    total_decline = opened - end_of_selloff
    return bool(np.count_nonzero(declines > 0) >= 4 and declines.max() <= 0.50 * total_decline)


class DistributedMorningSelloff:
    name = "distributed_morning_selloff"
    universe = Universe(
        name, min_prev_close=3, min_adv20=1e6, min_marketcap=50e6, max_marketcap=10e9
    )
    features = (PREV_CLOSE,)

    def signals(self, view: DayView, features: FeatureValues) -> list[Signal]:
        checkpoints = CHECKPOINT_OFFSETS + view.open_minute
        decision = int(checkpoints[-1])
        return [
            Signal(symbol, decision, expire_minute=decision + 1)
            for symbol, bars in view.symbols.items()
            if confirms_selloff(bars, checkpoints, features[symbol][PREV_CLOSE.name])
        ]


def build(params: dict) -> DistributedMorningSelloff:
    if params:
        raise ValueError("distributed_morning_selloff accepts no parameters")
    return DistributedMorningSelloff()
