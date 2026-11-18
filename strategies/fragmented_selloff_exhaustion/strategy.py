"""First shock-recovery event, optionally filtered by print-size fragmentation."""

from math import isfinite, log

import numpy as np

from kinn.core.types import Signal
from kinn.data.universe import Universe
from kinn.engine.intraday.data import DayView
from kinn.engine.intraday.strategy import FeatureValues
from kinn.features.library import ADV20


def base_event(prices, volume, transactions, adv: float) -> tuple[float, bool] | None:
    """Return (impact-decay score, fragmentation eligibility) at one completed window."""
    p, v, n = np.asarray(prices), np.asarray(volume), np.asarray(transactions)
    if p.shape != (16,) or v.shape != (16,) or n.shape != (16,):
        raise ValueError("base event requires sixteen aligned bars")
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
    if (
        p[10] > np.nextafter(0.90 * p[0], np.inf)
        or p[-1] > np.nextafter(0.92 * p[0], np.inf)
        or p[-1] < np.nextafter(1.01 * p[-2], -np.inf)
        or p[-1] * v[-1] < 40_000
    ):
        return None
    q1, q2 = float(np.sum(p[1:11] * v[1:11])), float(np.sum(p[11:] * v[11:]))
    if not isfinite(q1 + q2) or q1 < 0.10 * adv or q2 < np.nextafter(0.25 * q1, -np.inf):
        return None
    v1, v2 = sum(map(int, v[1:11])), sum(map(int, v[11:]))
    n1, n2 = sum(map(int, n[1:11])), sum(map(int, n[11:]))
    if n1 < 200 or n2 < 100:
        return None
    j1 = log(float(p[0] / p[10])) / n1
    j2 = max(0, log(float(p[10] / p[-1]))) / n2
    score = (1 - float(p[-1] / p[0])) * max(0, 1 - j2 / j1)
    if score < np.nextafter(0.06, -np.inf):
        return None
    fragmented = 4 * n2 >= 3 * n1 and 2 * v2 * n1 <= v1 * n2
    return score, fragmented


class FragmentedSelloffExhaustion:
    name = "fragmented_selloff_exhaustion"
    universe = Universe(
        name,
        min_prev_close=3,
        min_adv20=2e6,
        min_marketcap=50e6,
        max_marketcap=10e9,
        min_sessions_prior=20,
    )
    features = (ADV20,)

    def __init__(self, fragmented: bool):
        self.fragmented = fragmented

    def signals(self, view: DayView, features: FeatureValues) -> list[Signal]:
        if view.open_minute != 570 or view.close_minute != 960:
            return []
        found = []
        for symbol, bars in view.symbols.items():
            if len(bars.minute) < 16:
                continue
            if bars.transactions is None:
                raise ValueError("fragmented_selloff_exhaustion requires observed transactions")
            eligible = np.flatnonzero((bars.minute >= 600) & (bars.minute <= 825))
            eligible = eligible[eligible >= 15]
            # Price-only prefilter; all count, activity and continuity gates follow below.
            hits = eligible[
                (bars.close[eligible - 5] <= np.nextafter(0.90 * bars.close[eligible - 15], np.inf))
                & (bars.close[eligible] <= np.nextafter(0.92 * bars.close[eligible - 15], np.inf))
                & (bars.close[eligible] >= np.nextafter(1.01 * bars.close[eligible - 1], -np.inf))
            ]
            for i in hits:
                a = int(i) - 15
                b = int(i) + 1
                if not (np.diff(bars.minute[a:b]) == 1).all():
                    continue
                event = base_event(
                    bars.close[a:b],
                    bars.volume[a:b],
                    bars.transactions[a:b],
                    features[symbol][ADV20.name],
                )
                if event is None:
                    continue
                if not self.fragmented or event[1]:
                    minute = int(bars.minute[i])
                    found.append(
                        Signal(symbol, minute, expire_minute=minute + 1, max_hold_minutes=120)
                    )
                # The primary can never rescue a rejected first base event with a later one.
                break
        return found


def build(params: dict) -> FragmentedSelloffExhaustion:
    if set(params) - {"fragmented"} or type(params.get("fragmented", True)) is not bool:
        raise ValueError("only the frozen boolean fragmented parameter is supported")
    return FragmentedSelloffExhaustion(params.get("fragmented", True))
