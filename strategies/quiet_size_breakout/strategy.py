"""A fixed-time narrow-range breakout with a registered large-print ablation."""

from math import isfinite

import numpy as np

from kinn.core.types import Signal
from kinn.data.universe import Universe
from kinn.engine.intraday.data import DayView
from kinn.engine.intraday.strategy import FeatureValues
from kinn.features.library import ADV20


def base_event(prices, volume, transactions, adv: float) -> tuple[float, bool] | None:
    """Return (relative average print size, primary eligibility) for the fixed window."""
    p, v, n = np.asarray(prices), np.asarray(volume), np.asarray(transactions)
    if p.shape != (11,) or v.shape != (11,) or n.shape != (11,):
        raise ValueError("base event requires eleven aligned bars")
    if (
        not isfinite(adv)
        or adv <= 0
        or not (
            np.isfinite(p)
            & (p > 0)
            & np.isfinite(v)
            & (v > 0)
            & (v == np.floor(v))
            & np.isfinite(n)
            & (n > 0)
            & (n == np.floor(n))
        ).all()
    ):
        return None
    high, low = float(p[:10].max()), float(p[:10].min())
    if (
        high > np.nextafter(1.02 * low, np.inf)
        or p[-1] < np.nextafter(1.005 * high, -np.inf)
        or p[-1] > np.nextafter(1.03 * low, np.inf)
        or p[-1] * v[-1] < 40_000
        or np.sum(p[6:] * v[6:]) < max(100_000, 0.05 * adv)
    ):
        return None
    v1, v2 = sum(map(int, v[1:6])), sum(map(int, v[6:]))
    n1, n2 = sum(map(int, n[1:6])), sum(map(int, n[6:]))
    if n1 < 100 or n2 < 100:
        return None
    factor = (v2 * n1) / (v1 * n2)
    return factor, n2 >= n1 and v2 * n1 >= 2 * v1 * n2


class QuietSizeBreakout:
    name = "quiet_size_breakout"
    universe = Universe(
        name,
        min_prev_close=3,
        min_adv20=2e6,
        min_marketcap=50e6,
        max_marketcap=2e9,
        min_sessions_prior=20,
    )
    features = (ADV20,)

    def __init__(self, large_prints: bool):
        self.large_prints = large_prints

    def signals(self, view: DayView, features: FeatureValues) -> list[Signal]:
        if view.open_minute != 570 or view.close_minute != 960:
            return []
        found = []
        wanted = np.arange(589, 600)
        for symbol, bars in view.symbols.items():
            indices = np.searchsorted(bars.minute, wanted)
            if np.any(indices >= len(bars.minute)) or not np.array_equal(
                bars.minute[indices], wanted
            ):
                continue
            if bars.transactions is None:
                raise ValueError("quiet_size_breakout requires observed transaction counts")
            event = base_event(
                bars.close[indices],
                bars.volume[indices],
                bars.transactions[indices],
                features[symbol][ADV20.name],
            )
            if event is not None and (not self.large_prints or event[1]):
                found.append(Signal(symbol, 599, expire_minute=600, max_hold_minutes=120))
        return found


def build(params: dict) -> QuietSizeBreakout:
    if set(params) - {"large_prints"} or type(params.get("large_prints", True)) is not bool:
        raise ValueError("only the frozen boolean large_prints parameter is supported")
    return QuietSizeBreakout(params.get("large_prints", True))
