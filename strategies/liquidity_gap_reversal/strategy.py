"""Buy a partial recovery after a markdown on the first trade following a gap."""

import numpy as np

from kinn.core.types import Signal
from kinn.data.universe import Universe
from kinn.engine.intraday.data import DayView
from kinn.engine.intraday.strategy import FeatureValues


class LiquidityGapReversal:
    name = "liquidity_gap_reversal"
    universe = Universe(name, min_prev_close=2.0, min_adv20=1_000_000)
    features = ()

    def signals(self, view: DayView, features: FeatureValues) -> list[Signal]:
        found = []
        for symbol, bars in view.symbols.items():
            next_minute = bars.minute[1:]
            distance = np.diff(bars.minute)
            resumptions = (
                np.flatnonzero(
                    (distance >= 6)
                    & (distance <= 16)
                    & (next_minute >= 585)
                    & (next_minute <= 885)
                    & (next_minute < view.close_minute)
                )
                + 1
            )
            for i in resumptions:
                if i < 5 or bars.minute[i - 5] < view.open_minute:
                    continue
                block = slice(i - 5, i)
                if np.any(np.diff(bars.minute[block]) != 1):
                    continue
                reference = bars.close[i - 1]
                reopen = bars.open[i]
                if not (
                    0 < reopen <= 0.92 * reference
                    and 1.02 * reopen <= bars.close[i] <= 0.98 * reference
                ):
                    continue
                if np.dot(bars.close[block], bars.volume[block]) >= 100_000:
                    minute = int(bars.minute[i])
                    found.append(Signal(symbol, minute, expire_minute=minute + 1))
                    break
        return found


def build(params: dict) -> LiquidityGapReversal:
    if params:
        raise ValueError("liquidity_gap_reversal accepts no parameters")
    return LiquidityGapReversal()
