"""Check distributed price drops, exact checkpoints and same-day execution."""

from datetime import date

import pytest

from kinn import run as runner
from kinn.core.types import Signal
from kinn.costs.model import load
from kinn.engine.intraday.data import DayData, DayView, make_symbol_day
from kinn.engine.intraday.simulator import FillConfig, simulate_day
from kinn.engine.intraday.strategy import check_no_lookahead, day_signals
from kinn.risk.sizing import RiskConfig

NAME = "distributed_morning_selloff"
DAY = date(2016, 12, 2)
MINUTES = [570, 584, 599, 614, 629, 644, 659, 664]
PRICES = [10, 9.8, 9.6, 9.4, 9.2, 9.0, 8.8, 8.91]
ROWS = [(minute, price, 7_000) for minute, price in zip(MINUTES, PRICES, strict=True)]
EXPECTED = [Signal("ABC", 664, expire_minute=665)]


def session(rows=ROWS, *, prior_close=10.0):
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
        {"prev_close": prior_close, "adv20_prev": 2e6},
    )
    return DayView(DAY, 570, 960, {"ABC": stock})


def test_uses_completed_checkpoints_and_passes_prefix_replay():
    strategy = runner.load_strategy(NAME, {})
    view = session([(550, 20.0, 900_000), *ROWS, (665, 9.0, 8_000), (951, 10.2, 8_000)])
    found = day_signals(strategy, view)
    assert found == EXPECTED
    assert day_signals(strategy, view.upto(663)) == []
    assert day_signals(strategy, view.upto(664)) == EXPECTED
    check_no_lookahead(strategy, view, found, [550, 570, 659, 663, 664, 665, 951])


@pytest.mark.parametrize(
    "kwargs",
    [
        {"prior_close": 10.6},
        {"rows": ROWS[1:]},
        {"rows": [*ROWS[:2], (600, 9.6, 7_000), *ROWS[3:]]},
        {"rows": [*ROWS[:2], (599, float("nan"), 7_000), *ROWS[3:]]},
        {"rows": [*ROWS[:-2], (659, 9.1, 7_000), ROWS[-1]]},
        {"rows": [*ROWS[:-1], (664, 8.87, 7_000)]},
        {"rows": [*ROWS[:-1], (664, 8.91, 4_000)]},
    ],
)
def test_rejects_incomplete_or_unconfirmed_morning_decline(kwargs):
    assert day_signals(runner.load_strategy(NAME, {}), session(**kwargs)) == []


@pytest.mark.parametrize(
    "prices",
    [
        [10, 9.3, 9.2, 9.1, 9.0, 8.9, 8.8, 8.91],
        [10, 9.5, 9.6, 9.1, 9.2, 8.7, 8.8, 8.91],
    ],
)
def test_rejects_single_dominant_loss_and_only_three_down_intervals(prices):
    strategy = runner.load_strategy(NAME, {})
    rows = [(minute, price, 7_000) for minute, price in zip(MINUTES, prices, strict=True)]
    assert day_signals(strategy, session(rows)) == []


@pytest.mark.parametrize("entry", [665, 666])
def test_market_buy_expires_after_next_minute_and_exits_same_day(entry):
    meta, config = runner.load_config(NAME, "development")
    strategy = runner.load_strategy(NAME, config["params"])
    view = session([*ROWS, (entry, 9.0, 8_000), (951, 10.0, 8_000)])
    trades = simulate_day(
        DayData(view, {"ABC": 10.2}),
        day_signals(strategy, view),
        risk=RiskConfig(**config["risk"]),
        config=FillConfig(**config["fills"]),
        costs=load(meta["cost_calibration"]),
    ).trades
    if entry == 665:
        (trade,) = trades
        assert (trade.entry_minute, trade.exit_minute, trade.exit_reason) == (665, 960, "auction")
    else:
        assert trades == []


def test_development_and_validation_configs_differ_only_by_dates():
    _, development = runner.load_config(NAME, "development")
    _, validation = runner.load_config(NAME, "validation")
    assert development.pop("period") == {"start": date(2003, 9, 10), "end": date(2016, 12, 30)}
    assert validation.pop("period") == {"start": date(2017, 1, 3), "end": date(2023, 11, 8)}
    assert development == validation
