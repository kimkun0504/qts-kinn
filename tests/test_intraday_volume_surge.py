"""The joint price and relative turnover event, including truncated-session replay."""

from datetime import date

import pytest

from kinn import run as runner
from kinn.core.types import Signal
from kinn.engine.intraday.data import DayView, make_symbol_day
from kinn.engine.intraday.strategy import check_no_lookahead, day_signals

NAME = "intraday_volume_surge"
OPEN = (570, 10.0, 23_000)
FIRST = (583, 12.0, 60_000)
SECOND = (584, 12.2, 15_000)


def view(*rows, adv=1_000_000):
    minute, price, volume = zip(*rows, strict=True)
    prior = {"prev_close": 10, "adv20_prev": adv, "marketcap_prev": 100_000_000}
    stock = make_symbol_day("ABC", 1, minute, price, price, price, price, volume, prior)
    return DayView(date(2016, 11, 25), 570, 780, {"ABC": stock})


def test_signal_is_the_first_completed_joint_hit_and_survives_replay():
    strategy = runner.load_strategy(NAME, {})
    session = view(OPEN, FIRST, SECOND, (585, 10.0, 10_000), (700, 20.0, 200_000))
    found = day_signals(strategy, session)
    assert found == [Signal("ABC", 584, expire_minute=589)]
    assert day_signals(strategy, session.upto(583)) == []
    assert day_signals(strategy, session.upto(584)) == found
    check_no_lookahead(strategy, session, found, [569, 570, 582, 583, 584, 585, 700])


def test_turnover_can_complete_the_setup_after_the_price_condition():
    strategy = runner.load_strategy(NAME, {})
    session = view(OPEN, FIRST, (584, 12.2, 1_000), (585, 12.2, 15_000))
    assert day_signals(strategy, session) == [Signal("ABC", 585, expire_minute=590)]


@pytest.mark.parametrize(
    "rows",
    [
        [(570, 10.6, 23_000), (583, 13.0, 60_000), (584, 13.2, 15_000)],
        [(571, 10.0, 23_000), FIRST, SECOND],
        [OPEN, (582, 12.1, 70_000), SECOND],  # stale preceding print
        [OPEN, (583, 11.99, 70_000), SECOND],  # a single elevated close
        [(565, 12.0, 100_000), OPEN, FIRST, (584, 12.2, 1_000)],  # thin regular session
        [OPEN, (582, 12.0, 80_000), (583, 12.2, 15_000)],  # before 09:45
        [OPEN, (719, 12.0, 80_000), (720, 12.2, 15_000)],  # after 12:00
    ],
)
def test_missing_joint_conditions_have_no_signal(rows):
    assert day_signals(runner.load_strategy(NAME, {}), view(*rows)) == []


def test_turnover_threshold_uses_the_symbols_own_prior_liquidity():
    assert day_signals(runner.load_strategy(NAME, {}), view(OPEN, FIRST, SECOND, adv=2e6)) == []


def test_configs_differ_only_in_date_range():
    _, development = runner.load_config(NAME, "development")
    _, validation = runner.load_config(NAME, "validation")
    assert development.pop("period") == {"start": date(2003, 9, 10), "end": date(2016, 12, 30)}
    assert validation.pop("period") == {"start": date(2017, 1, 3), "end": date(2023, 11, 8)}
    assert development == validation
