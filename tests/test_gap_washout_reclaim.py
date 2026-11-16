"""Verify that the VWAP reclaim can be observed and filled after its signal bar."""

from datetime import date

import pytest

from kinn import run as runner
from kinn.core.types import Signal
from kinn.costs.model import load
from kinn.engine.intraday.data import DayData, DayView, make_symbol_day
from kinn.engine.intraday.simulator import FillConfig, simulate_day
from kinn.engine.intraday.strategy import check_no_lookahead, day_signals
from kinn.risk.sizing import RiskConfig

NAME = "gap_washout_reclaim"
ROWS = [
    (550, 100.0, 100_000),
    (570, 12.0, 10_000),
    (580, 10.0, 1_000),
    (600, 10.5, 1_000),
    (601, 12.2, 1_000),
    (602, 12.5, 5_000),
    (603, 12.9, 10_000),
    (662, 11.5, 10_000),
    (663, 13.0, 10_000),
]
EXPECTED = [Signal("ABC", 602, expire_minute=603, max_hold_minutes=60)]


def session(rows=ROWS, *, prior_close=10.0, cap=200e6, close_minute=960):
    minutes, prices, volumes = zip(*rows, strict=True)
    stock = make_symbol_day(
        "ABC",
        1,
        minutes,
        prices,
        prices,
        prices,
        prices,
        volumes,
        {"marketcap_prev": cap, "prev_close": prior_close, "adv20_prev": 2e6},
    )
    return DayView(date(2016, 12, 2), 570, close_minute, {"ABC": stock})


def test_reclaim_ignores_premarket_and_passes_prefix_replay():
    strategy = runner.load_strategy(NAME, {})
    full = session()
    found = day_signals(strategy, full)
    assert found == EXPECTED
    assert day_signals(strategy, session(ROWS[1:])) == EXPECTED
    assert day_signals(strategy, full.upto(601)) == []
    assert day_signals(strategy, full.upto(602)) == EXPECTED
    check_no_lookahead(strategy, full, found, [549, 550, 570, 580, 600, 601, 602, 603, 663])


@pytest.mark.parametrize(
    "kwargs",
    [
        {"prior_close": 10.01},
        {"cap": 2e9},
        {"close_minute": 676},
        {"rows": [row for row in ROWS if row[0] != 570]},
        {"rows": [row for row in ROWS if row[0] != 601]},
        {"rows": [*ROWS[:2], (580, 11.0, 1_000), (600, 11.0, 1_000), *ROWS[4:]]},
        {"rows": [*ROWS[:5], (602, 12.5, 3_000), *ROWS[6:]]},
        {"rows": [*ROWS[:5], (602, 12.1, 5_000), *ROWS[6:]]},
    ],
)
def test_reclaim_requires_the_frozen_sequence(kwargs):
    assert day_signals(runner.load_strategy(NAME, {}), session(**kwargs)) == []


def test_reclaim_enters_next_minute_and_exits_after_one_hour():
    meta, config = runner.load_config(NAME, "development")
    strategy = runner.load_strategy(NAME, config["params"])
    view = session()
    trades = simulate_day(
        DayData(view, {"ABC": 15.0}),
        day_signals(strategy, view),
        risk=RiskConfig(**config["risk"]),
        config=FillConfig(**config["fills"]),
        costs=load(meta["cost_calibration"]),
    ).trades
    (trade,) = trades
    assert (trade.entry_minute, trade.exit_minute, trade.exit_reason) == (603, 663, "time")
    assert trade.exit_price == pytest.approx(13.0)


def test_validation_differs_only_in_the_date_range():
    _, development = runner.load_config(NAME, "development")
    _, validation = runner.load_config(NAME, "validation")
    assert development.pop("period") == {"start": date(2003, 9, 10), "end": date(2016, 12, 30)}
    assert validation.pop("period") == {"start": date(2017, 1, 3), "end": date(2023, 11, 8)}
    assert development == validation
