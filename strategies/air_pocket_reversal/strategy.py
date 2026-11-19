"""Fixed relative-price event, then an ablation of transaction-rate collapse."""

import numpy as np

from kinn.core.types import Signal
from kinn.data.universe import Universe
from kinn.engine.intraday.data import DayView, SymbolDay
from kinn.engine.intraday.strategy import FeatureValues
from kinn.features.library import ADV20, MARKETCAP


def observed_prices(view: DayView, bars: SymbolDay) -> np.ndarray:
    values = np.full(view.close_minute - view.open_minute, np.nan)
    inside = (bars.minute >= view.open_minute) & (bars.minute < view.close_minute)
    positive = np.isfinite(bars.close) & (bars.close > 0)
    valid = inside & positive
    values[bars.minute[valid] - view.open_minute] = bars.close[valid]
    return values


def returns(prices: np.ndarray, lag: int) -> np.ndarray:
    values = np.full_like(prices, np.nan)
    np.divide(
        prices[..., lag:], prices[..., :-lag], out=values[..., lag:], where=prices[..., :-lag] > 0
    )
    return values - 1


def reference(prices: list[np.ndarray]) -> tuple[np.ndarray, np.ndarray] | None:
    if len(prices) < 31:
        return None
    matrix = np.stack(prices)
    medians = []
    for lag in (15, 1):
        changes = returns(matrix, lag)
        usable = np.isfinite(changes).sum(axis=0) >= 31
        median = np.full(matrix.shape[1], np.nan)
        median[usable] = np.nanmedian(changes[:, usable], axis=0)
        medians.append(median)
    return tuple(medians)


def activity_counts(bars: SymbolDay, minute: int) -> tuple[int, int] | None:
    """All thirty consecutive observed bars; no imputed inactivity or later rescue."""
    if bars.transactions is None:
        return None
    end = int(np.searchsorted(bars.minute, minute))
    start = end - 29
    if start < 0 or not np.array_equal(
        bars.minute[start : end + 1], np.arange(minute - 29, minute + 1)
    ):
        return None
    close = bars.close[start : end + 1]
    volume = bars.volume[start : end + 1]
    counts = bars.transactions[start : end + 1]
    for values in (close, volume, counts):
        if values.dtype.kind not in "iuf" or not np.all(np.isfinite(values) & (values > 0)):
            return None
    if not all(np.equal(values, np.floor(values)).all() for values in (volume, counts)):
        return None
    # Python integers preserve the cross-product inequality without fixed-width overflow.
    return sum(int(x) for x in counts[:15]), sum(int(x) for x in counts[15:29])


def collapsed(baseline: int, falling: int) -> bool:
    return 15 * falling <= 7 * baseline


class AirPocketReversal:
    name = "air_pocket_reversal"
    universe = Universe(name, min_prev_close=2, min_adv20=10e6)
    features = (MARKETCAP, ADV20)

    def __init__(self, require_collapse: bool):
        self.require_collapse = require_collapse

    def signals(self, view: DayView, features: FeatureValues) -> list[Signal]:
        groups: list[list[np.ndarray]] = [[], []]
        candidates = []
        for symbol, bars in view.symbols.items():
            cap = features[symbol][MARKETCAP.name]
            if 0 < cap < 10e9 and features[symbol][ADV20.name] >= 10e6:
                group = int(cap >= 2e9)
                prices = observed_prices(view, bars)
                groups[group].append(prices)
                candidates.append((symbol, bars, group, prices))
        references = [reference(prices) for prices in groups]
        signals = []
        for symbol, bars, group, prices in candidates:
            if references[group] is None:
                continue
            r15, r1 = returns(prices, 15), returns(prices, 1)
            market15, market1 = references[group]
            inside = (bars.minute >= 600) & (bars.minute <= 885) & (bars.minute < view.close_minute)
            minutes = bars.minute[inside]
            indices = minutes - view.open_minute
            hits = np.flatnonzero(
                (r15[indices] - market15[indices] <= np.nextafter(-0.12, np.inf))
                & (prices[indices] >= np.nextafter(1.01 * prices[indices - 1], -np.inf))
                & (r1[indices] - market1[indices] >= np.nextafter(0.01, -np.inf))
                & (prices[indices] * bars.volume[inside] >= 40_000)
            )
            if not len(hits):
                continue
            minute = int(minutes[hits[0]])
            activity = activity_counts(bars, minute)
            if activity is None or (self.require_collapse and not collapsed(*activity)):
                continue
            signals.append(Signal(symbol, minute, expire_minute=minute + 1, max_hold_minutes=120))
        return signals


def build(params: dict) -> AirPocketReversal:
    if set(params) - {"require_collapse"} or type(params.get("require_collapse", True)) is not bool:
        raise ValueError("only the frozen boolean require_collapse is supported")
    return AirPocketReversal(params.get("require_collapse", True))
