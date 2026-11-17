"""Buy a partial opening recovery after a disclosed unregistered equity sale."""

from datetime import date
from math import isfinite

import numpy as np

from kinn.core.types import Signal
from kinn.data.universe import Universe
from kinn.engine.intraday.data import DayView, SymbolDay
from kinn.engine.intraday.strategy import FeatureValues
from kinn.features.library import ADV20, PREV_CLOSE

ITEM_EFFECTIVE = date(2004, 8, 23)


def confirms_recovery(view: DayView, bars: SymbolDay, prior_close: float, adv: float) -> bool:
    opening = int(bars.minute.searchsorted(view.open_minute))
    decision = view.open_minute + 29
    last = int(bars.minute.searchsorted(decision))
    if last <= opening or last >= len(bars.minute):
        return False
    if (
        bars.minute[opening] != view.open_minute
        or bars.minute[last - 1] != decision - 1
        or bars.minute[last] != decision
    ):
        return False

    opened = bars.open[opening]
    if not isfinite(prior_close) or not 0.65 * prior_close <= opened <= 0.90 * prior_close:
        return False
    gap = prior_close - opened
    if gap <= 0:
        return False
    recovered = bars.close[last - 1 : last + 1] - opened
    if not ((0.25 * gap <= recovered) & (recovered <= 0.60 * gap)).all():
        return False

    close = bars.close[opening : last + 1]
    volume = bars.volume[opening : last + 1]
    turnover = np.zeros(len(close))
    np.multiply(close, volume, out=turnover, where=np.isfinite(close) & (close > 0) & (volume > 0))
    return turnover[-1] >= 40_000 and turnover.sum() >= 0.15 * adv


class EquitySaleGapReclaim:
    name = "equity_sale_gap_reclaim"
    universe = Universe(
        name, min_prev_close=2, min_adv20=1e6, min_marketcap=50e6, max_marketcap=2e9
    )
    features = (PREV_CLOSE, ADV20)
    inputs = {"form8k": {"sessions": 1}}

    def signals(self, view: DayView, features: FeatureValues) -> list[Signal]:
        decision = view.open_minute + 29
        found = []
        for symbol, reports in view.reports.items():
            bars = view.symbols[symbol]
            current = [
                report
                for report in reports
                if ITEM_EFFECTIVE <= report.filed < view.day
                and report.symbol == symbol
                and report.permaticker == bars.permaticker
            ]
            if not any("3.02" in report.items for report in current):
                continue
            if any(report.earnings for report in current):
                continue
            prior = features[symbol]
            if confirms_recovery(view, bars, prior[PREV_CLOSE.name], prior[ADV20.name]):
                found.append(Signal(symbol, decision, expire_minute=decision + 1))
        return found


def build(params: dict) -> EquitySaleGapReclaim:
    if params:
        raise ValueError("equity_sale_gap_reclaim accepts no parameters")
    return EquitySaleGapReclaim()
