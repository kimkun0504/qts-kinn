"""Verify the surge, pullback and next-bar fill sequence."""

from datetime import date

import pytest

from kinn import run as runner
from kinn.core.types import Signal
from kinn.costs.model import load
from kinn.engine.intraday.data import DayData, DayView, make_symbol_day
from kinn.engine.intraday.simulator import FillConfig, simulate_day
from kinn.engine.intraday.strategy import check_no_lookahead, day_signals
from kinn.risk.sizing import RiskConfig

NAME = "volume_surge_pullback"
SETUP = [(570, 10.0, 20_000), (583, 12.0, 35_000), (584, 12.2, 40_000)]
PULLBACK = [(590, 14.0, 7_000), (591, 12.3, 7_000), (592, 12.5, 7_000)]
FUTURE = [(593, 12.6, 8_000), (652, 13.0, 8_000), (653, 13.1, 8_000), (910, 60.0, 1_000)]
EXPECTED = [Signal("ABC", 592, expire_minute=593, max_hold_minutes=60)]


def session(rows, *, prior_close=10, adv=1e6, cap=400e6, close=960):
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
        {"marketcap_prev": cap, "prev_close": prior_close, "adv20_prev": adv},
    )
    return DayView(date(2016, 12, 2), 570, close, {"ABC": stock})


def test_pullback_requires_the_completed_surge_and_passes_lookahead_replay():
    strategy = runner.load_strategy(NAME, {})
    full = session([*SETUP, *PULLBACK, *FUTURE])
    found = day_signals(strategy, full)
    assert found == EXPECTED
    assert day_signals(strategy, full.upto(591)) == []
    assert day_signals(strategy, full.upto(592)) == EXPECTED
    check_no_lookahead(strategy, full, found, [570, 583, 584, 590, 591, 592, 593, 653, 910])


@pytest.mark.parametrize(
    ("rows", "params"),
    [
        ([*SETUP, *PULLBACK], {"prior_close": 9.0}),
        ([*SETUP, *PULLBACK], {"cap": 2e9}),
        ([*SETUP, *PULLBACK], {"close": 666}),
        ([*SETUP[1:], *PULLBACK], {}),
        ([SETUP[0], SETUP[-1], *PULLBACK], {}),
        ([(550, 15.0, 100_000), *SETUP[:2], (584, 12.2, 30_000), *PULLBACK], {}),
        ([*SETUP, PULLBACK[0], PULLBACK[-1]], {}),
        ([*SETUP, *PULLBACK[:2], (592, 12.4, 7_000)], {}),
        ([*SETUP, *PULLBACK[:2], (592, 13.0, 7_000)], {}),
        ([*SETUP, *PULLBACK[:2], (592, 12.5, 3_000)], {}),
        ([*SETUP, (585, 9.8, 7_000), (586, 9.95, 7_000)], {}),
    ],
)
def test_pullback_rejects_incomplete_or_late_setups(rows, params):
    assert day_signals(runner.load_strategy(NAME, {}), session(rows, **params)) == []


def test_pullback_enters_next_bar_and_exits_in_one_hour():
    meta, config = runner.load_config(NAME, "development")
    strategy = runner.load_strategy(NAME, config["params"])
    view = session([*SETUP, *PULLBACK, *FUTURE])
    result = simulate_day(
        DayData(view, {"ABC": 13.5}),
        day_signals(strategy, view),
        risk=RiskConfig(**config["risk"]),
        config=FillConfig(**config["fills"]),
        costs=load(meta["cost_calibration"]),
    )
    (trade,) = result.trades
    assert (trade.entry_minute, trade.exit_minute, trade.exit_reason) == (593, 653, "time")


def test_configs_differ_only_in_dates():
    _, development = runner.load_config(NAME, "development")
    _, validation = runner.load_config(NAME, "validation")
    assert development.pop("period") == {"start": date(2003, 9, 10), "end": date(2016, 12, 30)}
    assert validation.pop("period") == {"start": date(2017, 1, 3), "end": date(2023, 11, 8)}
    assert development == validation
