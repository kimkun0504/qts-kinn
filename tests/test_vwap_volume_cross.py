"""Check the turnover control, completed-block replay and one-hour trade."""

from datetime import date

import pytest

from kinn import run as runner
from kinn.core.types import Signal
from kinn.costs.model import load
from kinn.engine.intraday.data import DayData, DayView, make_symbol_day
from kinn.engine.intraday.simulator import FillConfig, simulate_day
from kinn.engine.intraday.strategy import check_no_lookahead, day_signals
from kinn.risk.sizing import RiskConfig

NAME = "vwap_volume_cross"
DAY = date(2016, 12, 2)
HISTORY = [(minute, 20.0, 5_000) for minute in range(574, 599, 5)] + [(599, 19.8, 5_000)]
CROSS = (604, 20.7, 20_000)
CONFIRM = (609, 20.4, 5_000)
EXPECTED = [Signal("ABC", 609, expire_minute=610, max_hold_minutes=60)]


def session(rows=(*HISTORY, CROSS, CONFIRM), *, close_minute=960):
    minutes, prices, sizes = zip(*rows, strict=True)
    stock = make_symbol_day(
        "ABC", 1, minutes, prices, prices, prices, prices, sizes, {"adv20_prev": 2e6}
    )
    return DayView(DAY, 570, close_minute, {"ABC": stock})


def strategy(group):
    return runner.load_strategy(NAME, {"turnover_group": group})


def test_surge_cross_waits_for_a_completed_confirmation_and_passes_replay():
    view = session(
        [(569, 40.0, 1_000_000), *HISTORY, CROSS, CONFIRM, (610, 20.5, 9_000), (700, 25.0, 900_000)]
    )
    tested = strategy("surge")
    assert day_signals(tested, view.upto(608)) == []
    found = day_signals(tested, view)
    assert found == EXPECTED
    assert day_signals(strategy("ordinary"), view) == []
    check_no_lookahead(tested, view, found, [569, 599, 604, 608, 609, 610, 700])


def test_ordinary_control_and_no_later_cross_selection():
    view = session(
        [
            *HISTORY,
            (604, 20.7, 6_000),
            CONFIRM,
            (614, 19.6, 5_000),
            (619, 21.3, 30_000),
            (624, 21.2, 5_000),
        ]
    )
    assert day_signals(strategy("ordinary"), view) == EXPECTED
    assert day_signals(strategy("surge"), view) == []


@pytest.mark.parametrize(
    "rows",
    [
        [*HISTORY[:-1], (598, 19.8, 5_000), CROSS, CONFIRM],
        [*HISTORY[:-1], (599, 20.2, 5_000), CROSS, CONFIRM],
        [*HISTORY, (603, 20.7, 20_000), CONFIRM],
        [*HISTORY, (604, 20.2, 20_000), CONFIRM],
        [*HISTORY, CROSS, (608, 20.4, 8_000)],
        [*HISTORY, CROSS, (609, 19.9, 5_000)],
        [*HISTORY, CROSS, (609, 20.4, 1_000)],
        [*HISTORY[-2:], CROSS, CONFIRM],
        [(minute + 240, price, size) for minute, price, size in (*HISTORY, CROSS, CONFIRM)],
    ],
)
def test_cross_requires_valid_clock_blocks_and_positive_baseline(rows):
    for group in ("surge", "ordinary"):
        assert day_signals(strategy(group), session(rows)) == []


def test_requires_time_left_to_hold():
    assert day_signals(strategy("surge"), session(close_minute=683)) == []


@pytest.mark.parametrize("entry", [610, 611])
def test_next_minute_expiry_and_same_session_exit(entry):
    meta, config = runner.load_config(NAME, "development")
    tested = strategy("surge")
    view = session([*HISTORY, CROSS, CONFIRM, (entry, 20.5, 9_000), (670, 22.0, 9_000)])
    trades = simulate_day(
        DayData(view, {"ABC": 23.0}),
        day_signals(tested, view),
        risk=RiskConfig(**config["risk"]),
        config=FillConfig(**config["fills"]),
        costs=load(meta["cost_calibration"]),
    ).trades
    if entry == 610:
        (trade,) = trades
        assert (trade.entry_minute, trade.exit_minute, trade.exit_reason) == (610, 670, "time")
    else:
        assert trades == []


def test_only_turnover_group_and_dates_differ_across_configs():
    _, dev = runner.load_config(NAME, "development")
    _, ordinary = runner.load_config(NAME, "development_ordinary")
    _, validation = runner.load_config(NAME, "validation")
    assert dev["period"] == {"start": date(2003, 9, 10), "end": date(2016, 12, 30)}
    assert validation["period"] == {"start": date(2017, 1, 3), "end": date(2023, 11, 8)}
    assert ordinary == {**dev, "params": {"turnover_group": "ordinary"}}
    assert validation == {**dev, "period": validation["period"]}
