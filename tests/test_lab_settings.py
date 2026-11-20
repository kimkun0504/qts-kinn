"""Lab settings: the page over the algorithm's SETTINGS over the Lab's defaults, validated."""

from datetime import date

import pytest

from kinn.lab.settings import LAST_ENTRY, PERIODS, SettingsError, parse


def test_defaults():
    s = parse(None)
    assert s.period == "search" and s.window() == PERIODS["search"][:2]
    assert (s.entry.mode, s.exit.hold_days, s.book.max_positions) == ("signal", 20, 20)
    assert s.exit.stop_loss is None and s.universe.min_market_cap == 50e6
    assert (s.entry.side, s.book.borrow_rate, s.universe.tickers) == ("long", 0.01, ())


def test_the_page_wins_over_the_algorithm_which_wins_over_the_lab():
    algorithm = {"exit": {"hold_days": 5, "stop_loss": 0.1}, "book": {"max_positions": 3}}
    s = parse({"exit": {"hold_days": 7}}, algorithm)
    assert (s.exit.hold_days, s.exit.stop_loss, s.book.max_positions) == (7, 0.1, 3)
    assert s.book.position_size == 2000


def test_a_custom_period_ends_by_the_last_entry_day():
    s = parse({"period": "custom", "start": "2019-03-01", "end": "2024-06-30"})
    assert s.window() == (date(2019, 3, 1), LAST_ENTRY)


@pytest.mark.parametrize(
    ("raw", "words"),
    [
        ({"exit": {"hold_days": 0}}, "exit.hold_days must be between 1 and 250"),
        ({"exit": {"hold_days": 2.5}}, "exit.hold_days must be a whole number"),
        ({"exit": {"stop_loss": "ten"}}, "exit.stop_loss must be a number"),
        ({"book": {"position_size": True}}, "book.position_size must be a number"),
        ({"entry": {"mode": "both"}}, "entry.mode must be"),
        ({"entry": {"rank_order": "middle"}}, "entry.rank_order must be"),
        ({"entry": {"side": "both"}}, "entry.side must be 'long' or 'short'"),
        ({"book": {"borrow_rate": 2}}, "book.borrow_rate must be between 0 and 1"),
        ({"universe": {"tickers": ["no way"]}}, "universe.tickers: not a ticker"),
        ({"universe": {"max_market_cap": 10e6}}, "max_market_cap must be above"),
        ({"universe": {"exclude_blank_checks": "no"}}, "exclude_blank_checks must be true"),
        ({"universe": {"min_cap": 1}}, "unknown universe settings: min_cap"),
        ({"speed": 1}, "unknown settings: speed"),
        ({"period": "2024"}, "period must be one of"),
        ({"period": "custom", "start": "2003-01-01", "end": "2010-01-01"}, "on or after 2005"),
        ({"period": "custom", "start": "2012-01-01", "end": "2011-01-01"}, "start must come"),
        ({"period": "custom", "start": "June", "end": "2011-01-01"}, "start must be a date"),
    ],
)
def test_a_bad_setting_is_named(raw, words):
    with pytest.raises(SettingsError, match=words):
        parse(raw)


def test_settings_must_be_an_object():
    with pytest.raises(SettingsError):
        parse(["exit"])  # type: ignore[arg-type]


def test_to_dict_round_trips():
    s = parse(
        {
            "period": "custom",
            "start": "2015-01-05",
            "end": "2016-01-05",
            "entry": {"mode": "rank", "top_n": 4},
        }
    )
    again = parse(s.to_dict())
    assert again == s
