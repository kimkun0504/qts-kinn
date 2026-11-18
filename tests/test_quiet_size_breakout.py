"""Synthetic fixed-time price/print-size conditions, ablation and prefix replay."""

from dataclasses import replace
from datetime import date
from importlib.util import module_from_spec, spec_from_file_location
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

SOURCE = Path(__file__).resolve().parents[1] / "strategies/quiet_size_breakout/strategy.py"
SPEC = spec_from_file_location("quiet_size_breakout", SOURCE)
MODULE = module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
PRICES = np.r_[np.linspace(9.95, 10, 10), 10.08]
VOLUME = np.r_[10000, np.full(5, 2000), np.full(5, 6000)]
COUNTS = np.r_[100, np.full(5, 100), np.full(5, 150)]


def test_exact_trade_size_boundary_and_integer_comparison():
    assert MODULE.base_event(PRICES, VOLUME, COUNTS, 2e6) == (2, True)
    assert MODULE.base_event(PRICES, VOLUME * 2, COUNTS * 2, 4e6) == (2, True)
    smaller = VOLUME.copy()
    smaller[-1] -= 1
    factor, eligible = MODULE.base_event(PRICES, smaller, COUNTS, 2e6)
    assert factor < 2 and not eligible


def test_count_persistence_and_print_size_are_separate_primary_requirements():
    more = COUNTS.copy()
    more[6:] = 200
    assert MODULE.base_event(PRICES, VOLUME, more, 2e6) == (1.5, False)
    fewer = COUNTS.copy()
    fewer[6:] = 80
    factor, eligible = MODULE.base_event(PRICES, VOLUME, fewer, 2e6)
    assert factor > 2 and not eligible


@pytest.mark.parametrize("failure", ["range", "no_breakout", "overextended", "turnover", "counts"])
def test_base_event_rejects_unqualified_price_activity_and_missing_counts(failure):
    p, v, n = PRICES.copy(), VOLUME.copy(), COUNTS.astype(float)
    adv = 2e6
    if failure == "range":
        p[0] = 9.5
    elif failure == "no_breakout":
        p[-1] = 10.04
    elif failure == "overextended":
        p[-1] = 10.4
    elif failure == "turnover":
        adv = 1e9
    else:
        n[4] = np.nan
    assert MODULE.base_event(p, v, n, adv) is None


def stock(*, large=True):
    prices = np.r_[PRICES, 10.1, 10.5, 10.6, 99]
    minute = np.r_[np.arange(589, 600), 600, 719, 720, 959]
    volume = np.r_[VOLUME, [20000] * 4]
    counts = COUNTS.copy()
    if not large:
        counts[6:] = 200
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
        transactions=np.r_[counts, [200] * 4],
    )


def view(bars):
    return DayView(date(2010, 1, 4), 570, 960, {"ABC": bars})


def test_matched_control_and_full_prefix_replay():
    data = view(stock())
    primary = MODULE.build({})
    control = MODULE.build({"large_prints": False})
    signals = day_signals(primary, data)
    assert len(signals) == 1 and signals == day_signals(control, data)
    assert signals[0].minute == 599 and signals[0].expire_minute == 600
    for strategy in (primary, control):
        check_no_lookahead(strategy, data, signals, list(range(588, 722)))
    unfiltered = view(stock(large=False))
    assert not day_signals(primary, unfiltered) and len(day_signals(control, unfiltered)) == 1
    assert not day_signals(primary, replace(data, close_minute=780))


def test_future_counts_and_prices_cannot_create_or_change_the_fixed_event():
    data = view(stock())
    signals = day_signals(MODULE.build({}), data)
    bars = data.symbols["ABC"]
    counts = bars.transactions.copy()
    counts[-1] = 10000000
    prices = bars.close.copy()
    prices[-1] = 1000
    changed = replace(bars, transactions=counts, close=prices)
    assert day_signals(MODULE.build({}), replace(data, symbols={"ABC": changed})) == signals
    keep = bars.minute != 595
    missing = replace(
        bars,
        **{
            k: getattr(bars, k)[keep]
            for k in ("minute", "open", "high", "low", "close", "volume", "transactions")
        },
    )
    assert not day_signals(MODULE.build({}), view(missing))
    with pytest.raises(ValueError, match="observed transaction counts"):
        day_signals(MODULE.build({}), view(replace(bars, transactions=None)))


def test_market_entry_expiry_and_timed_exit_follow_the_registered_clock():
    data = view(stock())
    (signal,) = day_signals(MODULE.build({}), data)
    _, cfg = runner.load_config("quiet_size_breakout", "development")
    risk, fills = RiskConfig(**cfg["risk"]), FillConfig(**cfg["fills"])
    (trade,) = simulate_day(
        DayData(data, {"ABC": 99}), [signal], risk=risk, config=fills, costs=COSTS
    ).trades
    assert trade.entry_minute == 600 and trade.entry_price == 10.1
    assert trade.exit_minute == 720 and trade.exit_price == pytest.approx(10.6)
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
    assert row["r_120"] == pytest.approx(10.5 / 10.1 - 1)
    bars = data.symbols["ABC"]
    keep = bars.minute != 600
    missing = replace(
        bars,
        **{
            k: getattr(bars, k)[keep]
            for k in ("minute", "open", "high", "low", "close", "volume", "transactions")
        },
    )
    result = simulate_day(
        DayData(view(missing), {}), [signal], risk=risk, config=fills, costs=COSTS
    )
    assert not result.trades and result.unfilled == 1


def test_shape_and_parameters_are_fixed():
    with pytest.raises(ValueError, match="eleven aligned"):
        MODULE.base_event(PRICES[:-1], VOLUME[:-1], COUNTS[:-1], 2e6)
    for params in ({"large_prints": 1}, {"threshold": 1.5}):
        with pytest.raises(ValueError, match="frozen boolean"):
            MODULE.build(params)
