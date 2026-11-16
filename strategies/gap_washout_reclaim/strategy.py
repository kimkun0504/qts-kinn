"""Buy a sustained VWAP reclaim after a large opening gap unwinds."""

import numpy as np

from kinn.core.types import Signal
from kinn.data.universe import Universe
from kinn.engine.intraday.data import DayView, SymbolDay
from kinn.engine.intraday.strategy import FeatureValues
from kinn.features import library as f


def reclaim_minute(view: DayView, bars: SymbolDay, prior_close: float) -> int | None:
    regular = (bars.minute >= view.open_minute) & (bars.minute < view.close_minute)
    minutes = bars.minute[regular]
    if len(minutes) < 3 or minutes[0] != view.open_minute:
        return None

    opening_price = bars.open[regular][0]
    if not opening_price >= 1.2 * prior_close:
        return None

    close = bars.close[regular]
    volume = bars.volume[regular]
    turnover = close * volume
    cumulative_volume = np.cumsum(volume)
    vwap = np.divide(
        np.cumsum(turnover),
        cumulative_volume,
        out=np.full(len(close), np.nan),
        where=cumulative_volume > 0,
    )

    current = minutes[2:]
    latest = min(885, view.close_minute - 75)
    within_window = (current >= 600) & (current <= latest)
    consecutive = (current - minutes[1:-1] == 1) & (minutes[1:-1] - minutes[:-2] == 1)
    washed_out = np.minimum.accumulate(close)[:-2] <= 0.90 * opening_price
    reclaimed = (
        (close[:-2] < vwap[:-2])
        & (close[1:-1] > vwap[1:-1])
        & (close[2:] > vwap[2:])
        & (close[2:] > close[1:-1])
    )
    hits = np.flatnonzero(
        within_window & consecutive & washed_out & reclaimed & (turnover[2:] >= 40_000)
    )
    return int(current[hits[0]]) if len(hits) else None


class GapWashoutReclaim:
    name = "gap_washout_reclaim"
    universe = Universe(name, min_prev_close=2, min_adv20=1_000_000)
    features = (f.PREV_CLOSE, f.MARKETCAP)

    def signals(self, view: DayView, features: FeatureValues) -> list[Signal]:
        found = []
        for symbol, bars in view.symbols.items():
            prior = features[symbol]
            cap = prior[f.MARKETCAP.name]
            prior_close = prior[f.PREV_CLOSE.name]
            if cap is None or not 0 < cap < 2e9 or prior_close is None or prior_close <= 0:
                continue
            minute = reclaim_minute(view, bars, prior_close)
            if minute is not None:
                found.append(Signal(symbol, minute, expire_minute=minute + 1, max_hold_minutes=60))
        return found


def build(params: dict) -> GapWashoutReclaim:
    if params:
        raise ValueError("gap_washout_reclaim accepts no parameters")
    return GapWashoutReclaim()
