"""Registered fragmentation ablation and replay on synthetic windows only."""

from dataclasses import replace
from datetime import date
from importlib.util import module_from_spec, spec_from_file_location
from math import log
from pathlib import Path

import numpy as np
import pytest

from kinn import run as runner
from kinn.engine.intraday.data import DayData, DayView, make_symbol_day
from kinn.engine.intraday.simulator import FillConfig, simulate_day
from kinn.engine.intraday.strategy import check_no_lookahead, day_signals
from kinn.risk.sizing import RiskConfig
from kinn.validation.event_study import measure
from tests.test_simulator import COSTS

SOURCE = (
    Path(__file__).resolve().parents[1] / "strategies/fragmented_selloff_exhaustion/strategy.py"
)
SPEC = spec_from_file_location("fragmented_selloff_exhaustion", SOURCE)
MODULE = module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
PRICES = np.r_[np.linspace(10, 9, 11), [8.98, 8.96, 8.94, 8.91, 9.01]]
VOLUME = np.r_[20000, np.full(10, 20000), np.full(5, 12000)]
COUNTS = np.r_[200, np.full(10, 200), np.full(5, 400)]


def test_score_and_fragmentation_follow_the_definition():
    score, fragmented = MODULE.base_event(PRICES, VOLUME, COUNTS, 2e6)
    assert score == pytest.approx(1 - 9.01 / 10) and fragmented
    lower = PRICES.copy()
    lower[-2:] = [8.8, 8.9]
    n1, n2 = 2000, 2000
    expected = (1 - 8.9 / 10) * (1 - (log(9 / 8.9) / n2) / (log(10 / 9) / n1))
    assert MODULE.base_event(lower, VOLUME, COUNTS, 2e6)[0] == pytest.approx(expected)
    assert MODULE.base_event(PRICES, VOLUME * 2, COUNTS * 2, 4e6) == pytest.approx((score, True))


def test_control_keeps_the_same_base_event_without_the_fragmentation_filter():
    event = MODULE.base_event(PRICES, VOLUME, np.full(16, 200), 2e6)
    assert event is not None and not event[1]


@pytest.mark.parametrize(
    "change", ["shock", "discount", "recovery", "impact", "liquidity", "count"]
)
def test_base_event_rejects_failed_economic_and_input_gates(change):
    p, v, n = PRICES.copy(), VOLUME.copy(), COUNTS.astype(float)
    adv = 2e6
    if change == "shock":
        p[10] = 9.1
    elif change == "discount":
        p[-1] = 9.3
    elif change == "recovery":
        p[-1] = 8.95
    elif change == "impact":
        p[11:] = [8.5, 8.4, 8.2, 7.9, 8.0]
    elif change == "liquidity":
        adv = 1e9
    else:
        n[4] = np.nan
    assert MODULE.base_event(p, v, n, adv) is None


def stock(*, fragmented=True, later=False):
    prices = PRICES.copy()
    minute = np.arange(585, 601)
    volume = VOLUME.copy()
    counts = COUNTS.copy() if fragmented else np.full(16, 200)
    if later:
        prices = np.r_[prices, PRICES]
        minute = np.r_[minute, np.arange(625, 641)]
        volume = np.r_[volume, VOLUME]
        counts = np.r_[counts, COUNTS]
    prices = np.r_[prices, 9.02, 9.6, 9.7, 99]
    minute = np.r_[minute, 641 if later else 601, 720, 721, 959]
    volume = np.r_[volume, [20000] * 4]
    counts = np.r_[counts, [200] * 4]
    return make_symbol_day(
        "ABC",
        1,
        minute,
        prices,
        prices,
        prices,
        prices,
        volume,
        {"prev_close": 10, "adv20_prev": 2e6},
        transactions=counts,
    )


def view(bars):
    return DayView(date(2010, 1, 4), 570, 960, {"ABC": bars})


def test_primary_is_exact_control_subset_and_both_replay_with_future_removed():
    data = view(stock())
    primary, control = MODULE.build({"fragmented": True}), MODULE.build({"fragmented": False})
    signals = day_signals(primary, data)
    assert len(signals) == 1 and signals == day_signals(control, data)
    assert signals[0].minute == 600 and signals[0].expire_minute == 601
    for strategy in (primary, control):
        check_no_lookahead(strategy, data, signals, list(range(584, 723)))
    assert not day_signals(primary, replace(data, close_minute=780))


def test_later_fragmented_event_cannot_rescue_an_excluded_first_base_event():
    data = view(stock(fragmented=False, later=True))
    primary, control = MODULE.build({}), MODULE.build({"fragmented": False})
    assert not day_signals(primary, data)
    assert day_signals(control, data)[0].minute == 600
    check_no_lookahead(primary, data, [], list(range(584, 723)))


def test_missing_clock_bar_and_unavailable_counts_are_not_imputed():
    bars = stock()
    keep = np.arange(len(bars.minute)) != 4
    missing = replace(
        bars,
        **{
            k: getattr(bars, k)[keep]
            for k in ("minute", "open", "high", "low", "close", "volume", "transactions")
        },
    )
    assert not day_signals(MODULE.build({}), view(missing))
    with pytest.raises(ValueError, match="observed transactions"):
        day_signals(MODULE.build({}), view(replace(bars, transactions=None)))


def test_next_clock_expiry_and_registered_two_hour_market_exit():
    data = view(stock())
    (signal,) = day_signals(MODULE.build({}), data)
    _, cfg = runner.load_config("fragmented_selloff_exhaustion", "development")
    risk, fills = RiskConfig(**cfg["risk"]), FillConfig(**cfg["fills"])
    (trade,) = simulate_day(
        DayData(data, {"ABC": 99}), [signal], risk=risk, config=fills, costs=COSTS
    ).trades
    assert trade.entry_minute == 601 and trade.entry_price == 9.02
    assert trade.exit_minute == 721 and trade.exit_price == 9.7
    row = measure(
        data.day,
        data.symbols["ABC"],
        signal,
        open_minute=570,
        close_minute=960,
        official_close=99,
        costs=COSTS,
        position_dollars=2000,
    )
    assert row["r_120"] == pytest.approx(9.6 / 9.02 - 1)  # legacy study's close mark, not exit fill
    bars = data.symbols["ABC"]
    keep = bars.minute != 601
    no_next = replace(
        bars,
        **{
            k: getattr(bars, k)[keep]
            for k in ("minute", "open", "high", "low", "close", "volume", "transactions")
        },
    )
    result = simulate_day(
        DayData(view(no_next), {}), [signal], risk=risk, config=fills, costs=COSTS
    )
    assert not result.trades and result.unfilled == 1


def test_parameters_and_shape_are_fixed():
    with pytest.raises(ValueError, match="sixteen"):
        MODULE.base_event(PRICES[:-1], VOLUME[:-1], COUNTS[:-1], 2e6)
    for params in ({"fragmented": 1}, {"threshold": 0.04}):
        with pytest.raises(ValueError, match="frozen boolean"):
            MODULE.build(params)
