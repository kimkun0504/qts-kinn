"""Frozen count acceleration, size ablation, share proxy and prefix/expiry checks."""

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
from kinn.features.base import LookaheadError
from kinn.risk.sizing import RiskConfig
from kinn.validation.event_study import measure
from tests.test_simulator import COSTS

SOURCE = Path(__file__).resolve().parents[1] / "strategies/fragmented_demand_burst/strategy.py"
SPEC = spec_from_file_location("fragmented_demand_burst", SOURCE)
MODULE = module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
PRICES = np.r_[np.linspace(10, 10.1, 6), np.linspace(10.2, 10.5, 5)]
VOLUME = np.r_[5000, np.full(5, 5000), np.full(5, 10000)]
COUNTS = np.r_[100, np.full(5, 100), np.full(5, 500)]


def stock(*, fragmented=True):
    prices = np.r_[PRICES, 10.51, 11, 11.1, 99]
    minute = np.r_[np.arange(579, 590), 590, 649, 650, 959]
    counts = COUNTS.copy()
    volume = VOLUME.copy()
    if not fragmented:
        volume[6:] = 15000
    return make_symbol_day(
        "ABC",
        1,
        minute,
        prices,
        prices,
        prices,
        prices,
        np.r_[volume, [20000] * 4],
        {"prev_close": 10, "adv20_prev": 2e6, "marketcap_prev": 100e6},
        transactions=np.r_[counts, [200] * 4],
    )


def view(bars):
    return DayView(date(2010, 1, 4), 570, 960, {"ABC": bars})


def test_exact_fragmentation_boundary_and_count_burst_boundary():
    counts = COUNTS.copy()
    counts[6:] = 400
    assert MODULE.base_event(PRICES, VOLUME, counts, 2e6) == (0.5, True)
    counts[-1] -= 1
    assert MODULE.base_event(PRICES, VOLUME, counts, 2e6) is None
    volumes = VOLUME.copy()
    volumes[-1] += 1
    factor, primary = MODULE.base_event(PRICES, volumes, COUNTS, 2e6)
    assert factor > 0.4 and primary
    volumes[6:] = 15000
    assert MODULE.base_event(PRICES, volumes, COUNTS, 2e6) == (0.6, False)


@pytest.mark.parametrize("failure", ["no_gain", "overextended", "turnover", "fraction", "missing"])
def test_base_activity_and_price_gates(failure):
    p, v, n = PRICES.copy(), VOLUME.astype(float), COUNTS.astype(float)
    adv = 2e6
    if failure == "no_gain":
        p[-1] = p[5]
    elif failure == "overextended":
        p[-1] = 1.06 * p[5]
    elif failure == "turnover":
        adv = 1e9
    elif failure == "fraction":
        n[2] += 0.5
    else:
        n[2] = np.nan
    assert MODULE.base_event(p, v, n, adv) is None


def test_exact_primary_subset_and_all_clock_prefixes():
    primary, control = MODULE.build({}), MODULE.build({"fragmented": False})
    data = view(stock())
    signals = day_signals(primary, data)
    assert len(signals) == 1 and signals == day_signals(control, data)
    assert signals[0].minute == 589 and signals[0].expire_minute == 590
    assert signals[0].max_hold_minutes == 60
    for strategy in (primary, control):
        check_no_lookahead(strategy, data, signals, list(range(575, 654)))
    unfiltered = view(stock(fragmented=False))
    assert not day_signals(primary, unfiltered) and len(day_signals(control, unfiltered)) == 1
    assert not day_signals(primary, replace(data, close_minute=780))


def test_share_proxy_uses_only_prior_columns_and_rejects_missing_values():
    bars = stock()
    for cap, price, eligible in (
        (200e6, 10, True),
        (200e6 + 1, 10, False),
        (100e6, None, False),
        (None, 10, False),
    ):
        changed = replace(bars, prior={**bars.prior, "marketcap_prev": cap, "prev_close": price})
        assert bool(day_signals(MODULE.build({}), view(changed))) is eligible
    assert MODULE.build({}).universe.max_marketcap == 300e6


def test_missing_bar_and_field_fail_without_imputation_and_future_values_do_not_matter():
    bars = stock()
    signals = day_signals(MODULE.build({}), view(bars))
    p, n = bars.close.copy(), bars.transactions.copy()
    p[-1], n[-1] = 0.01, 10000000
    assert day_signals(MODULE.build({}), view(replace(bars, close=p, transactions=n))) == signals
    keep = bars.minute != 585
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


def test_replay_catches_a_deliberate_future_count_condition():
    class Cheater(MODULE.FragmentedDemandBurst):
        def signals(self, data, features):
            found = super().signals(data, features)
            return found if data.symbols["ABC"].transactions[-1] == 200 else []

    strategy, data = Cheater(True), view(stock())
    with pytest.raises(LookaheadError):
        check_no_lookahead(strategy, data, day_signals(strategy, data), [589])


def test_registered_entry_expiry_timed_exit_and_study_convention():
    data = view(stock())
    (signal,) = day_signals(MODULE.build({}), data)
    _, cfg = runner.load_config("fragmented_demand_burst", "development")
    risk, fills = RiskConfig(**cfg["risk"]), FillConfig(**cfg["fills"])
    (trade,) = simulate_day(
        DayData(data, {"ABC": 99}), [signal], risk=risk, config=fills, costs=COSTS
    ).trades
    assert trade.entry_minute == 590 and trade.entry_price == pytest.approx(10.51)
    assert trade.exit_minute == 650 and trade.exit_price == pytest.approx(11.1)
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
    assert row["r_60"] == pytest.approx(11 / 10.51 - 1)
    bars = data.symbols["ABC"]
    keep = bars.minute != 590
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
    for params in ({"fragmented": 1}, {"ratio": 2}):
        with pytest.raises(ValueError, match="frozen boolean"):
            MODULE.build(params)
