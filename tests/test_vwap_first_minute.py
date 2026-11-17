"""Verify first-minute VWAP entry and exact subset selection by volume."""

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
HISTORY = [(m, 20.0, 5_000) for m in range(570, 599)] + [(599, 19.99, 5_000)]
CROSS = (600, 20.10, 20_000)
EXPECTED = [Signal("ABC", 600, expire_minute=601, max_hold_minutes=60)]


def strategy(group):
    return runner.load_strategy(NAME, {"entry_mode": "immediate", "turnover_group": group})


def session(rows=(*HISTORY, CROSS), *, close_minute=960):
    minutes, prices, shares = zip(*rows, strict=True)
    bars = make_symbol_day(
        "ABC", 1, minutes, prices, prices, prices, prices, shares, {"adv20_prev": 2e6}
    )
    return DayView(DAY, 570, close_minute, {"ABC": bars})


def test_immediate_surge_is_a_subset_of_all_with_identical_signals_and_replays():
    view = session(
        [(550, 50, 1_000_000), *HISTORY, CROSS, (601, 20.15, 10_000), (660, 20.5, 10_000)]
    )
    for group in ("surge", "all"):
        tested = strategy(group)
        assert day_signals(tested, view.upto(599)) == []
        found = day_signals(tested, view)
        assert found == EXPECTED
        check_no_lookahead(tested, view, found, [550, 590, 599, 600, 601, 660])


def test_all_group_keeps_the_same_first_cross_even_when_later_cross_has_more_volume():
    view = session([*HISTORY, (600, 20.1, 3_000), (601, 19.9, 5_000), (602, 20.8, 40_000)])
    assert day_signals(strategy("all"), view) == EXPECTED
    assert day_signals(strategy("surge"), view) == []


def test_zero_baseline_cannot_be_replaced_by_later_cross():
    view = session(
        [
            (570, 20.0, 5_000),
            (599, 19.8, 5_000),
            CROSS,
            *[(m, 19.8, 5_000) for m in range(601, 630)],
            (630, 20.7, 20_000),
        ]
    )
    for group in ("all", "surge"):
        assert day_signals(strategy(group), view) == []


@pytest.mark.parametrize(
    "rows",
    [
        [*HISTORY[:-1], CROSS],
        [*HISTORY[:-1], (599, 20.1, 5_000), CROSS],
        [*HISTORY, (600, 19.8, 20_000)],
        [*[(m, 20.0, 5_000) for m in range(570, 600)], (600, 20.0, 20_000)],
        [*HISTORY, (600, 20.10, 1_000)],
        [*HISTORY, (600, float("nan"), 20_000)],
        [*HISTORY[:-1], (599, 19.99, 0), CROSS],
        [*HISTORY, (600, 20.10, 0)],
        [(m - 1, p, n) for m, p, n in (*HISTORY, CROSS)],
        [(m + 240, p, n) for m, p, n in (*HISTORY, CROSS)],
    ],
)
def test_requires_actual_crossover_and_executable_signal_time(rows):
    for group in ("all", "surge"):
        assert day_signals(strategy(group), session(rows)) == []


def test_respects_time_left_before_calendar_close():
    assert day_signals(strategy("surge"), session(close_minute=674)) == []


@pytest.mark.parametrize("entry", [601, 602])
def test_next_minute_expiry_and_one_hour_exit(entry):
    meta, config = runner.load_config(NAME, "development_immediate")
    tested = runner.load_strategy(NAME, config["params"])
    view = session([*HISTORY, CROSS, (entry, 20.15, 10_000), (661, 21, 10_000)])
    trades = simulate_day(
        DayData(view, {"ABC": 22.0}),
        day_signals(tested, view),
        risk=RiskConfig(**config["risk"]),
        config=FillConfig(**config["fills"]),
        costs=load(meta["cost_calibration"]),
    ).trades
    if entry == 601:
        (trade,) = trades
        assert (trade.entry_minute, trade.exit_minute, trade.exit_reason) == (601, 661, "time")
    else:
        assert trades == []


def test_configs_preserve_the_primary_and_only_add_a_volume_comparator():
    _, primary = runner.load_config(NAME, "development_immediate")
    _, all_crosses = runner.load_config(NAME, "development_immediate_all")
    _, validation = runner.load_config(NAME, "validation_immediate")
    assert primary["period"] == {"start": date(2003, 9, 10), "end": date(2016, 12, 30)}
    assert all_crosses == {
        **primary,
        "params": {"entry_mode": "immediate", "turnover_group": "all"},
    }
    assert validation["period"] == {"start": date(2017, 1, 3), "end": date(2023, 11, 8)}
    assert validation == {**primary, "period": validation["period"]}
