"""Test the listing-age screen and the completed first-half-hour signal."""

from datetime import date

import duckdb
import pytest

from kinn import run as runner
from kinn.core.types import Signal
from kinn.engine.intraday.data import DayView, make_symbol_day
from kinn.engine.intraday.strategy import check_no_lookahead, day_signals

NAME = "new_listing_drift"
OPEN = (570, 10.0, 65_000)
CONFIRM = (599, 10.7, 63_000)


def view(*rows, day=date(2016, 12, 2), adv=5_000_000):
    minute, price, volume = zip(*rows, strict=True)
    prior = {"prev_close": 10.0, "adv20_prev": adv}
    stock = make_symbol_day("ABC", 1, minute, price, price, price, price, volume, prior)
    return DayView(day, 570, 960, {"ABC": stock})


def test_only_one_through_nine_prior_sessions_eligible():
    where = runner.load_strategy(NAME, {}).universe.where()
    with duckdb.connect() as connection:
        result = connection.sql(
            f"""select sessions_prior from (
                    select unnest([0, 1, 9, 10, 100]) as sessions_prior,
                           'Domestic Common Stock' as category,
                           10.0 as prev_close, 5000000 as adv20_prev
                ) where {where}
                order by sessions_prior"""
        ).fetchall()
    assert result == [(1,), (9,)]


def test_bar_completion_and_future_independent_replay():
    strategy = runner.load_strategy(NAME, {})
    session = view(OPEN, CONFIRM, (600, 7.5, 100_000), (930, 12.0, 10_000))
    found = day_signals(strategy, session)
    assert found == [Signal("ABC", 599, expire_minute=600)]
    assert day_signals(strategy, session.upto(598)) == []
    assert day_signals(strategy, session.upto(599)) == found
    check_no_lookahead(strategy, session, found, [569, 570, 598, 599, 600, 930])


@pytest.mark.parametrize(
    "rows",
    [
        [(571, 10.0, 65_000), CONFIRM],
        [OPEN, (598, 10.7, 63_000), (600, 10.7, 63_000)],
        [OPEN, (599, 10.5, 63_000)],
        [(570, 10.6, 65_000), (599, 11.3, 63_000)],
        [(565, 10.0, 100_000), OPEN, (599, 10.7, 1_000)],
    ],
)
def test_rejects_without_exact_open_confirm_or_turnover(rows):
    assert day_signals(runner.load_strategy(NAME, {}), view(*rows)) == []


def test_relative_turnover_and_coverage_start():
    strategy = runner.load_strategy(NAME, {})
    assert day_signals(strategy, view(OPEN, CONFIRM, adv=10_000_000)) == []
    assert day_signals(strategy, view(OPEN, CONFIRM, day=date(2003, 10, 31))) == []


def test_only_the_dates_differ_between_configs():
    _, development = runner.load_config(NAME, "development")
    _, validation = runner.load_config(NAME, "validation")
    assert development.pop("period") == {"start": date(2003, 9, 10), "end": date(2016, 12, 30)}
    assert validation.pop("period") == {"start": date(2017, 1, 3), "end": date(2023, 11, 8)}
    assert development == validation
