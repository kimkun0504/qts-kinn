"""Check filing eligibility, the opening confirmation and same-day execution."""

from dataclasses import replace
from datetime import date

import pytest

from kinn import run as runner
from kinn.core.types import CurrentReport, Signal
from kinn.costs.model import load
from kinn.engine.intraday.data import DayData, DayView, make_symbol_day
from kinn.engine.intraday.simulator import FillConfig, simulate_day
from kinn.engine.intraday.strategy import check_no_lookahead, day_signals
from kinn.risk.sizing import RiskConfig

NAME = "earnings_gap_followthrough"
DAY = date(2016, 12, 2)
EARNINGS = CurrentReport("ABC", 1, date(2016, 12, 1), (22, 91), ("2.02", "9.01"), True)
ROWS = [(570, 11.0, 7_000), (582, 11.0, 7_000), (583, 11.2, 7_000), (584, 11.4, 7_000)]
LATER = [(585, 11.5, 8_000), (950, 13.0, 8_000)]
EXPECTED = [Signal("ABC", 584, expire_minute=585)]


def session(rows=ROWS, *, reports=(EARNINGS,), prior_close=10.0, adv=1e6):
    minutes, prices, sizes = zip(*rows, strict=True)
    stock = make_symbol_day(
        "ABC",
        1,
        minutes,
        prices,
        prices,
        prices,
        prices,
        sizes,
        {"prev_close": prior_close, "adv20_prev": adv},
    )
    return DayView(DAY, 570, 960, {"ABC": stock}, reports={"ABC": reports})


def test_confirmed_gap_uses_available_filings_and_passes_prefix_replay():
    strategy = runner.load_strategy(NAME, {})
    assert strategy.inputs == {"form8k": {"sessions": 1}}
    view = session([(550, 1.0, 900_000), *ROWS, *LATER])
    found = day_signals(strategy, view)
    assert found == EXPECTED
    assert day_signals(strategy, view.upto(583)) == []
    assert day_signals(strategy, view.upto(584)) == EXPECTED
    check_no_lookahead(strategy, view, found, [550, 570, 583, 584, 585, 950])


@pytest.mark.parametrize(
    "kwargs",
    [
        {"reports": ()},
        {"reports": (replace(EARNINGS, filed=DAY),)},
        {"reports": (replace(EARNINGS, filed=date(2016, 12, 5)),)},
        {"reports": (replace(EARNINGS, items=("9.01",), earnings=False),)},
        {"reports": (replace(EARNINGS, permaticker=2),)},
        {"prior_close": 10.1},
        {"rows": ROWS[1:]},
        {"rows": [*ROWS[:2], ROWS[-1]]},
        {"rows": [*ROWS[:2], (583, 11.05, 7_000), ROWS[-1]]},
        {"rows": [*ROWS[:-1], (584, 11.4, 3_000)]},
        {"rows": [(550, 11.0, 900_000), *ROWS], "adv": 2e6},
    ],
)
def test_requires_typed_filing_and_confirmed_regular_session_gap(kwargs):
    assert day_signals(runner.load_strategy(NAME, {}), session(**kwargs)) == []


def test_order_uses_next_clock_minute_and_closing_auction():
    meta, config = runner.load_config(NAME, "development")
    strategy = runner.load_strategy(NAME, config["params"])
    view = session([*ROWS, *LATER])
    (trade,) = simulate_day(
        DayData(view, {"ABC": 13.2}),
        day_signals(strategy, view),
        risk=RiskConfig(**config["risk"]),
        config=FillConfig(**config["fills"]),
        costs=load(meta["cost_calibration"]),
    ).trades
    assert (trade.entry_minute, trade.exit_minute, trade.exit_reason) == (585, 960, "auction")


def test_development_and_validation_configs_differ_only_by_dates():
    _, development = runner.load_config(NAME, "development")
    _, validation = runner.load_config(NAME, "validation")
    assert development.pop("period") == {"start": date(2003, 9, 10), "end": date(2016, 12, 30)}
    assert validation.pop("period") == {"start": date(2017, 1, 3), "end": date(2023, 11, 8)}
    assert development == validation
