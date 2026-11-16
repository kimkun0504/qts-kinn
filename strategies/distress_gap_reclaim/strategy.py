"""Buy a positive opening gap after the first pullback in a beaten-down stock."""

import numpy as np

from kinn.core.types import Signal
from kinn.data.universe import Universe
from kinn.engine.intraday.data import DayView, SymbolDay
from kinn.engine.intraday.strategy import FeatureValues
from kinn.features import library as f


def reclaim_minute(view: DayView, bars: SymbolDay, prior_close: float) -> int | None:
    regular = (bars.minute >= view.open_minute) & (bars.minute < view.close_minute)
    minutes = bars.minute[regular]
    if not len(minutes) or minutes[0] != view.open_minute:
        return None
    opening = bars.open[regular][0]
    if not opening >= 1.10 * prior_close:
        return None

    closes = bars.close[regular]
    valid = np.isfinite(closes) & (closes > 0)
    lowest = np.fmin.accumulate(np.where(valid, closes, np.nan))[:-1]
    current = minutes[1:]
    latest = min(690, view.close_minute - 75)
    level = 1.01 * opening
    qualifies = (
        (current >= 575)
        & (current <= latest)
        & (np.diff(minutes) == 1)
        & (lowest <= 0.96 * opening)
        & (lowest >= prior_close)
        & valid[:-1]
        & valid[1:]
        & (closes[:-1] < level)
        & (closes[1:] >= level)
        & (closes[1:] * bars.volume[regular][1:] >= 40_000)
    )
    hits = np.flatnonzero(qualifies)
    return int(current[hits[0]]) if len(hits) else None


class DistressGapReclaim:
    name = "distress_gap_reclaim"
    universe = Universe(name, min_prev_close=3, min_adv20=2e6)
    features = (f.PREV_CLOSE, f.RET60)

    def signals(self, view: DayView, features: FeatureValues) -> list[Signal]:
        found = []
        for symbol, bars in view.symbols.items():
            prior = features[symbol]
            trend = prior[f.RET60.name]
            if not np.isfinite(trend) or trend > -0.50:
                continue
            minute = reclaim_minute(view, bars, prior[f.PREV_CLOSE.name])
            if minute is not None:
                found.append(Signal(symbol, minute, expire_minute=minute + 1, max_hold_minutes=60))
        return found


def build(params: dict) -> DistressGapReclaim:
    if params:
        raise ValueError("distress_gap_reclaim accepts no parameters")
    return DistressGapReclaim()
