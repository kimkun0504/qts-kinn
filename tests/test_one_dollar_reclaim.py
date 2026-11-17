"""Check the fixed reference, order timing and lookahead replay."""

from datetime import date

import pytest

from kinn import run as runner
from kinn.core.types import Signal
from kinn.costs.model import load
from kinn.engine.intraday.data import DayData, DayView, make_symbol_day
from kinn.engine.intraday.simulator import FillConfig, simulate_day
from kinn.engine.intraday.strategy import check_no_lookahead, day_signals
from kinn.risk.sizing import RiskConfig

NAME = "one_dollar_reclaim"
DAY = date(2016, 12, 2)
ROWS = [(570, 1.10, 30_000), (574, 0.96, 30_000), (575, 0.99, 30_000), (576, 1.03, 30_000)]
EXPECTED = [Signal("ABC", 576, expire_minute=577)]


def session(rows=ROWS, *, close_minute=960):
    minutes, prices, sizes = zip(*rows, strict=True)
    stock = make_symbol_day(
        "ABC", 1, minutes, prices, prices, prices, prices, sizes, {"adv20_prev": 1e6}
    )
    return DayView(DAY, 570, close_minute, {"ABC": stock})


def test_first_reclaim_requires_completed_regular_bars_and_passes_replay():
    strategy = runner.load_strategy(NAME, {"reference": 1.0})
    view = session(
        [
            (550, 0.8, 900_000),
            *ROWS,
            (577, 1.02, 60_000),
            (578, 0.95, 30_000),
            (579, 0.99, 30_000),
            (580, 1.04, 30_000),
            (950, 1.20, 50_000),
        ]
    )
    found = day_signals(strategy, view)
    assert found == EXPECTED
    assert day_signals(strategy, view.upto(575)) == []
    assert day_signals(strategy, view.upto(576)) == EXPECTED
    check_no_lookahead(strategy, view, found, [550, 574, 575, 576, 577, 580, 950])


@pytest.mark.parametrize(
    "rows",
    [
        ROWS[1:],
        [(570, 0.99, 30_000), *ROWS[1:]],
        [(570, 1.50, 30_000), *ROWS[1:]],
        [(550, 0.90, 30_000), ROWS[0], *ROWS[2:]],
        [*ROWS[:2], ROWS[-1]],
        [*ROWS[:2], (575, 1.0, 30_000), ROWS[-1]],
        [*ROWS[:-1], (576, 1.005, 30_000)],
        [*ROWS[:-1], (576, 1.09, 30_000)],
        [*ROWS[:-1], (576, 1.02, 10_000)],
        [*ROWS[:2], (604, 0.99, 30_000), (605, 1.03, 30_000)],
        [*ROWS[:2], (884, 0.96, 30_000), (885, 0.99, 30_000), (886, 1.03, 30_000)],
    ],
)
def test_requires_actual_crossing_and_recent_break_in_trade_window(rows):
    assert day_signals(runner.load_strategy(NAME, {"reference": 1.0}), session(rows)) == []


def test_same_proportions_and_universe_use_registered_comparison_level():
    strategy = runner.load_strategy(NAME, {"reference": 1.2})
    assert strategy.universe.min_prev_close == 1.2
    assert strategy.universe.max_prev_close == pytest.approx(1.8)
    assert day_signals(strategy, session()) == []
    scaled = [(m, p * 1.2, n) for m, p, n in ROWS]
    assert day_signals(strategy, session(scaled)) == EXPECTED


@pytest.mark.parametrize("entry", [577, 578])
def test_simulator_enforces_next_minute_expiry_and_auction_exit(entry):
    meta, config = runner.load_config(NAME, "development")
    strategy = runner.load_strategy(NAME, config["params"])
    view = session([*ROWS, (entry, 1.03, 60_000), (950, 1.08, 45_000)])
    trades = simulate_day(
        DayData(view, {"ABC": 1.09}),
        day_signals(strategy, view),
        risk=RiskConfig(**config["risk"]),
        config=FillConfig(**config["fills"]),
        costs=load(meta["cost_calibration"]),
    ).trades
    if entry == 577:
        (trade,) = trades
        assert (trade.entry_minute, trade.exit_minute, trade.exit_reason) == (577, 960, "auction")
    else:
        assert trades == []


def test_registered_configs_differ_only_by_period_or_comparison_reference():
    _, development = runner.load_config(NAME, "development")
    _, comparison = runner.load_config(NAME, "development_comparison")
    _, validation = runner.load_config(NAME, "validation")
    assert development["period"] == {"start": date(2003, 9, 10), "end": date(2016, 12, 30)}
    assert validation["period"] == {"start": date(2017, 1, 3), "end": date(2023, 11, 8)}
    assert comparison == {**development, "params": {"reference": 1.2}}
    assert validation == {**development, "period": validation["period"]}
