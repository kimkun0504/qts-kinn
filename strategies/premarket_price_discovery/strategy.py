"""One frozen premarket momentum score, using completed bars and prior-session liquidity."""

from math import isfinite, log

import numpy as np

from kinn.core.types import Signal
from kinn.data.universe import Universe
from kinn.engine.intraday.data import DayView, SymbolDay
from kinn.engine.intraday.strategy import FeatureValues
from kinn.features.library import ADV20, PREV_CLOSE


def discovery_score(prices: np.ndarray, volumes: np.ndarray) -> float | None:
    """Log price progress, discounted by path reversals and concentrated dollar turnover."""
    p, v = np.asarray(prices, dtype=float), np.asarray(volumes, dtype=float)
    if p.shape != (6,) or v.shape != (6,):
        raise ValueError("discovery score requires six completed bars")
    if not (np.isfinite(p) & (p > 0) & np.isfinite(v) & (v > 0)).all():
        return None
    changes = np.diff(np.log(p))
    progress, travel = float(changes.sum()), float(np.abs(changes).sum())
    if progress <= 0 or travel <= 0:
        return None
    q = p[1:] * v[1:]
    # Normalise before squaring to keep the concentration calculation bounded.
    weights = q / q.sum()
    breadth = 1 / (5 * float(np.square(weights).sum()))
    return progress * (progress / travel) * breadth


def first_candidate(bars: SymbolDay, prior_close: float, adv: float) -> tuple[int, float] | None:
    if not isfinite(prior_close) or prior_close <= 0 or not isfinite(adv) or adv <= 0:
        return None
    eligible = np.flatnonzero(
        (bars.minute >= 425) & (bars.minute <= 525) & (bars.close >= 1.15 * prior_close)
    )
    for end in eligible:
        if end < 5 or not (np.diff(bars.minute[end - 5 : end + 1]) == 1).all():
            continue
        prices, volume = bars.close[end - 5 : end + 1], bars.volume[end - 5 : end + 1]
        score = discovery_score(prices, volume)
        if score is None or score < log(1.05):
            continue
        turnover = prices[1:] * volume[1:]
        if (turnover >= 10_000).all() and turnover.sum() >= max(100_000, 0.05 * adv):
            return int(bars.minute[end]), score
    return None


class PremarketPriceDiscovery:
    name = "premarket_price_discovery"
    universe = Universe(
        name,
        min_prev_close=2,
        min_adv20=2e6,
        min_marketcap=50e6,
        max_marketcap=2e9,
        min_sessions_prior=20,
    )
    features = (PREV_CLOSE, ADV20)

    def signals(self, view: DayView, features: FeatureValues) -> list[Signal]:
        if view.close_minute != 960:
            return []
        signals = []
        for symbol, bars in view.symbols.items():
            prior = features[symbol]
            candidate = first_candidate(bars, prior[PREV_CLOSE.name], prior[ADV20.name])
            if candidate is not None:
                minute, _ = candidate
                i = int(bars.minute.searchsorted(minute))
                signals.append(
                    Signal(
                        symbol,
                        minute,
                        limit_price=float(bars.close[i]) * 1.01,
                        expire_minute=minute + 1,
                        max_hold_minutes=30,
                    )
                )
        return signals


def build(params: dict) -> PremarketPriceDiscovery:
    if params:
        raise ValueError("premarket_price_discovery accepts no parameters")
    return PremarketPriceDiscovery()
