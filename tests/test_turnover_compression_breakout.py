"""Check the frozen turnover window, next-bar execution and replay."""

from datetime import date

import pytest

from kinn import run as runner
from kinn.core.types import Signal
from kinn.costs.model import load
from kinn.engine.intraday.data import DayData, DayView, make_symbol_day
from kinn.engine.intraday.simulator import FillConfig, simulate_day
from kinn.engine.intraday.strategy import check_no_lookahead, day_signals
from kinn.risk.sizing import RiskConfig

NAME = "turnover_compression_breakout"
BASE = [(minute, 10.0, 6_000) for minute in range(570, 600)]
BREAKOUT = [
    (600, 10.5, 5_000),
    (601, 10.6, 5_000),
    (602, 10.7, 5_000),
    (661, 11.5, 10_000),
    (662, 11.7, 10_000),
]
EXPECTED = [Signal("ABC", 601, expire_minute=602, max_hold_minutes=60)]


def session(rows, *, prior_close=10, adv=5e6, cap=400e6, close=960):
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


def test_breakout_uses_only_regular_bars_and_passes_replay():
    strategy = runner.load_strategy(NAME, {})
    full = session([(560, 99.0, 100_000), *BASE, *BREAKOUT])
    found = day_signals(strategy, full)
    assert found == EXPECTED
    assert day_signals(strategy, full.upto(600)) == []
    assert day_signals(strategy, full.upto(601)) == EXPECTED
    assert day_signals(strategy, session([BASE[0], *BASE[3:], *BREAKOUT])) == EXPECTED
    check_no_lookahead(strategy, full, found, [560, 570, 599, 600, 601, 602, 662])


@pytest.mark.parametrize(
    ("rows", "prior"),
    [
        ([*BASE, *BREAKOUT], {"prior_close": 9.4}),
        ([*BASE, *BREAKOUT], {"adv": 4.9e6}),
        ([*BASE, *BREAKOUT], {"cap": 2e9}),
        ([*BASE, *BREAKOUT], {"close": 675}),
        ([*BASE[1:], *BREAKOUT], {}),
        ([BASE[0], *BASE[4:], *BREAKOUT], {}),
        ([*BASE[:15], (585, 9.6, 6_000), *BASE[16:], *BREAKOUT], {}),
        ([(m, p, 4_000) for m, p, _ in BASE] + BREAKOUT, {}),
        ([*BASE, (600, 10.2, 5_000), BREAKOUT[1]], {}),
        ([*BASE, BREAKOUT[0], (601, 10.4, 5_000), *BREAKOUT[2:]], {}),
        ([*BASE, BREAKOUT[0], (601, 10.6, 3_000), *BREAKOUT[2:]], {}),
    ],
)
def test_breakout_requires_the_registered_history_and_confirmation(rows, prior):
    assert day_signals(runner.load_strategy(NAME, {}), session(rows, **prior)) == []


def test_order_enters_on_next_minute_and_stays_intraday():
    meta, config = runner.load_config(NAME, "development")
    strategy = runner.load_strategy(NAME, config["params"])
    view = session([*BASE, *BREAKOUT])
    result = simulate_day(
        DayData(view, {"ABC": 14.0}),
        day_signals(strategy, view),
        risk=RiskConfig(**config["risk"]),
        config=FillConfig(**config["fills"]),
        costs=load(meta["cost_calibration"]),
    )
    (trade,) = result.trades
    assert (trade.entry_minute, trade.exit_minute, trade.exit_reason) == (602, 662, "time")


def test_configs_differ_only_in_dates():
    _, development = runner.load_config(NAME, "development")
    _, validation = runner.load_config(NAME, "validation")
    assert development.pop("period") == {"start": date(2003, 9, 10), "end": date(2016, 12, 30)}
    assert validation.pop("period") == {"start": date(2017, 1, 3), "end": date(2023, 11, 8)}
    assert development == validation
