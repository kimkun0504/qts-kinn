"""Buy a smaller stock still near its low as large-cap stocks recover."""

import numpy as np

from kinn.core.types import Signal
from kinn.data.universe import Universe
from kinn.engine.intraday.data import DayView, SymbolDay
from kinn.engine.intraday.strategy import FeatureValues
from kinn.features import library as f


def closing_prices(view: DayView, bars: SymbolDay) -> np.ndarray:
    prices = np.full(view.close_minute - view.open_minute, np.nan)
    observed = (
        (bars.minute >= view.open_minute)
        & (bars.minute < view.close_minute)
        & np.isfinite(bars.close)
        & (bars.close > 0)
    )
    prices[bars.minute[observed] - view.open_minute] = bars.close[observed]
    return prices


def recovering_market(peers: np.ndarray, candidate_offsets: np.ndarray) -> np.ndarray:
    start = peers[:, candidate_offsets - 45]
    low = peers[:, candidate_offsets - 15]
    current = peers[:, candidate_offsets]
    observed = np.isfinite(start) & np.isfinite(low) & np.isfinite(current)
    covered = observed.sum(axis=0) >= 30
    if not covered.any():
        return candidate_offsets[:0]
    included = observed[:, covered]
    selloff = np.where(included, low[:, covered] / start[:, covered] - 1, np.nan)
    recovery = np.where(included, current[:, covered] / low[:, covered] - 1, np.nan)
    turns = (np.nanmedian(selloff, axis=0) <= -0.015) & (np.nanmedian(recovery, axis=0) >= 0.0075)
    return candidate_offsets[covered][turns]


class MarketRecoveryLag:
    name = "market_recovery_lag"
    universe = Universe(name, min_prev_close=3, min_adv20=2e6)
    features = (f.ADV20, f.MARKETCAP)

    def signals(self, view: DayView, features: FeatureValues) -> list[Signal]:
        reference = []
        candidates = []
        for symbol, bars in view.symbols.items():
            cap = features[symbol][f.MARKETCAP.name]
            adv = features[symbol][f.ADV20.name]
            if cap >= 10e9 and adv >= 20e6:
                reference.append(closing_prices(view, bars))
            if 0 < cap < 2e9:
                candidates.append((symbol, bars))
        if len(reference) < 30:
            return []

        first = max(615, view.open_minute + 45)
        last = min(885, view.close_minute - 75)
        offsets = np.arange(first, last + 1) - view.open_minute
        offsets = recovering_market(np.stack(reference), offsets)
        if not len(offsets):
            return []

        found = []
        for symbol, bars in candidates:
            close = closing_prices(view, bars)
            start = close[offsets - 45]
            low = close[offsets - 15]
            current = close[offsets]
            rebound = current - low
            qualified = (
                (low <= 0.92 * start)
                & (rebound >= 0)
                & (rebound <= 0.25 * (start - low))
                & (current >= 1.01 * close[offsets - 1])
            )
            for instant in offsets[qualified]:
                minute = int(instant + view.open_minute)
                index = int(bars.minute.searchsorted(minute))
                if bars.close[index] * bars.volume[index] >= 40_000:
                    found.append(
                        Signal(symbol, minute, expire_minute=minute + 1, max_hold_minutes=60)
                    )
                    break
        return found


def build(params: dict) -> MarketRecoveryLag:
    if params:
        raise ValueError("market_recovery_lag accepts no parameters")
    return MarketRecoveryLag()
