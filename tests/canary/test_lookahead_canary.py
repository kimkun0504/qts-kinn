"""Canary 1: a hidden next-bar feature must be caught.

If these tests ever pass a cheating feature or strategy, the main defence against lookahead
is broken and no result from the engine can be trusted.
"""

from datetime import date

import numpy as np
import pytest

from kinn.core.types import Signal
from kinn.data.universe import Universe
from kinn.engine.intraday.data import DayView, make_symbol_day
from kinn.engine.intraday.strategy import check_no_lookahead, day_signals
from kinn.features.base import Availability, Feature, LookaheadError, check_causal
from kinn.features.library import RETURN_FROM_PREV_CLOSE

DAY = date(2020, 1, 2)


def view():
    rng = np.random.default_rng(7)
    symbols = {}
    for k, name in enumerate(("AAA", "BBB", "CCC")):
        minutes = np.arange(570, 960)
        close = 10 + np.cumsum(rng.normal(0, 0.05, len(minutes)))
        symbols[name] = make_symbol_day(
            name,
            k,
            minutes,
            close,
            close + 0.02,
            close - 0.02,
            close,
            np.full(len(minutes), 1000),
            {"prev_close": 10.0},
        )
    return DayView(DAY, 570, 960, symbols)


def _next_bar_return(sd):
    out = np.full(len(sd.close), np.nan)
    out[:-1] = sd.close[1:] / sd.close[:-1] - 1  # value at bar i uses bar i + 1
    return out


PEEK = Feature("next_bar_return", Availability.BAR_CLOSE, _next_bar_return)


class Rule:
    """Buy when a feature is positive at a bar."""

    universe = Universe("all")

    def __init__(self, feature, stamp_offset=0):
        self.name = f"rule_{feature.name}"
        self.features = [feature]
        self._key = feature.name
        self._offset = stamp_offset

    def signals(self, day_view, features):
        out = []
        for symbol, sd in day_view.symbols.items():
            values = features[symbol][self._key]
            for i in np.flatnonzero(values > 0.004):
                out.append(Signal(symbol, int(sd.minute[i]) + self._offset))
        return out


CUTS = range(575, 955, 7)


def test_the_feature_check_catches_a_next_bar_feature():
    sd = view().symbols["AAA"]
    check_causal(RETURN_FROM_PREV_CLOSE, sd, CUTS)  # an honest feature passes
    with pytest.raises(LookaheadError, match="not causal"):
        check_causal(PEEK, sd, CUTS)


def test_the_engine_refuses_a_strategy_built_on_a_next_bar_feature():
    v = view()
    cheat = Rule(PEEK)
    signals = day_signals(cheat, v)
    assert signals, "the canary needs the cheat to produce signals"
    with pytest.raises(LookaheadError):
        check_no_lookahead(cheat, v, signals, CUTS)


def test_an_honest_strategy_passes_the_same_check():
    v = view()
    honest = Rule(RETURN_FROM_PREV_CLOSE)
    signals = day_signals(honest, v)
    assert signals
    check_no_lookahead(honest, v, signals, CUTS)


def test_a_signal_stamped_earlier_than_its_information_is_caught():
    v = view()
    backdated = Rule(RETURN_FROM_PREV_CLOSE, stamp_offset=-3)
    with pytest.raises(LookaheadError):
        check_no_lookahead(backdated, v, day_signals(backdated, v), CUTS)


def test_a_strategy_that_reads_the_days_low_directly_is_caught():
    class BuyTheLow:
        name, universe, features = "buy_the_low", Universe("all"), []

        def signals(self, day_view, features):
            return [
                Signal(s, int(sd.minute[np.argmin(sd.low)]))
                for s, sd in day_view.symbols.items()
                if len(sd.minute)
            ]

    v = view()
    cheat = BuyTheLow()
    with pytest.raises(LookaheadError):
        check_no_lookahead(cheat, v, day_signals(cheat, v), CUTS)
