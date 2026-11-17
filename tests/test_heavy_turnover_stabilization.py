"""Check the ordered price and turnover pattern and next-minute execution."""

from datetime import date

import pytest

from kinn import run as runner
from kinn.core.types import Signal
from kinn.costs.model import load
from kinn.engine.intraday.data import DayData, DayView, make_symbol_day
from kinn.engine.intraday.simulator import FillConfig, simulate_day
from kinn.engine.intraday.strategy import check_no_lookahead, day_signals
from kinn.risk.sizing import RiskConfig

NAME = "heavy_turnover_stabilization"
DAY = date(2016, 12, 2)
SHOCK = [(570 + i, round(10.0 - i * 0.08, 2), 6_000) for i in range(16)]
STABLE = [
    (586, 8.75, 12_000),
    (587, 8.70, 12_000),
    (588, 8.85, 6_000),
    (589, 8.83, 12_000),
    (590, 8.93, 6_000),
]
ROWS = [*SHOCK, *STABLE]
EXPECTED = [Signal("ABC", 590, expire_minute=591, max_hold_minutes=60)]


def session(rows=ROWS, *, adv=3e6, close_minute=960):
    minutes, prices, volumes = zip(*rows, strict=True)
    stock = make_symbol_day(
        "ABC", 1, minutes, prices, prices, prices, prices, volumes, {"adv20_prev": adv}
    )
    return DayView(DAY, 570, close_minute, {"ABC": stock})


def test_first_signal_requires_completed_window_and_passes_prefix_replay():
    strategy = runner.load_strategy(NAME, {})
    view = session([(555, 50, 1_000_000), *ROWS, (591, 9.1, 8_000), (900, 10.4, 8_000)])
    found = day_signals(strategy, view)
    assert found == EXPECTED
    assert day_signals(strategy, view.upto(589)) == []
    assert day_signals(strategy, view.upto(590)) == EXPECTED
    check_no_lookahead(strategy, view, found, [555, 570, 585, 589, 590, 591, 900])


@pytest.mark.parametrize(
    "kwargs",
    [
        {"rows": [(570, 9.7, 6_000), *ROWS[1:]]},
        {"rows": [*ROWS[:8], *ROWS[9:]]},
        {"rows": [*ROWS[:8], (578, 9.36, 0), *ROWS[9:]]},
        {"rows": [*ROWS[:8], (578, float("nan"), 6_000), *ROWS[9:]]},
        {"rows": [(minute - 1, price, size) for minute, price, size in ROWS]},
        {"rows": [*SHOCK, (586, 8.60, 12_000), *STABLE[1:]]},
        {"rows": [*SHOCK, (586, 9.20, 12_000), *STABLE[1:]]},
        {"rows": [*ROWS[:-1], (590, 8.87, 6_000)]},
        {
            "rows": [
                *SHOCK,
                *[(minute, price, 1_000) for minute, price, _ in STABLE[:-1]],
                STABLE[-1],
            ]
        },
        {
            "rows": [
                *SHOCK,
                *[(minute, price, 1_000) for minute, price, _ in STABLE[:-1]],
                (590, 8.93, 40_000),
            ]
        },
        {"rows": [*ROWS[:-1], (590, 8.93, 4_000)]},
        {"rows": [(minute + 296, price, size) for minute, price, size in ROWS]},
        {"close_minute": 664},
        {"adv": 12e6},
    ],
)
def test_rejects_ineligible_shock_or_stabilization(kwargs):
    assert day_signals(runner.load_strategy(NAME, {}), session(**kwargs)) == []


@pytest.mark.parametrize("entry", [591, 592])
def test_simulator_uses_order_expiry_and_one_hour_hold(entry):
    meta, config = runner.load_config(NAME, "development")
    strategy = runner.load_strategy(NAME, config["params"])
    view = session([*ROWS, (entry, 9.1, 8_000), (651, 9.5, 8_000), (652, 9.6, 8_000)])
    trades = simulate_day(
        DayData(view, {"ABC": 10.2}),
        day_signals(strategy, view),
        risk=RiskConfig(**config["risk"]),
        config=FillConfig(**config["fills"]),
        costs=load(meta["cost_calibration"]),
    ).trades
    if entry == 591:
        (trade,) = trades
        assert (trade.entry_minute, trade.exit_minute, trade.exit_reason) == (591, 651, "time")
    else:
        assert trades == []


def test_development_and_validation_configs_differ_only_by_dates():
    _, development = runner.load_config(NAME, "development")
    _, validation = runner.load_config(NAME, "validation")
    assert development.pop("period") == {"start": date(2003, 9, 10), "end": date(2016, 12, 30)}
    assert validation.pop("period") == {"start": date(2017, 1, 3), "end": date(2023, 11, 8)}
    assert development == validation
