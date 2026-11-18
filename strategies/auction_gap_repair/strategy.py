"""Opening recovery below an active, contemporaneous premarket price reference."""

from math import isfinite

import numpy as np

from kinn.core.types import Signal
from kinn.data.universe import Universe
from kinn.engine.intraday.data import DayView, SymbolDay
from kinn.engine.intraday.strategy import FeatureValues
from kinn.features.library import ADV20, PREV_CLOSE


def weighted_median(prices: np.ndarray, volume: np.ndarray) -> float:
    """Lower median price by observed share volume, with no interpolation."""
    p, v = np.asarray(prices, dtype=float), np.asarray(volume, dtype=float)
    if p.ndim != 1 or p.shape != v.shape or not len(p):
        raise ValueError("weighted median needs matching nonempty one-dimensional arrays")
    if not (np.isfinite(p) & (p > 0) & np.isfinite(v) & (v > 0)).all():
        raise ValueError("weighted median needs positive finite prices and volumes")
    order = np.argsort(p, kind="stable")
    cumulative = np.cumsum(v[order])
    index = int(np.searchsorted(cumulative, cumulative[-1] / 2, side="left"))
    return float(p[order[index]])


def premarket_reference(bars: SymbolDay, previous: float, adv: float) -> float | None:
    if not isfinite(previous) or previous <= 0 or not isfinite(adv) or adv <= 0:
        return None
    valid = (
        (bars.minute >= 540)
        & (bars.minute < 570)
        & np.isfinite(bars.close)
        & (bars.close > 0)
        & (bars.volume > 0)
    )
    indices = np.flatnonzero(valid)
    if len(indices) < 15 or bars.minute[indices[-1]] != 569:
        return None
    prices, volume = bars.close[indices], bars.volume[indices]
    if float(np.sum(prices * volume)) < max(250_000, 0.10 * adv):
        return None
    median = weighted_median(prices, volume)
    if (
        median < np.nextafter(1.15 * previous, -np.inf)
        or prices[-1] < np.nextafter(0.98 * median, -np.inf)
        or prices[-1] > np.nextafter(1.02 * median, np.inf)
        or prices[-1] * volume[-1] < 20_000
    ):
        return None
    return median


class AuctionGapRepair:
    name = "auction_gap_repair"
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
        if view.open_minute != 570 or view.close_minute != 960:
            return []
        found = []
        for symbol, bars in view.symbols.items():
            i = int(bars.minute.searchsorted(570))
            if i >= len(bars.minute) or bars.minute[i] != 570:
                continue
            prior = features[symbol]
            median = premarket_reference(bars, prior[PREV_CLOSE.name], prior[ADV20.name])
            if median is None:
                continue
            open_, close, volume = float(bars.open[i]), float(bars.close[i]), int(bars.volume[i])
            if (
                not isfinite(open_)
                or not isfinite(close)
                or min(open_, close) <= 0
                or volume <= 0
                or open_ > np.nextafter(0.90 * median, np.inf)
                or close < np.nextafter(1.01 * open_, -np.inf)
                or close > np.nextafter(0.95 * median, np.inf)
                or close * volume < 40_000
            ):
                continue
            found.append(
                Signal(
                    symbol, 570, limit_price=1.005 * close, expire_minute=571, max_hold_minutes=30
                )
            )
        return found


def build(params: dict) -> AuctionGapRepair:
    if params:
        raise ValueError("auction_gap_repair accepts no parameters")
    return AuctionGapRepair()
