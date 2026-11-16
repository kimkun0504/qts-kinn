"""Test confirmation timing, event exclusions and portfolio execution."""

from datetime import date

import pytest

from kinn import run as runner
from kinn.core.types import Signal
from kinn.costs.model import load
from kinn.engine.intraday.data import DayData, DayView, make_symbol_day
from kinn.engine.intraday.simulator import FillConfig, simulate_day
from kinn.engine.intraday.strategy import check_no_lookahead, day_signals
from kinn.risk.sizing import RiskConfig

NAME = "rebound_confirmed_recovery"
# Clock minute, price (open, close, high, low unless specified).
OPEN = (570, 10.0)
EVENT = (640, 8.9)
LOW_CLOSE = (641, 8.3)
RECOVERY = (642, 8.4)
SETUP = (OPEN, EVENT, LOW_CLOSE, RECOVERY)
EXPECTED = Signal("ABC", 642, expire_minute=643)


def view(*rows, filings=0, premarket_volume=5_000):
    minutes = [row[0] for row in rows]
    prices = [row[1] for row in rows]
    lows = [row[-1] for row in rows]
    volume = [premarket_volume if minute < 570 else 10_000 for minute in minutes]
    prior = {"prev_close": 10.0, "adv20_prev": 1_000_000, "filings_prev": filings}
    stock = make_symbol_day("ABC", 1, minutes, prices, prices, lows, prices, volume, prior)
    return DayView(date(2016, 11, 25), 570, 780, {"ABC": stock})


def test_confirmation_uses_only_prior_closes_and_survives_replay():
    strategy = runner.load_strategy(NAME, {})
    session = view(*SETUP, (643, 7.0), (644, 7.2), (779, 9.1))
    found = day_signals(strategy, session)
    assert found == [EXPECTED]
    assert day_signals(strategy, session.upto(641)) == []
    assert day_signals(strategy, session.upto(642)) == found
    check_no_lookahead(strategy, session, found, [569, 575, 640, 641, 642, 643, 644, 779])


@pytest.mark.parametrize(
    "rows",
    [
        [(570, 9.4), EVENT, LOW_CLOSE, RECOVERY],  # gap down before the signal
        [OPEN, (572, 8.95), EVENT, LOW_CLOSE, RECOVERY],  # first crossing too early
        [OPEN, EVENT, (641, 8.5), (642, 8.53)],  # negligible recovery
        [OPEN, EVENT, LOW_CLOSE, (642, 8.55)],  # recovery above the reference
        [OPEN, EVENT, (641, 8.6, 8.1), RECOVERY],  # isolated low, no preceding deep close
        [OPEN, EVENT, (650, 8.3), (651, 8.4)],  # recovery after ten clock minutes
        [OPEN, (781, 8.9), (782, 8.3), (783, 8.4)],  # after an early session close
    ],
)
def test_rejects_setups_outside_the_definition(rows):
    assert day_signals(runner.load_strategy(NAME, {}), view(*rows)) == []


def test_news_and_heavy_premarket_turnover_are_excluded():
    strategy = runner.load_strategy(NAME, {})
    assert day_signals(strategy, view(*SETUP, filings=1)) == []
    assert day_signals(strategy, view((560, 10.0), *SETUP)) == []
    assert day_signals(strategy, view((560, 10.0), *SETUP, premarket_volume=4_999)) == [EXPECTED]


@pytest.mark.parametrize("entry_bar", [(643, 8.6), (644, 8.7)])
def test_next_bar_market_entry_or_expiry_and_same_day_auction(entry_bar):
    meta, config = runner.load_config(NAME, "development")
    strategy = runner.load_strategy(NAME, config.get("params", {}))
    session = view(*SETUP, entry_bar, (779, 8.8))
    found = day_signals(strategy, session)
    assert found == [EXPECTED]
    result = simulate_day(
        DayData(session, {"ABC": 9.1}),
        found,
        risk=RiskConfig(**config["risk"]),
        config=FillConfig(**config["fills"]),
        costs=load(meta["cost_calibration"]),
    )
    if entry_bar[0] == 643:
        (trade,) = result.trades
        assert (trade.signal_minute, trade.entry_minute, trade.exit_minute) == (642, 643, 780)
        assert trade.entry_price == pytest.approx(8.6)
        assert trade.exit_price == pytest.approx(9.1)
        assert trade.exit_reason == "auction"
    else:
        assert not result.trades and result.unfilled == 1


def test_configs_differ_only_in_date_range():
    _, development = runner.load_config(NAME, "development")
    _, validation = runner.load_config(NAME, "validation")
    assert development.pop("period") == {"start": date(2003, 9, 10), "end": date(2016, 12, 30)}
    assert validation.pop("period") == {"start": date(2017, 1, 3), "end": date(2023, 11, 8)}
    assert development == validation
