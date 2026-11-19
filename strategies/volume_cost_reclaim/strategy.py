"""First relative-price event with one volume-weighted bar-high reference condition."""

from math import fsum, isfinite

import numpy as np

from kinn.core.types import Signal
from kinn.data.universe import Universe
from kinn.engine.intraday.data import DayView, SymbolDay
from kinn.engine.intraday.strategy import FeatureValues
from kinn.features.library import ADV20, MARKETCAP


def prices_in_session(view: DayView, bars: SymbolDay) -> np.ndarray:
    prices = np.full(view.close_minute - view.open_minute, np.nan)
    good = (bars.minute >= view.open_minute) & (bars.minute < view.close_minute)
    good &= np.isfinite(bars.close) & (bars.close > 0)
    prices[bars.minute[good] - view.open_minute] = bars.close[good]
    return prices


def lag_return(prices: np.ndarray, lag: int) -> np.ndarray:
    result = np.full_like(prices, np.nan)
    np.divide(
        prices[..., lag:], prices[..., :-lag], out=result[..., lag:], where=prices[..., :-lag] > 0
    )
    return result - 1


def peer_references(group: list[np.ndarray]):
    if len(group) < 31:
        return None
    matrix = np.stack(group)
    refs = []
    for lag in (15, 1):
        changes = lag_return(matrix, lag)
        valid = np.isfinite(changes).sum(axis=0) >= 31
        median = np.full(matrix.shape[1], np.nan)
        median[valid] = np.nanmedian(changes[:, valid], axis=0)
        refs.append(median)
    return tuple(refs)


def reference_terms(bars: SymbolDay, minute: int) -> tuple[float, int] | None:
    """Validate sixteen consecutive OHLCV bars, then use only the fourteen interior bars."""
    end = int(np.searchsorted(bars.minute, minute))
    start = end - 15
    if start < 0 or not np.array_equal(
        bars.minute[start : end + 1], np.arange(minute - 15, minute + 1)
    ):
        return None
    open_, high, low, close, volume = (
        getattr(bars, field)[start : end + 1]
        for field in ("open", "high", "low", "close", "volume")
    )
    if not all(np.all(np.isfinite(x) & (x > 0)) for x in (open_, high, low, close, volume)):
        return None
    if not (
        np.all(high >= np.maximum(open_, close))
        and np.all(low <= np.minimum(open_, close))
        and np.all(high >= low)
        and np.all(volume == np.floor(volume))
    ):
        return None
    shares = sum(int(v) for v in volume[1:-1])
    try:
        weighted_high = fsum(
            float(h) * int(v) for h, v in zip(high[1:-1], volume[1:-1], strict=True)
        )
    except OverflowError:
        return None
    return (weighted_high, shares) if isfinite(weighted_high) else None


def above_reference(close: float, weighted_high: float, shares: int) -> bool:
    product = close * shares
    return isfinite(product) and product >= np.nextafter(weighted_high, -np.inf)


class VolumeCostReclaim:
    name = "volume_cost_reclaim"
    universe = Universe(name, min_prev_close=2, min_adv20=10e6)
    features = (MARKETCAP, ADV20)

    def __init__(self, require_reference: bool):
        self.require_reference = require_reference

    def signals(self, view: DayView, features: FeatureValues) -> list[Signal]:
        groups: list[list[np.ndarray]] = [[], []]
        candidates = []
        for symbol, bars in view.symbols.items():
            cap = features[symbol][MARKETCAP.name]
            if 0 < cap < 10e9 and features[symbol][ADV20.name] >= 10e6:
                group = int(cap >= 2e9)
                prices = prices_in_session(view, bars)
                groups[group].append(prices)
                candidates.append((symbol, bars, group, prices))
        refs = [peer_references(g) for g in groups]
        found = []
        for symbol, bars, group, prices in candidates:
            if refs[group] is None:
                continue
            market15, market1 = refs[group]
            valid = (bars.minute >= 590) & (bars.minute <= 885) & (bars.minute < view.close_minute)
            minutes = bars.minute[valid]
            indices = minutes - view.open_minute
            r15, r1 = lag_return(prices, 15), lag_return(prices, 1)
            hits = np.flatnonzero(
                (r15[indices] - market15[indices] <= np.nextafter(-0.08, np.inf))
                & (prices[indices] >= np.nextafter(1.01 * prices[indices - 1], -np.inf))
                & (r1[indices] - market1[indices] >= np.nextafter(0.01, -np.inf))
                & (prices[indices] * bars.volume[valid] >= 40_000)
            )
            if not len(hits):
                continue
            hit = int(hits[0])
            minute = int(minutes[hit])
            terms = reference_terms(bars, minute)
            if terms is None or (
                self.require_reference and not above_reference(prices[indices[hit]], *terms)
            ):
                continue
            found.append(Signal(symbol, minute, expire_minute=minute + 1, max_hold_minutes=120))
        return found


def build(params: dict) -> VolumeCostReclaim:
    if (
        set(params) - {"require_reference"}
        or type(params.get("require_reference", True)) is not bool
    ):
        raise ValueError("only the frozen boolean require_reference is supported")
    return VolumeCostReclaim(params.get("require_reference", True))
