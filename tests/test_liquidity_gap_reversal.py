"""Verify the observed gap, price recovery, signal clock and expiry."""

from datetime import date

import pytest

from kinn import run as runner
from kinn.core.types import Signal
from kinn.costs.model import load
from kinn.engine.intraday.data import DayData, DayView, make_symbol_day
from kinn.engine.intraday.simulator import FillConfig, simulate_day
from kinn.engine.intraday.strategy import check_no_lookahead, day_signals
from kinn.risk.sizing import RiskConfig

NAME = "liquidity_gap_reversal"
ACTIVE = [(m, 10.0, 10.0, 2_500) for m in range(600, 605)]
RESUMPTION = (610, 9.1, 9.4, 10_000)
EXPECTED = Signal("ABC", 610, expire_minute=611)


def view(*rows, close_minute=960):
    minute, open_, close, volume = zip(*rows, strict=True)
    high = [max(o, c) for o, c in zip(open_, close, strict=True)]
    low = [min(o, c) for o, c in zip(open_, close, strict=True)]
    stock = make_symbol_day("ABC", 1, minute, open_, high, low, close, volume)
    return DayView(date(2016, 11, 25), 570, close_minute, {"ABC": stock})


def test_partial_recovery_is_known_only_when_the_resumption_bar_closes():
    strategy = runner.load_strategy(NAME, {})
    session = view(*ACTIVE, RESUMPTION, (611, 9.2, 9.0, 5_000), (900, 15.0, 15.0, 5_000))
    found = day_signals(strategy, session)
    assert found == [EXPECTED]
    assert day_signals(strategy, session.upto(609)) == []
    assert day_signals(strategy, session.upto(610)) == found
    check_no_lookahead(strategy, session, found, [599, 604, 605, 609, 610, 611, 900])


@pytest.mark.parametrize(
    "rows",
    [
        [*ACTIVE, (609, 9.1, 9.4, 10_000)],  # gap of four missing minutes
        [*ACTIVE, (621, 9.1, 9.4, 10_000)],  # gap of sixteen missing minutes
        [ACTIVE[0], *ACTIVE[2:], RESUMPTION],  # five consecutive preceding prints required
        [*((m, o, c, 1_000) for m, o, c, _ in ACTIVE), RESUMPTION],  # thin pre-gap bars
        [*ACTIVE, (610, 9.3, 9.55, 10_000)],  # markdown too small
        [*ACTIVE, (610, 9.1, 9.2, 10_000)],  # recovery too small
        [*ACTIVE, (610, 9.1, 9.81, 10_000)],  # full recovery already observed
    ],
)
def test_incomplete_setup_produces_no_signal(rows):
    assert day_signals(runner.load_strategy(NAME, {}), view(*rows)) == []


@pytest.mark.parametrize("entry_minute", [611, 612])
def test_next_bar_only_and_early_close(entry_minute):
    meta, config = runner.load_config(NAME, "development")
    strategy = runner.load_strategy(NAME, {})
    session = view(*ACTIVE, RESUMPTION, (entry_minute, 9.5, 9.5, 10_000), close_minute=780)
    result = simulate_day(
        DayData(session, {"ABC": 10.0}),
        day_signals(strategy, session),
        risk=RiskConfig(**config["risk"]),
        config=FillConfig(**config["fills"]),
        costs=load(meta["cost_calibration"]),
    )
    if entry_minute == 611:
        (trade,) = result.trades
        assert (trade.entry_minute, trade.exit_minute, trade.exit_reason) == (611, 780, "auction")
    else:
        assert result.unfilled == 1 and not result.trades


def test_configs_differ_only_in_date_range():
    _, development = runner.load_config(NAME, "development")
    _, validation = runner.load_config(NAME, "validation")
    assert development.pop("period") == {"start": date(2003, 9, 10), "end": date(2016, 12, 30)}
    assert validation.pop("period") == {"start": date(2017, 1, 3), "end": date(2023, 11, 8)}
    assert development == validation
