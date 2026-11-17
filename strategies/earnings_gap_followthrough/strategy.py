"""Buy an opening gap that extends after a public earnings disclosure."""

from math import isfinite

import numpy as np

from kinn.core.types import Signal
from kinn.data.universe import Universe
from kinn.engine.intraday.data import DayView, SymbolDay
from kinn.engine.intraday.strategy import FeatureValues
from kinn.features import library as f


def confirms_earnings_gap(view: DayView, bars: SymbolDay, prior_close: float, adv: float) -> bool:
    opening = int(bars.minute.searchsorted(view.open_minute))
    decision = view.open_minute + 14
    last = int(bars.minute.searchsorted(decision))
    if last <= opening or last >= len(bars.minute):
        return False
    if (
        bars.minute[opening] != view.open_minute
        or bars.minute[last - 1] != decision - 1
        or bars.minute[last] != decision
    ):
        return False

    price = bars.open[opening]
    if not isfinite(price) or not isfinite(prior_close) or not 0 < prior_close <= price / 1.10:
        return False
    confirmation = bars.close[last - 1 : last + 1]
    if not (np.isfinite(confirmation) & (confirmation >= 1.01 * price)).all():
        return False

    close = bars.close[opening : last + 1]
    volume = bars.volume[opening : last + 1]
    turnover = np.zeros(len(close))
    np.multiply(close, volume, out=turnover, where=np.isfinite(close) & (close > 0))
    return turnover[-1] >= 40_000 and turnover.sum() >= 0.25 * adv


class EarningsGapFollowThrough:
    name = "earnings_gap_followthrough"
    universe = Universe(
        name, min_prev_close=2, min_adv20=1e6, min_marketcap=50e6, max_marketcap=2e9
    )
    features = (f.PREV_CLOSE, f.ADV20)
    inputs = {"form8k": {"sessions": 1}}

    def signals(self, view: DayView, features: FeatureValues) -> list[Signal]:
        decision = view.open_minute + 14
        found = []
        for symbol, reports in view.reports.items():
            bars = view.symbols[symbol]
            disclosed = any(
                report.earnings
                and report.filed < view.day
                and report.symbol == symbol
                and report.permaticker == bars.permaticker
                for report in reports
            )
            if not disclosed:
                continue
            prior = features[symbol]
            if confirms_earnings_gap(view, bars, prior[f.PREV_CLOSE.name], prior[f.ADV20.name]):
                found.append(Signal(symbol, decision, expire_minute=decision + 1))
        return found


def build(params: dict) -> EarningsGapFollowThrough:
    if params:
        raise ValueError("earnings_gap_followthrough accepts no parameters")
    return EarningsGapFollowThrough()
