"""The filing signal uses a prior-day disclosure and a completed first trading hour."""

from datetime import date

import pytest

from kinn import run as runner
from kinn.core.types import Signal
from kinn.engine.intraday.data import DayView, make_symbol_day
from kinn.engine.intraday.strategy import check_no_lookahead, day_signals

NAME = "filing_session_momentum"
OPEN = (570, 10.0, 10_000)
CONFIRM = (629, 10.7, 10_000)


def view(*rows, filings=1):
    minute, price, volume = zip(*rows, strict=True)
    prior = {"prev_close": 10, "filings_prev": filings, "filings_today": 1}
    stock = make_symbol_day("ABC", 1, minute, price, price, price, price, volume, prior)
    return DayView(date(2016, 12, 30), 570, 960, {"ABC": stock})


def test_signal_requires_the_completed_first_hour_and_survives_replay():
    strategy = runner.load_strategy(NAME, {})
    session = view(OPEN, (600, 11.0, 5_000), CONFIRM, (630, 9.0, 7_000), (950, 8.0, 7_000))
    found = day_signals(strategy, session)
    assert found == [Signal("ABC", 629, expire_minute=634)]
    assert day_signals(strategy, session.upto(628)) == []
    assert day_signals(strategy, session.upto(629)) == found
    check_no_lookahead(strategy, session, found, [569, 570, 600, 628, 629, 630, 950])


@pytest.mark.parametrize("filings", [None, 0])
def test_same_day_filing_cannot_replace_a_prior_disclosure(filings):
    assert day_signals(runner.load_strategy(NAME, {}), view(OPEN, CONFIRM, filings=filings)) == []


@pytest.mark.parametrize(
    "rows",
    [
        [(570, 10.4, 10_000), (629, 11.1, 10_000)],  # excessive gap up
        [(570, 9.6, 10_000), (629, 10.8, 10_000)],  # excessive gap down
        [OPEN, (629, 10.59, 10_000), (630, 12.0, 10_000)],  # later gain
        [(560, 10.0, 90_000), OPEN, (629, 10.7, 100)],  # premarket turnover excluded
        [(571, 10.0, 10_000), CONFIRM],  # missing opening bar
        [OPEN, (628, 10.7, 10_000), (630, 10.7, 10_000)],  # missing confirmation
    ],
)
def test_invalid_opening_conditions_have_no_signal(rows):
    assert day_signals(runner.load_strategy(NAME, {}), view(*rows)) == []


def test_periods_are_the_only_config_difference():
    _, development = runner.load_config(NAME, "development")
    _, validation = runner.load_config(NAME, "validation")
    assert development.pop("period") == {"start": date(2003, 9, 10), "end": date(2016, 12, 30)}
    assert validation.pop("period") == {"start": date(2017, 1, 3), "end": date(2023, 11, 8)}
    assert development == validation
