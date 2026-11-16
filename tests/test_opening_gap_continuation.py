"""Opening gap signal and fills on synthetic sessions."""

from datetime import date

import pytest

from kinn import run as runner
from kinn.core.types import Signal
from kinn.costs.model import load
from kinn.engine.intraday.data import DayData, DayView, make_symbol_day
from kinn.engine.intraday.simulator import FillConfig, simulate_day
from kinn.engine.intraday.strategy import check_no_lookahead, day_signals
from kinn.risk.sizing import RiskConfig

NAME = "opening_gap_continuation"
# minute, open, close, volume
OPEN = (570, 11.0, 11.0, 5_000)
CONFIRM = (584, 11.1, 11.2, 5_000)
ENTRY = (585, 11.4, 11.6, 200)
LATE = (586, 11.9, 12.0, 5_000)
EARLY_CLOSE_EXIT = (775, 12.5, 12.5, 5_000)
EXPECTED = Signal("ABC", 584, expire_minute=585)


def view(*bars):
    minute, open_, close, volume = zip(*bars, strict=True)
    high = [max(o, c) for o, c in zip(open_, close, strict=True)]
    low = [min(o, c) for o, c in zip(open_, close, strict=True)]
    prior = {"prev_close": 10.0, "adv20_prev": 2_000_000, "sessions_prior": 20}
    sd = make_symbol_day("ABC", 1, minute, open_, high, low, close, volume, prior)
    return DayView(date(2016, 11, 25), 570, 780, {"ABC": sd})


def test_signal_is_known_at_confirmation_and_survives_lookahead_replay():
    strategy = runner.load_strategy(NAME, {})
    session = view(OPEN, CONFIRM, ENTRY, LATE, EARLY_CLOSE_EXIT)
    found = day_signals(strategy, session)
    assert found == [EXPECTED]
    assert day_signals(strategy, session.upto(583)) == []
    assert day_signals(strategy, session.upto(584)) == found
    check_no_lookahead(strategy, session, found, [569, 570, 583, 584, 585, 775])


@pytest.mark.parametrize(
    "bars",
    [
        [(570, 10.4, 10.4, 5_000), CONFIRM],  # gap below 5%
        [(570, 13.0, 13.0, 5_000), (584, 13.2, 13.2, 5_000)],  # gap above 25%
        [OPEN, (584, 11.1, 11.1, 5_000), LATE],  # less than 1% above the open at 09:45
        [(569, 11.0, 11.0, 50_000), OPEN, (584, 11.1, 11.2, 10), LATE],  # thin RTH
        [(571, 11.0, 11.0, 5_000), CONFIRM],  # no print at 09:30
        [OPEN, (583, 11.2, 11.2, 5_000), ENTRY],  # no confirmation at 09:44
    ],
)
def test_rejects_when_an_opening_condition_is_missing(bars):
    assert day_signals(runner.load_strategy(NAME, {}), view(*bars)) == []


@pytest.mark.parametrize("entry_bars", [(ENTRY, LATE), (LATE,)])
def test_market_entry_expires_after_one_bar_and_exit_uses_early_close(entry_bars):
    meta, config = runner.load_config(NAME, "development")
    strategy = runner.load_strategy(NAME, config.get("params", {}))
    session = view(OPEN, CONFIRM, *entry_bars, EARLY_CLOSE_EXIT)
    found = day_signals(strategy, session)
    assert found == [EXPECTED]
    result = simulate_day(
        DayData(session, {"ABC": 13.0}),
        found,
        risk=RiskConfig(**config["risk"]),
        config=FillConfig(**config["fills"]),
        costs=load(meta["cost_calibration"]),
    )
    if entry_bars == (LATE,):
        assert not result.trades
        assert result.unfilled == 1
    else:
        (trade,) = result.trades
        assert (trade.signal_minute, trade.entry_minute, trade.exit_minute) == (584, 585, 775)
        assert trade.quantity == 10  # 5% of the next bar, without a later top-up
        assert trade.entry_price == pytest.approx(11.4)
        assert trade.exit_price == pytest.approx(12.5)
        assert trade.exit_reason == "flatten"


def test_fold_configs_change_only_the_dates():
    _, development = runner.load_config(NAME, "development")
    _, validation = runner.load_config(NAME, "validation")
    development_period = development.pop("period")
    validation_period = validation.pop("period")
    assert development == validation
    assert development_period == {"start": date(2003, 9, 10), "end": date(2016, 12, 30)}
    assert validation_period == {"start": date(2017, 1, 3), "end": date(2023, 11, 8)}
