"""Check item eligibility, the opening recovery and same-day execution."""

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

NAME = "equity_sale_gap_reclaim"
DAY = date(2016, 12, 2)
SALE = CurrentReport("ABC", 1, date(2016, 12, 1), (32, 91), ("3.02", "9.01"), False)
EARNINGS = CurrentReport("ABC", 1, date(2016, 12, 1), (22,), ("2.02",), True)
ROWS = [(570, 8.0, 7_000), (582, 8.2, 7_000), (598, 8.6, 7_000), (599, 8.9, 7_000)]
LATER = [(600, 9.0, 8_000), (950, 9.96, 8_000)]
EXPECTED = [Signal("ABC", 599, expire_minute=600)]


def session(rows=ROWS, *, reports=(SALE,), prior_close=10.0, adv=1e6):
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


def test_signal_uses_completed_bars_and_only_earnings_visible_for_this_issuer():
    strategy = runner.load_strategy(NAME, {})
    assert strategy.inputs == {"form8k": {"sessions": 1}}
    unrelated = replace(EARNINGS, permaticker=2)
    same_day = replace(EARNINGS, filed=DAY)
    view = session(
        [(550, 1.0, 900_000), *ROWS, *LATER],
        reports=(SALE, unrelated, same_day),
    )
    found = day_signals(strategy, view)
    assert found == EXPECTED
    assert day_signals(strategy, view.upto(598)) == []
    assert day_signals(strategy, view.upto(599)) == EXPECTED
    check_no_lookahead(strategy, view, found, [550, 570, 598, 599, 600, 950])


@pytest.mark.parametrize(
    "kwargs",
    [
        {"reports": ()},
        {"reports": (replace(SALE, filed=DAY),)},
        {"reports": (replace(SALE, filed=date(2004, 8, 22)),)},
        {"reports": (replace(SALE, items=("9.01",)),)},
        {"reports": (replace(SALE, permaticker=2),)},
        {"reports": (replace(SALE, symbol="XYZ"),)},
        {"reports": (SALE, EARNINGS)},
        {"prior_close": 8.8},
        {"prior_close": 13.0},
        {"rows": ROWS[1:]},
        {"rows": [*ROWS[:2], ROWS[-1]]},
        {"rows": [*ROWS[:2], (598, 8.4, 7_000), ROWS[-1]]},
        {"rows": [*ROWS[:-1], (599, 9.3, 7_000)]},
        {"rows": [*ROWS[:-1], (599, 8.9, 4_400)]},
        {"rows": [(550, 8.9, 900_000), *ROWS], "adv": 2e6},
    ],
)
def test_requires_clean_typed_report_and_partial_recovery(kwargs):
    assert day_signals(runner.load_strategy(NAME, {}), session(**kwargs)) == []


@pytest.mark.parametrize("entry", [600, 601])
def test_simulator_expires_at_first_entry_minute_and_exits_same_day(entry):
    meta, config = runner.load_config(NAME, "development")
    strategy = runner.load_strategy(NAME, config["params"])
    view = session([*ROWS, (entry, 9.0, 8_000), LATER[-1]])
    trades = simulate_day(
        DayData(view, {"ABC": 10.2}),
        day_signals(strategy, view),
        risk=RiskConfig(**config["risk"]),
        config=FillConfig(**config["fills"]),
        costs=load(meta["cost_calibration"]),
    ).trades
    if entry == 600:
        (trade,) = trades
        assert (trade.entry_minute, trade.exit_minute, trade.exit_reason) == (600, 960, "auction")
    else:
        assert trades == []


def test_development_and_validation_configs_differ_only_by_dates():
    _, development = runner.load_config(NAME, "development")
    _, validation = runner.load_config(NAME, "validation")
    assert development.pop("period") == {"start": date(2003, 9, 10), "end": date(2016, 12, 30)}
    assert validation.pop("period") == {"start": date(2017, 1, 3), "end": date(2023, 11, 8)}
    assert development == validation
