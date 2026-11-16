"""Verify trend availability, opening pullback and next-bar execution."""

from datetime import date

import pytest

from kinn import run as runner
from kinn.core.types import Signal
from kinn.costs.model import load
from kinn.engine.intraday.data import DayData, DayView, make_symbol_day
from kinn.engine.intraday.simulator import FillConfig, simulate_day
from kinn.engine.intraday.strategy import check_no_lookahead, day_signals
from kinn.risk.sizing import RiskConfig

NAME = "distress_gap_reclaim"
OPEN = [(570, 11.0, 10_000), (571, 10.5, 10_000), (574, 10.6, 10_000), (575, 11.2, 10_000)]
LATER = [(576, 11.3, 10_000), (635, 11.5, 10_000), (636, 11.7, 10_000), (690, 4.0, 10_000)]
EXPECTED = [Signal("ABC", 575, expire_minute=576, max_hold_minutes=60)]


def session(rows=OPEN, *, prior_close=10.0, trend=-0.50, close_minute=960):
    minutes, prices, sizes = zip(*rows, strict=True)
    stock = make_symbol_day(
        "ABC",
        1,
        minutes,
        prices,
        prices,
        prices,
        prices,
        sizes,
        {"prev_close": prior_close, "ret60_prev": trend, "adv20_prev": 3e6},
    )
    return DayView(date(2016, 12, 2), 570, close_minute, {"ABC": stock})


def test_reclaim_uses_only_observed_regular_bars_and_prior_trend():
    strategy = runner.load_strategy(NAME, {})
    view = session([(565, 1.0, 900_000), *OPEN, *LATER])
    found = day_signals(strategy, view)
    assert found == EXPECTED
    assert day_signals(strategy, view.upto(574)) == []
    assert day_signals(strategy, view.upto(575)) == EXPECTED
    check_no_lookahead(strategy, view, found, [565, 570, 571, 574, 575, 576, 690])


@pytest.mark.parametrize(
    "kwargs",
    [
        {"trend": -0.49},
        {"trend": None},
        {"prior_close": 10.01},
        {"close_minute": 649},
        {"rows": OPEN[1:]},
        {"rows": [OPEN[0], (571, 9.9, 10_000), *OPEN[2:]]},
        {"rows": [OPEN[0], (571, 10.7, 10_000), (574, 10.7, 10_000), OPEN[-1]]},
        {"rows": [*OPEN[:2], OPEN[-1]]},
        {"rows": [*OPEN[:2], (574, 11.12, 10_000), OPEN[-1]]},
        {"rows": [*OPEN[:3], (575, 11.2, 3_000)]},
    ],
)
def test_reclaim_requires_both_retained_gap_and_confirmation(kwargs):
    assert day_signals(runner.load_strategy(NAME, {}), session(**kwargs)) == []


def test_order_enters_after_confirmation_and_exits_on_entry_clock():
    meta, config = runner.load_config(NAME, "development")
    strategy = runner.load_strategy(NAME, config["params"])
    view = session([*OPEN, *LATER])
    result = simulate_day(
        DayData(view, {"ABC": 12.0}),
        day_signals(strategy, view),
        risk=RiskConfig(**config["risk"]),
        config=FillConfig(**config["fills"]),
        costs=load(meta["cost_calibration"]),
    )
    (trade,) = result.trades
    assert (trade.entry_minute, trade.exit_minute, trade.exit_reason) == (576, 636, "time")


def test_validation_differs_only_in_dates():
    _, development = runner.load_config(NAME, "development")
    _, validation = runner.load_config(NAME, "validation")
    assert development.pop("period") == {"start": date(2003, 9, 10), "end": date(2016, 12, 30)}
    assert validation.pop("period") == {"start": date(2017, 1, 3), "end": date(2023, 11, 8)}
    assert development == validation
