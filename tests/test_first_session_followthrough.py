"""Verify first-session selection, clock alignment, replay and auction exit."""

from datetime import date

import duckdb
import pytest

from kinn import run as runner
from kinn.core.types import Signal
from kinn.costs.model import load
from kinn.engine.intraday.data import DayData, DayView, make_symbol_day
from kinn.engine.intraday.simulator import FillConfig, simulate_day
from kinn.engine.intraday.strategy import check_no_lookahead, day_signals
from kinn.risk.sizing import RiskConfig

NAME = "first_session_followthrough"
ROWS = [(m, 10.0, 10_000) for m in range(650, 678)] + [(678, 10.6, 10_000), (679, 10.7, 10_000)]
LATER = [(680, 10.8, 8_000), (950, 11.0, 7_000)]
EXPECTED = [Signal("ABC", 679, expire_minute=680)]


def session(rows=ROWS, *, day=date(2016, 12, 2), close=960):
    minutes, prices, sizes = zip(*rows, strict=True)
    stock = make_symbol_day("ABC", 1, minutes, prices, prices, prices, prices, sizes)
    return DayView(day, 570, close, {"ABC": stock})


def test_universe_selects_zero_prior_sessions():
    universe = runner.load_strategy(NAME, {}).universe
    with duckdb.connect() as connection:
        result = connection.execute(
            "select sessions_prior from (values (0), (1), (20)) as n(sessions_prior) "
            "cross join (values ('Domestic Common Stock')) as c(category) "
            f"where {universe.where()}"
        ).fetchall()
    assert result == [(0,)]


def test_first_regular_print_starts_clock_and_passes_replay():
    strategy = runner.load_strategy(NAME, {})
    view = session([(550, 2.0, 2_000_000), *ROWS, *LATER])
    found = day_signals(strategy, view)
    assert found == EXPECTED
    assert day_signals(strategy, view.upto(678)) == []
    assert day_signals(strategy, view.upto(679)) == EXPECTED
    check_no_lookahead(strategy, view, found, [550, 650, 677, 678, 679, 680, 950])


@pytest.mark.parametrize(
    ("rows", "params"),
    [
        (ROWS, {"day": date(2003, 12, 2)}),
        (ROWS, {"close": 738}),
        ([(m + 101, p, q) for m, p, q in ROWS], {}),
        ([(m, p * 0.4, q) for m, p, q in ROWS], {}),
        ([ROWS[0], *ROWS[7:]], {}),
        ([*ROWS[:-2], ROWS[-1]], {}),
        ([*ROWS[:-2], (678, 10.4, 10_000), ROWS[-1]], {}),
        ([*ROWS[:-1], (679, float("inf"), 10_000)], {}),
        ([(550, 10, 1_000_000), *((m, p, 4_000) for m, p, _ in ROWS)], {}),
        ([*ROWS[:-1], (679, 10.7, 3_000)], {}),
    ],
)
def test_requires_eligible_first_print_and_confirmed_turnover(rows, params):
    assert day_signals(runner.load_strategy(NAME, {}), session(rows, **params)) == []


def test_entry_follows_confirmation_and_exits_in_the_auction():
    meta, config = runner.load_config(NAME, "development")
    strategy = runner.load_strategy(NAME, config["params"])
    view = session([*ROWS, *LATER])
    result = simulate_day(
        DayData(view, {"ABC": 11.3}),
        day_signals(strategy, view),
        risk=RiskConfig(**config["risk"]),
        config=FillConfig(**config["fills"]),
        costs=load(meta["cost_calibration"]),
    )
    (trade,) = result.trades
    assert (trade.entry_minute, trade.exit_minute, trade.exit_reason) == (680, 960, "auction")


def test_validation_differs_only_in_dates():
    _, development = runner.load_config(NAME, "development")
    _, validation = runner.load_config(NAME, "validation")
    assert development.pop("period") == {"start": date(2003, 9, 10), "end": date(2016, 12, 30)}
    assert validation.pop("period") == {"start": date(2017, 1, 3), "end": date(2023, 11, 8)}
    assert development == validation


def test_turnover_timing_uses_only_trading_through_each_candidate_bar():
    _, config = runner.load_config(NAME, "development_turnover_timing")
    strategy = runner.load_strategy(NAME, config["params"])
    rows = [(650, 10.0, 40_000)]
    rows += [(m, 10.6, 40_000) for m in range(651, 660)]
    view = session(rows + LATER)
    expected = [Signal("ABC", 654, expire_minute=655)]
    found = day_signals(strategy, view)
    assert found == expected
    assert day_signals(strategy, view.upto(653)) == []
    assert day_signals(strategy, view.upto(654)) == expected
    check_no_lookahead(strategy, view, found, [650, 653, 654, 655, 679, 680, 950])
    assert day_signals(strategy, session(rows[:4] + rows[7:8])) == []
    assert day_signals(strategy, session(rows, close=713)) == []


@pytest.mark.parametrize("phase", ["development", "validation"])
def test_turnover_timing_configs_keep_all_other_parameters(phase):
    _, original = runner.load_config(NAME, phase)
    _, timed = runner.load_config(NAME, f"{phase}_turnover_timing")
    assert timed["params"].pop("turnover_timing") is True
    assert timed == original
