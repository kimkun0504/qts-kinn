"""The rebound event definition, on hand-built sessions (HYPOTHESIS.md)."""

from datetime import date

from kinn import run as runner
from kinn.engine.intraday.data import DayView, make_symbol_day
from kinn.engine.intraday.strategy import check_no_lookahead, day_signals

PARAMS = {
    "drop": 0.10,
    "max_gap": 0.05,
    "max_premarket_share_of_adv": 0.05,
    "first_minute": 575,
    "last_minute": 900,
    "min_price": 1.0,
    "min_adv": 250000,
}
PRIOR = {"prev_close": 10.0, "adv20_prev": 1_000_000.0, "filings_prev": 0}


def view(bars, prior=None):
    """bars: (minute, close, volume); open = high = low = close."""
    m, c, v = zip(*bars, strict=True)
    sd = make_symbol_day("AAA", 1, m, c, c, c, c, v, {**PRIOR, **(prior or {})})
    return DayView(date(2020, 1, 2), 570, 960, {"AAA": sd})


def signals(v):
    strategy = runner.load_strategy("intraday_rebound", PARAMS)
    found = day_signals(strategy, v)
    check_no_lookahead(strategy, v, found, range(571, 955, 3))
    return [(s.symbol, s.minute) for s in found]


DROP = [(570, 10.0, 100), (600, 9.6, 100), (640, 8.9, 100), (700, 8.5, 100), (800, 9.5, 100)]


def test_the_first_close_ten_percent_down_is_the_event():
    assert signals(view(DROP)) == [("AAA", 640)]


def test_a_drop_of_less_than_ten_percent_is_not():
    assert signals(view([(570, 10.0, 100), (640, 9.05, 100)])) == []


def test_a_gap_down_open_is_not_an_intraday_drop():
    assert signals(view([(570, 9.4, 100), (640, 8.9, 100)])) == []


def test_a_filing_since_the_prior_session_excludes_it():
    assert signals(view(DROP, {"filings_prev": 1})) == []


def test_heavy_premarket_trading_excludes_it():
    heavy = [(500, 10.0, 6000), *DROP]  # $60,000 before the open, 6% of the 20-day volume
    assert signals(view(heavy)) == []
    light = [(500, 10.0, 4000), *DROP]
    assert signals(view(light)) == [("AAA", 640)]


def test_only_the_first_crossing_counts_and_only_inside_the_window():
    early = [(570, 10.0, 100), (572, 8.9, 100), (640, 8.8, 100)]  # crossed at 09:32
    assert signals(view(early)) == []
    late = [(570, 10.0, 100), (905, 8.9, 100)]  # after 15:00
    assert signals(view(late)) == []
