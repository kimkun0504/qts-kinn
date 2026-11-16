"""Verify the completed premarket reference, prefix replay and entry timing."""

from datetime import date

import pytest

from kinn import run as runner
from kinn.core.types import Signal
from kinn.costs.model import load
from kinn.engine.intraday.data import DayData, DayView, make_symbol_day
from kinn.engine.intraday.simulator import FillConfig, simulate_day
from kinn.engine.intraday.strategy import check_no_lookahead, day_signals
from kinn.risk.sizing import RiskConfig

NAME = "opening_premarket_discount"
PRE = [(540, 9.0, 4_000), (549, 10.0, 4_000), (556, 11.0, 4_000), (568, 10.0, 4_000)]
SIGNAL = [(570, 9.0, 20_000), (573, 9.05, 8_000), (574, 9.2, 8_000)]
FUTURE = [(575, 9.3, 8_000), (634, 10.8, 8_000), (635, 11.0, 8_000), (960, 120.0, 900_000)]
EXPECTED = [Signal("ABC", 574, expire_minute=575, max_hold_minutes=60)]


def session(rows, close_minute=960):
    minutes, prices, sizes = zip(*rows, strict=True)
    stock = make_symbol_day("ABC", 1, minutes, prices, prices, prices, prices, sizes)
    return DayView(date(2016, 12, 2), 570, close_minute, {"ABC": stock})


def test_recovery_uses_only_the_fixed_premarket_window_and_passes_replay():
    strategy = runner.load_strategy(NAME, {})
    full = session([(535, 1.0, 900_000), *PRE, *SIGNAL, *FUTURE])
    found = day_signals(strategy, full)
    assert found == EXPECTED
    assert day_signals(strategy, full.upto(573)) == []
    assert day_signals(strategy, full.upto(574)) == EXPECTED
    check_no_lookahead(strategy, full, found, [535, 568, 570, 573, 574, 575, 635, 960])


@pytest.mark.parametrize(
    "rows",
    [
        [*PRE[1:], *SIGNAL],
        [*PRE[:3], (564, 10.0, 4_000), *SIGNAL],
        [(m, p, 2_000) for m, p, _ in PRE] + SIGNAL,
        [(540, 9.0, 80_000), *PRE[1:], *SIGNAL],
        [*PRE, *SIGNAL[1:]],
        [*PRE, (570, 9.25, 20_000), *SIGNAL[1:]],
        [*PRE, SIGNAL[0], (572, 9.05, 8_000), SIGNAL[-1]],
        [*PRE, *SIGNAL[:2], (574, 9.10, 8_000)],
        [*PRE, *SIGNAL[:2], (574, 9.50, 8_000)],
        [*PRE, *SIGNAL[:2], (574, 9.20, 4_000)],
    ],
)
def test_recovery_requires_a_fresh_weighted_reference_and_enough_discount(rows):
    assert day_signals(runner.load_strategy(NAME, {}), session(rows)) == []


def test_order_enters_next_minute_and_exits_intraday():
    meta, config = runner.load_config(NAME, "development")
    strategy = runner.load_strategy(NAME, config["params"])
    view = session([*PRE, *SIGNAL, *FUTURE])
    result = simulate_day(
        DayData(view, {"ABC": 13.0}),
        day_signals(strategy, view),
        risk=RiskConfig(**config["risk"]),
        config=FillConfig(**config["fills"]),
        costs=load(meta["cost_calibration"]),
    )
    (trade,) = result.trades
    assert (trade.entry_minute, trade.exit_minute, trade.exit_reason) == (575, 635, "time")


def test_validation_differs_only_in_dates():
    _, development = runner.load_config(NAME, "development")
    _, validation = runner.load_config(NAME, "validation")
    assert development.pop("period") == {"start": date(2003, 9, 10), "end": date(2016, 12, 30)}
    assert validation.pop("period") == {"start": date(2017, 1, 3), "end": date(2023, 11, 8)}
    assert development == validation
