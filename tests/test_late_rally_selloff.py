"""Check the late-session path, exact bar availability and auction exit."""

from datetime import date

import pytest

from kinn import run as runner
from kinn.core.types import Signal
from kinn.costs.model import load
from kinn.engine.intraday.data import DayData, DayView, make_symbol_day
from kinn.engine.intraday.simulator import FillConfig, simulate_day
from kinn.engine.intraday.strategy import check_no_lookahead, day_signals
from kinn.risk.sizing import RiskConfig

NAME = "late_rally_selloff"
DAY = date(2016, 12, 2)
ROWS = [(570, 10.0, 7_000), (899, 12.0, 7_000), (919, 11.2, 7_000), (924, 11.4, 7_000)]
EXPECTED = [Signal("ABC", 924, expire_minute=925)]


def session(rows=ROWS, *, open_minute=570, close_minute=960):
    minutes, prices, sizes = zip(*rows, strict=True)
    stock = make_symbol_day(
        "ABC", 1, minutes, prices, prices, prices, prices, sizes, {"adv20_prev": 2e6}
    )
    return DayView(DAY, open_minute, close_minute, {"ABC": stock})


def test_recovery_requires_completed_bar_and_passes_prefix_replay():
    strategy = runner.load_strategy(NAME, {})
    view = session([(550, 20.0, 900_000), *ROWS, (925, 11.5, 8_000), (951, 11.9, 8_000)])
    found = day_signals(strategy, view)
    assert found == EXPECTED
    assert day_signals(strategy, view.upto(923)) == []
    assert day_signals(strategy, view.upto(924)) == EXPECTED
    check_no_lookahead(strategy, view, found, [550, 570, 899, 919, 923, 924, 925, 951])


@pytest.mark.parametrize(
    "kwargs",
    [
        {"rows": [(565, 10.0, 7_000), *ROWS[1:]]},
        {"rows": [ROWS[0], *ROWS[2:]]},
        {"rows": [*ROWS[:2], (920, 11.2, 7_000), ROWS[-1]]},
        {"rows": [*ROWS[:-1], (925, 11.4, 7_000)]},
        {"rows": [(570, 11.0, 7_000), *ROWS[1:]]},
        {"rows": [*ROWS[:2], (919, 11.4, 7_000), (924, 11.6, 7_000)]},
        {"rows": [*ROWS[:-1], (924, 11.3, 7_000)]},
        {"rows": [*ROWS[:-1], (924, 11.8, 7_000)]},
        {"rows": [*ROWS[:-1], (924, 11.4, 3_000)]},
        {"rows": [*ROWS[:-1], (924, float("nan"), 30_000)]},
        {"open_minute": 571},
        {"close_minute": 780},
    ],
)
def test_rejects_ineligible_path_or_session(kwargs):
    assert day_signals(runner.load_strategy(NAME, {}), session(**kwargs)) == []


@pytest.mark.parametrize("entry", [925, 926])
def test_only_next_minute_can_fill_and_exit_is_same_day(entry):
    meta, config = runner.load_config(NAME, "development")
    strategy = runner.load_strategy(NAME, config["params"])
    view = session([*ROWS, (entry, 11.5, 8_000), (951, 11.9, 8_000)])
    trades = simulate_day(
        DayData(view, {"ABC": 12.1}),
        day_signals(strategy, view),
        risk=RiskConfig(**config["risk"]),
        config=FillConfig(**config["fills"]),
        costs=load(meta["cost_calibration"]),
    ).trades
    if entry == 925:
        (trade,) = trades
        assert (trade.entry_minute, trade.exit_minute, trade.exit_reason) == (925, 960, "auction")
    else:
        assert trades == []


def test_development_and_validation_configs_differ_only_by_dates():
    _, development = runner.load_config(NAME, "development")
    _, validation = runner.load_config(NAME, "validation")
    assert development.pop("period") == {"start": date(2003, 9, 10), "end": date(2016, 12, 30)}
    assert validation.pop("period") == {"start": date(2017, 1, 3), "end": date(2023, 11, 8)}
    assert development == validation
