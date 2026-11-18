"""Count acceleration and shrinking average print size at one frozen morning time."""

from math import isfinite

import numpy as np

from kinn.core.types import Signal
from kinn.data.universe import Universe
from kinn.engine.intraday.data import DayView
from kinn.engine.intraday.strategy import FeatureValues
from kinn.features.library import ADV20, MARKETCAP, PREV_CLOSE


def base_event(prices, volume, transactions, adv: float) -> tuple[float, bool] | None:
    """Return the recent/prior average-size ratio and primary eligibility."""
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
    v1, v2 = sum(map(int, v[1:6])), sum(map(int, v[6:]))
    n1, n2 = sum(map(int, n[1:6])), sum(map(int, n[6:]))
    if (
        n1 < 100
        or n2 < 4 * n1
        or p[-1] < np.nextafter(1.02 * p[5], -np.inf)
        or p[-1] > np.nextafter(1.05 * p[5], np.inf)
        or np.sum(p[6:] * v[6:]) < 0.1 * adv
        or p[-1] * v[-1] < 40_000
    ):
        return None
    return (v2 * n1) / (v1 * n2), 2 * v2 * n1 <= v1 * n2


class FragmentedDemandBurst:
    name = "fragmented_demand_burst"
    universe = Universe(
        name,
        min_prev_close=3,
        min_adv20=2e6,
        min_marketcap=50e6,
        max_marketcap=300e6,
        min_sessions_prior=20,
    )
    features = (ADV20, MARKETCAP, PREV_CLOSE)

    def __init__(self, fragmented: bool):
        self.fragmented = fragmented

    def signals(self, view: DayView, features: FeatureValues) -> list[Signal]:
        if view.open_minute != 570 or view.close_minute != 960:
            return []
        found = []
        wanted = np.arange(579, 590)
        for symbol, bars in view.symbols.items():
            prior = features[symbol]
            cap, price = prior[MARKETCAP.name], prior[PREV_CLOSE.name]
            if not (isfinite(cap) and cap > 0 and isfinite(price) and price > 0):
                continue
            if cap > 20e6 * price:
                continue
            indices = np.searchsorted(bars.minute, wanted)
            if np.any(indices >= len(bars.minute)) or not np.array_equal(
                bars.minute[indices], wanted
            ):
                continue
            if bars.transactions is None:
                raise ValueError("fragmented_demand_burst requires observed transaction counts")
            event = base_event(
                bars.close[indices],
                bars.volume[indices],
                bars.transactions[indices],
                prior[ADV20.name],
            )
            if event is not None and (not self.fragmented or event[1]):
                found.append(Signal(symbol, 589, expire_minute=590, max_hold_minutes=60))
        return found


def build(params: dict) -> FragmentedDemandBurst:
    if set(params) - {"fragmented"} or type(params.get("fragmented", True)) is not bool:
        raise ValueError("only the frozen boolean fragmented parameter is supported")
    return FragmentedDemandBurst(params.get("fragmented", True))
