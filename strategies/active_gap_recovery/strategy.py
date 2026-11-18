"""Trade only a frozen recovery after an observed gap in dense prior trading."""

from math import isfinite

import numpy as np

from kinn.core.types import Signal
from kinn.data.universe import Universe
from kinn.engine.intraday.data import DayView, SymbolDay
from kinn.engine.intraday.strategy import FeatureValues
from kinn.features.library import ADV20


def valid_observations(bars: SymbolDay, indices: np.ndarray) -> bool:
    """Observed positive integer activity and internally consistent positive OHLC."""
    if bars.transactions is None:
        raise ValueError("active_gap_recovery requires observed transaction counts")
    o, h, low, c, v, n = (
        getattr(bars, name)[indices]
        for name in ("open", "high", "low", "close", "volume", "transactions")
    )
    return bool(
        (
            np.isfinite(o)
            & np.isfinite(h)
            & np.isfinite(low)
            & np.isfinite(c)
            & (low > 0)
            & (low <= np.minimum(o, c))
            & (h >= np.maximum(o, c))
            & np.isfinite(v)
            & (v > 0)
            & (v == np.floor(v))
            & np.isfinite(n)
            & (n > 0)
            & (n == np.floor(n))
        ).all()
    )


def candidate_gaps(bars: SymbolDay, adv: float) -> list[tuple[int, int]]:
    """Return (last pre-gap minute, returning minute), using only their prefixes."""
    if bars.transactions is None:
        raise ValueError("active_gap_recovery requires observed transaction counts")
    if not isfinite(adv) or adv <= 0:
        return []
    opening_index = int(np.searchsorted(bars.minute, 570))
    if opening_index >= len(bars.minute) or bars.minute[opening_index] != 570:
        return []
    opening = bars.open[opening_index]
    if not isfinite(opening) or opening <= 0:
        return []
    gaps = np.flatnonzero((np.diff(bars.minute) >= 6) & (np.diff(bars.minute) <= 31)) + 1
    found = []
    for k in gaps:
        t, p = int(bars.minute[k]), int(bars.minute[k - 1])
        if not 586 <= t <= 870 or p - 9 < 570 or k < 10:
            continue
        before = np.arange(k - 10, k)
        if not np.array_equal(bars.minute[before], np.arange(p - 9, p + 1)):
            continue
        if not valid_observations(bars, np.r_[before, k]):
            continue
        previous = bars.close[k - 1]
        if (
            previous < np.nextafter(1.10 * opening, -np.inf)
            or bars.transactions[before].sum() < 1000
            or np.sum(bars.close[before] * bars.volume[before]) < max(200_000, 0.1 * adv)
            or previous * bars.volume[k - 1] < 40_000
            or bars.transactions[k] < 100
            or bars.close[k] * bars.volume[k] < 40_000
            or bars.open[k] > np.nextafter(0.95 * previous, np.inf)
            or bars.close[k] > np.nextafter(0.95 * previous, np.inf)
            or bars.close[k] < np.nextafter(1.01 * bars.open[k], -np.inf)
        ):
            continue
        found.append((p, t))
    return found


class ActiveGapRecovery:
    name = "active_gap_recovery"
    universe = Universe(
        name,
        min_prev_close=3,
        min_adv20=2e6,
        min_marketcap=50e6,
        max_marketcap=2e9,
        min_sessions_prior=20,
    )
    features = (ADV20,)

    def signals(self, view: DayView, features: FeatureValues) -> list[Signal]:
        if view.open_minute != 570 or view.close_minute != 960:
            return []
        candidates = {
            symbol: candidate_gaps(bars, features[symbol][ADV20.name])
            for symbol, bars in view.symbols.items()
        }
        wanted = {m for gaps in candidates.values() for p, t in gaps for m in range(p + 1, t)}
        if not wanted:
            return []
        # Count distinct *other companies*, using only observations at each missing minute.
        coverage = {m: set() for m in wanted}
        wanted_array = np.array(sorted(wanted))
        for bars in view.symbols.values():
            keep = (
                np.isin(bars.minute, wanted_array)
                & np.isfinite(bars.close)
                & (bars.close > 0)
                & np.isfinite(bars.volume)
                & (bars.volume > 0)
            )
            for minute in bars.minute[keep]:
                coverage[int(minute)].add(bars.permaticker)
        signals = []
        for symbol, gaps in candidates.items():
            company = view.symbols[symbol].permaticker
            for p, t in gaps:
                if all(len(coverage[m] - {company}) >= 10 for m in range(p + 1, t)):
                    signals.append(Signal(symbol, t, expire_minute=t + 1, max_hold_minutes=30))
                    break
        return signals


def build(params: dict) -> ActiveGapRecovery:
    if params:
        raise ValueError("active_gap_recovery has no tunable parameters")
    return ActiveGapRecovery()
