"""Signal, availability and execution checks for the frozen gap reclaim."""

from datetime import date

import pytest

from kinn import run as runner
from kinn.core.types import Signal
from kinn.costs.model import load
from kinn.engine.intraday.data import DayData, DayView, make_symbol_day
from kinn.engine.intraday.simulator import FillConfig, simulate_day
from kinn.engine.intraday.strategy import check_no_lookahead, day_signals
from kinn.risk.sizing import RiskConfig

NAME = "opening_gap_reclaim"
OPEN = (570, 8.0, 7_000)
CONFIRM = (584, 8.4, 6_000)
EXPECTED = Signal("ABC", 584, expire_minute=589)


def view(*rows):
    minute, price, volume = zip(*rows, strict=True)
    stock = make_symbol_day(
        "ABC", 1, minute, price, price, price, price, volume, {"prev_close": 10}
    )
    return DayView(date(2016, 11, 25), 570, 780, {"ABC": stock})


def test_reclaim_is_available_at_confirmation_and_survives_replay():
    strategy = runner.load_strategy(NAME, {})
    session = view(OPEN, CONFIRM, (585, 7.0, 6_000), (776, 12.0, 7_000))
    found = day_signals(strategy, session)
    assert found == [EXPECTED]
    assert day_signals(strategy, session.upto(583)) == []
    assert day_signals(strategy, session.upto(584)) == found
    check_no_lookahead(strategy, session, found, [569, 570, 583, 584, 585, 776])


@pytest.mark.parametrize(
    "rows",
    [
        [(570, 8.6, 7_000), (584, 9.0, 6_000)],  # gap too small
        [(570, 5.9, 9_000), (584, 6.2, 9_000)],  # gap too large
        [OPEN, (584, 8.23, 6_000), (585, 9.0, 8_000)],  # later bounce
        [OPEN, (584, 9.21, 6_000)],  # room to recover already gone
        [(560, 8.0, 9_000), OPEN, (584, 8.4, 100)],  # premarket turnover excluded
        [(571, 8.0, 7_000), CONFIRM],  # opening bar missing
        [OPEN, (583, 8.4, 6_000), (585, 8.4, 6_000)],  # confirmation bar missing
    ],
)
def test_invalid_setup_has_no_signal(rows):
    assert day_signals(runner.load_strategy(NAME, {}), view(*rows)) == []


@pytest.mark.parametrize("entry_minute", [589, 590])
def test_inclusive_expiry_and_early_close_auction(entry_minute):
    meta, config = runner.load_config(NAME, "development")
    strategy = runner.load_strategy(NAME, config.get("params", {}))
    session = view(OPEN, CONFIRM, (entry_minute, 8.5, 100), (779, 11.0, 10_000))
    found = day_signals(strategy, session)
    assert found == [EXPECTED]
    result = simulate_day(
        DayData(session, {"ABC": 11.5}),
        found,
        risk=RiskConfig(**config["risk"]),
        config=FillConfig(**config["fills"]),
        costs=load(meta["cost_calibration"]),
    )
    if entry_minute == 589:
        (trade,) = result.trades
        assert (trade.entry_minute, trade.exit_minute, trade.quantity) == (589, 780, 5)
        assert trade.exit_reason == "auction"
        assert trade.exit_price == 11.5
    else:
        assert result.unfilled == 1 and not result.trades


def test_periods_are_the_only_config_difference():
    _, development = runner.load_config(NAME, "development")
    _, validation = runner.load_config(NAME, "validation")
    assert development.pop("period") == {"start": date(2003, 9, 10), "end": date(2016, 12, 30)}
    assert validation.pop("period") == {"start": date(2017, 1, 3), "end": date(2023, 11, 8)}
    assert development == validation
