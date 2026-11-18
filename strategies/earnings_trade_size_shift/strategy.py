"""Frozen trade-size expansion rule; pending the authorized transaction-count view."""

from math import isfinite

import numpy as np

from kinn.core.types import Signal
from kinn.data.universe import Universe
from kinn.engine.intraday.data import DayView
from kinn.engine.intraday.strategy import FeatureValues
from kinn.features.library import ADV20, PREV_CLOSE


def trade_size_expansion(volume: np.ndarray, transactions: np.ndarray) -> float | None:
    """Two five-minute windows; compare exact integer cross-products at the ratio gate."""
    v, n = np.asarray(volume), np.asarray(transactions)
    if v.shape != (10,) or n.shape != (10,):
        raise ValueError("trade-size expansion needs ten aligned bars")
    if not (
        np.isfinite(v)
        & (v > 0)
        & (v == np.floor(v))
        & np.isfinite(n)
        & (n > 0)
        & (n == np.floor(n))
    ).all():
        return None
    v1, v2 = sum(map(int, v[:5])), sum(map(int, v[5:]))
    n1, n2 = sum(map(int, n[:5])), sum(map(int, n[5:]))
    if n1 < 100 or n2 < 100 or n2 < n1 or v2 * n1 < 2 * v1 * n2:
        return None
    return (v2 * n1) / (v1 * n2)


def candidate_score(
    prices: np.ndarray, volume: np.ndarray, transactions: np.ndarray, previous: float, adv: float
) -> float | None:
    p, v, n = np.asarray(prices), np.asarray(volume), np.asarray(transactions)
    if p.shape != (11,) or v.shape != (11,) or n.shape != (11,):
        raise ValueError("candidate needs eleven aligned bars including the opening reference")
    if (
        not isfinite(previous)
        or previous <= 0
        or not isfinite(adv)
        or adv <= 0
        or not (np.isfinite(p) & (p > 0) & np.isfinite(v) & (v > 0)).all()
    ):
        return None
    if (
        p[0] < np.nextafter(1.05 * previous, -np.inf)
        or p[-1] < np.nextafter(1.03 * p[0], -np.inf)
        or np.sum(p[6:] * v[6:]) < 0.10 * adv
        or p[-1] * v[-1] < 40_000
    ):
        return None
    return trade_size_expansion(v[1:], n[1:])


class EarningsTradeSizeShift:
    name = "earnings_trade_size_shift"
    universe = Universe(
        name,
        min_prev_close=2,
        min_adv20=2e6,
        min_marketcap=50e6,
        max_marketcap=2e9,
        min_sessions_prior=20,
    )
    features = (PREV_CLOSE, ADV20)
    inputs = {"form8k": {"sessions": 1}}

    def signals(self, view: DayView, features: FeatureValues) -> list[Signal]:
        if view.open_minute != 570 or view.close_minute != 960:
            return []
        found = []
        wanted = np.arange(570, 581)
        for symbol, bars in view.symbols.items():
            earnings = any(
                r.earnings
                and r.filed < view.day
                and r.symbol == symbol
                and r.permaticker == bars.permaticker
                for r in view.reports.get(symbol, ())
            )
            if not earnings:
                continue
            indices = np.searchsorted(bars.minute, wanted)
            if np.any(indices >= len(bars.minute)) or not np.array_equal(
                bars.minute[indices], wanted
            ):
                continue
            counts = getattr(bars, "transactions", None)
            if counts is None:
                raise ValueError("earnings_trade_size_shift requires observed transaction counts")
            if np.shape(counts) != bars.minute.shape:
                raise ValueError("transaction counts are not aligned with minute bars")
            prior = features[symbol]
            score = candidate_score(
                bars.close[indices],
                bars.volume[indices],
                counts[indices],
                prior[PREV_CLOSE.name],
                prior[ADV20.name],
            )
            if score is not None:
                found.append(
                    Signal(
                        symbol,
                        580,
                        limit_price=1.005 * float(bars.close[indices[-1]]),
                        expire_minute=581,
                        max_hold_minutes=120,
                    )
                )
        return found


def build(params: dict) -> EarningsTradeSizeShift:
    if params:
        raise ValueError("earnings_trade_size_shift accepts no parameters")
    return EarningsTradeSizeShift()
