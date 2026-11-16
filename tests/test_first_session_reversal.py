"""Verify first-session filtering, the recovery window and replay."""

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

NAME = "first_session_reversal"
BASE = [(m, 10.0, 20_000) for m in range(650, 663)]
ROWS = [*BASE, (663, 8.8, 20_000), (664, 8.95, 20_000)]
LATER = [(665, 9.15, 12_000), (740, 8.5, 20_000), (950, 9.7, 20_000)]
EXPECTED = [Signal("ABC", 664, expire_minute=665)]


def session(rows=ROWS, *, day=date(2016, 12, 2), close=960):
    minutes, prices, sizes = zip(*rows, strict=True)
    stock = make_symbol_day("ABC", 1, minutes, prices, prices, prices, prices, sizes)
    return DayView(day, 570, close, {"ABC": stock})


def test_universe_accepts_only_first_observed_sessions():
    universe = runner.load_strategy(NAME, {}).universe
    with duckdb.connect() as connection:
        rows = connection.execute(
            "select sessions_prior from (values (0), (1), (20)) as n(sessions_prior) "
            "cross join (values ('Domestic Common Stock')) as c(category) "
            f"where {universe.where()}"
        ).fetchall()
    assert rows == [(0,)]


def test_signal_uses_regular_bars_and_passes_replay():
    strategy = runner.load_strategy(NAME, {})
    full = session([(545, 18.0, 400_000), *ROWS, *LATER])
    found = day_signals(strategy, full)
    assert found == EXPECTED
    assert day_signals(strategy, full.upto(663)) == []
    assert day_signals(strategy, full.upto(664)) == EXPECTED
    check_no_lookahead(strategy, full, found, [545, 650, 663, 664, 665, 740, 950])


@pytest.mark.parametrize(
    ("rows", "options"),
    [
        (ROWS, {"day": date(2003, 12, 2)}),
        (ROWS, {"close": 723}),
        ([(m + 101, p, q) for m, p, q in ROWS], {}),
        ([(m, p * 0.4, q) for m, p, q in ROWS], {}),
        ([*BASE, (663, 8.8, 20_000), (664, 9.05, 20_000)], {}),
        ([*BASE, (663, 8.9, 20_000), (664, 8.95, 20_000)], {}),
        ([*BASE, ROWS[-1]], {}),
        ([*BASE[:8], *ROWS[-2:]], {}),
        ([*BASE[:-1], (662, 8.8, 20_000), (663, 8.95, 20_000)], {}),
        ([(545, 10, 1_000_000), *((m, p, 8_000) for m, p, _ in ROWS)], {}),
        ([*ROWS[:-1], (664, 8.95, 4_000)], {}),
    ],
)
def test_signal_requires_registered_discount_turnover_and_window(rows, options):
    assert day_signals(runner.load_strategy(NAME, {}), session(rows, **options)) == []


def test_order_enters_next_bar_and_exits_in_the_auction():
    meta, config = runner.load_config(NAME, "development")
    strategy = runner.load_strategy(NAME, config["params"])
    view = session([*ROWS, *LATER])
    result = simulate_day(
        DayData(view, {"ABC": 9.9}),
        day_signals(strategy, view),
        risk=RiskConfig(**config["risk"]),
        config=FillConfig(**config["fills"]),
        costs=load(meta["cost_calibration"]),
    )
    (trade,) = result.trades
    assert (trade.entry_minute, trade.exit_minute, trade.exit_reason) == (665, 960, "auction")


def test_validation_differs_only_in_dates():
    _, development = runner.load_config(NAME, "development")
    _, validation = runner.load_config(NAME, "validation")
    assert development.pop("period") == {"start": date(2003, 9, 10), "end": date(2016, 12, 30)}
    assert validation.pop("period") == {"start": date(2017, 1, 3), "end": date(2023, 11, 8)}
    assert development == validation
