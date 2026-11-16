"""Verify the gap proxy and two printed resumption bars."""

from datetime import date

import pytest

from kinn import run as runner
from kinn.core.types import Signal
from kinn.engine.intraday.data import DayView, make_symbol_day
from kinn.engine.intraday.strategy import check_no_lookahead, day_signals

NAME = "resumption_momentum"
BEFORE = [(600, 10), (601, 10.15), (602, 10.3), (603, 10.6), (604, 10.9)]
REOPEN = (609, 10.97)
CONFIRM = (610, 11.1)
EXPECTED = Signal("ABC", 610, expire_minute=611, max_hold_minutes=60)


def view(*rows, day=date(2016, 12, 2), end=960, volume=5_000, cap=100e6):
    minute, price = zip(*rows, strict=True)
    stock = make_symbol_day(
        "ABC",
        1,
        minute,
        price,
        price,
        price,
        price,
        [volume] * len(price),
        {"marketcap_prev": cap},
    )
    return DayView(day, 570, end, {"ABC": stock})


def test_momentum_confirmation_is_causal_and_uses_its_own_clock_minute():
    strategy = runner.load_strategy(NAME, {})
    session = view(*BEFORE, REOPEN, CONFIRM, (611, 6.0), (900, 16))
    found = day_signals(strategy, session)
    assert found == [EXPECTED]
    assert day_signals(strategy, session.upto(609)) == []
    assert day_signals(strategy, session.upto(610)) == found
    check_no_lookahead(strategy, session, found, [598, 604, 608, 609, 610, 611, 900])


@pytest.mark.parametrize(
    "rows, options",
    [
        ([*BEFORE, (608, 10.97), (609, 11.1)], {}),  # three absent minutes
        ([*BEFORE, (612, 10.97), (613, 11.1)], {}),  # seven absent minutes
        ([*BEFORE, REOPEN, (611, 11.1)], {}),  # no immediate confirmation
        ([*BEFORE[:4], (604, 10.7), REOPEN, CONFIRM], {}),  # pre-gap rise too small
        ([*BEFORE, (609, 10.2), (610, 10.5)], {}),  # fails to keep the earlier gain
        ([*BEFORE, REOPEN, (610, 11.05)], {}),  # weak continuation
        ([*BEFORE, REOPEN, CONFIRM], {"volume": 3_000}),
        ([*BEFORE, REOPEN, CONFIRM], {"day": date(2014, 5, 9)}),
        ([*BEFORE, REOPEN, CONFIRM], {"end": 680}),
        ([*BEFORE, REOPEN, CONFIRM], {"cap": 0}),
    ],
)
def test_excludes_incomplete_setups(rows, options):
    assert day_signals(runner.load_strategy(NAME, {}), view(*rows, **options)) == []


def test_configs_differ_only_in_date_range():
    _, development = runner.load_config(NAME, "development")
    _, validation = runner.load_config(NAME, "validation")
    assert development.pop("period") == {"start": date(2003, 9, 10), "end": date(2016, 12, 30)}
    assert validation.pop("period") == {"start": date(2017, 1, 3), "end": date(2023, 11, 8)}
    assert development == validation
