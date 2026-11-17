"""Buy a delayed advance after several previously weak small caps rally early."""

from math import isfinite

import numpy as np

from kinn.core.types import Signal
from kinn.data.universe import Universe
from kinn.engine.intraday.data import DayView, SymbolDay
from kinn.engine.intraday.strategy import FeatureValues
from kinn.features.library import ADV20, PREV_CLOSE, RET60


def turnover(bars: SymbolDay, first: int, last: int) -> float:
    closes = bars.close[first:last]
    shares = bars.volume[first:last]
    valid = np.isfinite(closes) & (closes > 0) & (shares > 0)
    return float(closes[valid] @ shares[valid])


def confirms_laggard(bars: SymbolDay, early: int, decision: int, adv: float) -> bool:
    last = int(bars.minute.searchsorted(decision))
    if last < early + 2 or last >= len(bars.minute):
        return False
    if bars.minute[last - 1] != decision - 1 or bars.minute[last] != decision:
        return False
    anchor = bars.close[early]
    closing = bars.close[last - 1 : last + 1]
    return bool(
        ((closing >= 1.04 * anchor) & (closing <= 1.10 * anchor)).all()
        and closing[-1] * bars.volume[last] >= 40_000
        and turnover(bars, early + 1, last + 1) >= 0.12 * adv
    )


class SmallCapAttentionRotation:
    name = "small_cap_attention_rotation"
    universe = Universe(
        name,
        min_prev_close=2,
        min_adv20=1e6,
        min_marketcap=50e6,
        max_marketcap=2e9,
        min_sessions_prior=60,
    )
    features = (PREV_CLOSE, ADV20, RET60)

    def signals(self, view: DayView, features: FeatureValues) -> list[Signal]:
        early_minute = view.open_minute + 29
        decision = early_minute + 15
        if view.close_minute - decision < 75:
            return []

        leaders: set[int] = set()
        laggards: list[tuple[SymbolDay, int, float]] = []
        for symbol, bars in view.symbols.items():
            prior = features[symbol]
            trend = prior[RET60.name]
            if trend is None or not isfinite(trend) or trend > -0.20:
                continue
            opening = int(bars.minute.searchsorted(view.open_minute))
            early = int(bars.minute.searchsorted(early_minute))
            if early <= opening or early >= len(bars.minute):
                continue
            if bars.minute[opening] != view.open_minute or bars.minute[early] != early_minute:
                continue
            opened = bars.open[opening]
            first_close = bars.close[early]
            if not (isfinite(opened) and opened > 0 and isfinite(first_close) and first_close > 0):
                continue

            adv = prior[ADV20.name]
            if first_close >= 1.10 * opened and turnover(bars, opening, early + 1) >= 0.50 * adv:
                leaders.add(bars.permaticker)
            previous = prior[PREV_CLOSE.name]
            if 0.95 * previous <= opened <= 1.05 * previous and (
                0.98 * opened <= first_close <= 1.02 * opened
            ):
                laggards.append((bars, early, adv))

        if len(leaders) < 3:
            return []
        return [
            Signal(bars.symbol, decision, expire_minute=decision + 1, max_hold_minutes=60)
            for bars, early, adv in laggards
            if bars.permaticker not in leaders and confirms_laggard(bars, early, decision, adv)
        ]


def build(params: dict) -> SmallCapAttentionRotation:
    if params:
        raise ValueError("small_cap_attention_rotation accepts no parameters")
    return SmallCapAttentionRotation()
