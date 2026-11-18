"""First observed after-hours recovery as downside price impact diminishes."""

from math import isfinite, log

import numpy as np

from kinn.core.types import Signal
from kinn.data.universe import Universe
from kinn.engine.intraday.data import DayView, SymbolDay
from kinn.engine.intraday.strategy import FeatureValues
from kinn.features.library import PREV_CLOSE


def impact_decay_score(closes: np.ndarray, volumes: np.ndarray, reference: float) -> float | None:
    """Score one seven-minute window when its registered price and activity gates hold."""
    prices = np.asarray(closes, dtype=float)
    shares = np.asarray(volumes, dtype=float)
    if prices.shape != (7,) or shares.shape != (7,):
        raise ValueError("impact decay requires seven completed consecutive minute bars")
    if (
        not isfinite(reference)
        or reference <= 0
        or not (np.isfinite(prices) & (prices > 0)).all()
        or not (np.isfinite(shares) & (shares > 0)).all()
    ):
        return None

    discount = 1 - prices[-1] / reference
    # Allow one representable float of rounding at inclusive price boundaries.
    if (
        prices[3] > np.nextafter(0.97 * prices[0], np.inf)
        or prices[-1] > np.nextafter(0.92 * reference, np.inf)
        or prices[-1] < np.nextafter(prices[-2] + 0.01, -np.inf)
        or prices[-1] * shares[-1] < 20_000
    ):
        return None

    turnover = prices[1:] * shares[1:]
    falling = prices[1:] < prices[:-1]
    old_turnover = float(turnover[:3][falling[:3]].sum())
    new_turnover = float(turnover[3:][falling[3:]].sum())
    if (
        old_turnover <= 0
        or new_turnover <= 0
        or new_turnover < np.nextafter(0.5 * old_turnover, -np.inf)
    ):
        return None
    old_impact = log(prices[0] / prices[3]) / old_turnover
    new_impact = max(0, log(prices[3] / prices[-1])) / new_turnover
    return discount * max(0, 1 - new_impact / old_impact)


def first_candidate(
    bars: SymbolDay, prior_close: float, regular_close_minute: int
) -> tuple[int, float] | None:
    """Find the first qualifying completed after-hours bar and its impact-decay score."""
    if regular_close_minute != 960 or not isfinite(prior_close) or prior_close <= 0:
        return None
    last_regular = int(bars.minute.searchsorted(959))
    if last_regular == len(bars.minute) or bars.minute[last_regular] != 959:
        return None
    reference = bars.close[last_regular]
    regular_prices = bars.close[(bars.minute >= 570) & (bars.minute < 960)]
    regular_prices = regular_prices[np.isfinite(regular_prices) & (regular_prices > 0)]
    if (
        not isfinite(reference)
        or reference < 1.10 * prior_close
        or not len(regular_prices)
        or regular_prices.max() < 1.20 * prior_close
    ):
        return None

    eligible = np.flatnonzero((bars.minute >= 967) & (bars.minute <= 1020))
    for end in eligible:
        if end < 6 or not (np.diff(bars.minute[end - 6 : end + 1]) == 1).all():
            continue
        score = impact_decay_score(
            bars.close[end - 6 : end + 1], bars.volume[end - 6 : end + 1], reference
        )
        if score is not None and score >= 0.04:
            return int(bars.minute[end]), score
    return None


class CloseUnwindImpactDecay:
    name = "close_unwind_impact_decay"
    universe = Universe(
        name,
        min_prev_close=2,
        min_adv20=2e6,
        min_marketcap=50e6,
        max_marketcap=2e9,
        min_sessions_prior=20,
    )
    features = (PREV_CLOSE,)

    def signals(self, view: DayView, features: FeatureValues) -> list[Signal]:
        found = []
        for symbol, bars in view.symbols.items():
            candidate = first_candidate(bars, features[symbol][PREV_CLOSE.name], view.close_minute)
            if candidate is not None:
                minute, _ = candidate
                i = int(bars.minute.searchsorted(minute))
                found.append(
                    Signal(
                        symbol,
                        minute,
                        limit_price=float(bars.close[i]) * 1.005,
                        expire_minute=minute + 1,
                        max_hold_minutes=15,
                    )
                )
        return found


def build(params: dict) -> CloseUnwindImpactDecay:
    if params:
        raise ValueError("close_unwind_impact_decay accepts no parameters")
    return CloseUnwindImpactDecay()
