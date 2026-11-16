"""Check synchronous market windows, replay and same-day execution."""

from datetime import date

import pytest

from kinn import run as runner
from kinn.core.types import Signal
from kinn.costs.model import load
from kinn.engine.intraday.data import DayData, DayView, make_symbol_day
from kinn.engine.intraday.simulator import FillConfig, simulate_day
from kinn.engine.intraday.strategy import check_no_lookahead, day_signals
from kinn.risk.sizing import RiskConfig

NAME = "market_recovery_lag"
PEER = [(570, 100.0), (600, 98.0), (615, 99.0), (900, 50.0)]
TARGET = [
    (570, 10.0),
    (600, 9.0),
    (614, 9.0),
    (615, 9.2),
    (616, 9.3),
    (675, 9.6),
    (676, 9.7),
    (900, 40.0),
]
EXPECTED = [Signal("ABC", 615, expire_minute=616, max_hold_minutes=60)]


def stock(symbol, ident, rows, cap, adv, size):
    minutes, prices = zip(*rows, strict=True)
    return make_symbol_day(
        symbol,
        ident,
        minutes,
        prices,
        prices,
        prices,
        prices,
        [size] * len(rows),
        {"marketcap_prev": cap, "prev_close": prices[0], "adv20_prev": adv},
    )


def session(target=TARGET, *, peer=PEER, count=30, size=10_000, close=960):
    symbols = {f"P{i}": stock(f"P{i}", i, peer, 50e9, 20e6, 10_000) for i in range(count)}
    symbols["ABC"] = stock("ABC", 500, target, 1e9, 8e6, size)
    return DayView(date(2016, 12, 2), 570, close, symbols)


def test_market_recovery_is_visible_only_after_confirmation():
    strategy = runner.load_strategy(NAME, {})
    view = session()
    found = day_signals(strategy, view)
    assert found == EXPECTED
    assert day_signals(strategy, view.upto(614)) == []
    assert day_signals(strategy, view.upto(615)) == EXPECTED
    check_no_lookahead(strategy, view, found, [570, 600, 614, 615, 616, 676, 900])


@pytest.mark.parametrize(
    "kwargs",
    [
        {"count": 29},
        {"peer": [(570, 100), (600, 99), (615, 100)]},
        {"peer": [(570, 100), (600, 98), (615, 98.5)]},
        {"peer": [(570, 100), (599, 98), (615, 99)]},
        {"target": [TARGET[0], (600, 9.5), *TARGET[2:]]},
        {"target": [*TARGET[:3], (615, 9.5), *TARGET[4:]]},
        {"target": [*TARGET[:2], (613, 9), *TARGET[3:]]},
        {"size": 4_000},
        {"close": 689},
    ],
)
def test_requires_market_turn_and_lagging_stock_recovery(kwargs):
    assert day_signals(runner.load_strategy(NAME, {}), session(**kwargs)) == []


def test_requires_thirty_jointly_observed_peers():
    view = session(count=29)
    symbols = {
        **view.symbols,
        "LEFT": stock("LEFT", 100, PEER[:2], 50e9, 20e6, 10_000),
        "RIGHT": stock("RIGHT", 101, PEER[1:3], 50e9, 20e6, 10_000),
    }
    partial = DayView(view.day, view.open_minute, view.close_minute, symbols)
    assert day_signals(runner.load_strategy(NAME, {}), partial) == []


def test_order_enters_on_next_bar_and_exits_in_one_hour():
    meta, config = runner.load_config(NAME, "development")
    strategy = runner.load_strategy(NAME, config["params"])
    view = session()
    result = simulate_day(
        DayData(view, {"ABC": 11.0}),
        day_signals(strategy, view),
        risk=RiskConfig(**config["risk"]),
        config=FillConfig(**config["fills"]),
        costs=load(meta["cost_calibration"]),
    )
    (trade,) = result.trades
    assert (trade.entry_minute, trade.exit_minute, trade.exit_reason) == (616, 676, "time")


def test_validation_differs_only_in_dates():
    _, development = runner.load_config(NAME, "development")
    _, validation = runner.load_config(NAME, "validation")
    assert development.pop("period") == {"start": date(2003, 9, 10), "end": date(2016, 12, 30)}
    assert validation.pop("period") == {"start": date(2017, 1, 3), "end": date(2023, 11, 8)}
    assert development == validation
