"""Buy after a fast decline stabilizes with continued high turnover."""

import numpy as np

from kinn.core.types import Signal
from kinn.data.universe import Universe
from kinn.engine.intraday.data import DayView, SymbolDay
from kinn.engine.intraday.strategy import FeatureValues
from kinn.features.library import ADV20


def stabilization_minute(view: DayView, bars: SymbolDay, adv: float) -> int | None:
    first = int(bars.minute.searchsorted(view.open_minute))
    last_minute = min(14 * 60 + 45, view.close_minute - 75)
    last = int(bars.minute.searchsorted(last_minute, side="right"))
    minute = bars.minute[first:last]
    close = bars.close[first:last]
    volume = bars.volume[first:last]
    if len(minute) < 21:
        return None

    candidates = np.flatnonzero(
        (minute[20:] >= view.open_minute + 20)
        & (minute[20:] - minute[:-20] == 20)
        & (close[15:-5] <= 0.90 * close[:-20])
    )
    for start in candidates:
        end = start + 21
        prices = close[start:end]
        shares = volume[start:end]
        if not (np.isfinite(prices) & (prices > 0) & (shares > 0)).all():
            continue
        if not (np.diff(minute[start:end]) == 1).all():
            continue

        turnover = prices[1:] * shares[1:]
        shock_turnover = turnover[:15].sum()
        base = prices[15]
        stable = prices[16:]
        stable_turnover = turnover[15:]
        stable_total = stable_turnover.sum()
        down_minutes = stable < prices[15:-1]
        if (
            shock_turnover >= 0.10 * adv
            and (stable >= 0.98 * base).all()
            and (stable <= 1.04 * base).all()
            and stable[-1] >= 1.01 * base
            and 6 * stable_total >= shock_turnover
            and 2 * stable_turnover[down_minutes].sum() >= stable_total
            and stable_turnover[-1] >= 40_000
        ):
            return int(minute[end - 1])
    return None


class HeavyTurnoverStabilization:
    name = "heavy_turnover_stabilization"
    universe = Universe(
        name, min_prev_close=3, min_adv20=2e6, min_marketcap=50e6, max_marketcap=10e9
    )
    features = (ADV20,)

    def signals(self, view: DayView, features: FeatureValues) -> list[Signal]:
        found = []
        for symbol, bars in view.symbols.items():
            minute = stabilization_minute(view, bars, features[symbol][ADV20.name])
            if minute is not None:
                found.append(Signal(symbol, minute, expire_minute=minute + 1, max_hold_minutes=60))
        return found


def build(params: dict) -> HeavyTurnoverStabilization:
    if params:
        raise ValueError("heavy_turnover_stabilization accepts no parameters")
    return HeavyTurnoverStabilization()
