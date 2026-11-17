"""Buy a partial reversal of late selling in a stock that rallied earlier."""

import numpy as np

from kinn.core.types import RTH_CLOSE, RTH_OPEN, Signal
from kinn.data.universe import Universe
from kinn.engine.intraday.data import DayView, SymbolDay
from kinn.engine.intraday.strategy import FeatureValues

CHECKPOINTS = np.array([RTH_OPEN, 14 * 60 + 59, 15 * 60 + 19, 15 * 60 + 24])
DECISION_MINUTE = int(CHECKPOINTS[-1])


def confirms_recovery(bars: SymbolDay) -> bool:
    indices = bars.minute.searchsorted(CHECKPOINTS)
    if indices[-1] == len(bars.minute) or not np.array_equal(bars.minute[indices], CHECKPOINTS):
        return False

    opened = bars.open[indices[0]]
    rally, selloff, decision = bars.close[indices[1:]]
    prices = np.array([opened, rally, selloff, decision])
    return bool(
        (np.isfinite(prices) & (prices > 0)).all()
        and rally >= 1.10 * opened
        and selloff <= 0.94 * rally
        and 1.01 * selloff <= decision <= 0.97 * rally
        and decision * bars.volume[indices[-1]] >= 40_000
    )


class LateRallySelloff:
    name = "late_rally_selloff"
    universe = Universe(
        name, min_prev_close=2, min_adv20=1e6, min_marketcap=50e6, max_marketcap=2e9
    )
    features = ()

    def signals(self, view: DayView, features: FeatureValues) -> list[Signal]:
        if view.open_minute != RTH_OPEN or view.close_minute != RTH_CLOSE:
            return []
        return [
            Signal(symbol, DECISION_MINUTE, expire_minute=DECISION_MINUTE + 1)
            for symbol, bars in view.symbols.items()
            if confirms_recovery(bars)
        ]


def build(params: dict) -> LateRallySelloff:
    if params:
        raise ValueError("late_rally_selloff accepts no parameters")
    return LateRallySelloff()
