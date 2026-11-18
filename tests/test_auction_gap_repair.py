"""The premarket anchor and first-minute decision on synthetic bars only."""

import dataclasses
import subprocess
import sys
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
from kinn.validation.event_study import measure_extended
from tests.test_simulator import COSTS, flat

SOURCE = Path(__file__).resolve().parents[1] / "strategies/auction_gap_repair/strategy.py"
SPEC = spec_from_file_location("auction_gap_repair", SOURCE)
MODULE = module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def stock(rows=None, *, prev=10, adv=2e6):
    chosen = [flat(m, 12) for m in range(540, 570)]
    chosen += [
        (570, 10.5, 10.9, 10.4, 10.8, 10000),
        flat(571, 10.8),
        flat(600, 11.5),
        flat(601, 11.5),
    ]
    cols = list(zip(*(chosen if rows is None else rows), strict=True))
    return make_symbol_day("ABC", 1, *cols, {"prev_close": prev, "adv20_prev": adv})


def view(bars=None):
    return DayView(date(2010, 1, 4), 570, 960, {"ABC": stock() if bars is None else bars})


def test_weighted_median_is_order_invariant_and_uses_lower_half_boundary():
    prices, volume = np.array([100, 11, 10]), np.array([1, 49, 50])
    assert MODULE.weighted_median(prices, volume) == 10
    assert MODULE.weighted_median(prices[::-1], volume[::-1]) == 10
    assert MODULE.weighted_median(np.array([10, 12]), np.array([50, 50])) == 10
    assert MODULE.weighted_median(np.array([10, 12]), np.array([49, 51])) == 12


@pytest.mark.parametrize(
    ("prices", "volume"),
    [
        ([], []),
        ([10, 11], [1]),
        ([10, float("nan")], [1, 1]),
        ([10, 11], [1, 0]),
    ],
)
def test_weighted_median_rejects_invalid_inputs(prices, volume):
    with pytest.raises(ValueError, match="weighted median"):
        MODULE.weighted_median(np.array(prices), np.array(volume))


def test_reference_excludes_earlier_and_regular_prices_and_rejects_stale_anchor():
    bars = stock()
    assert MODULE.premarket_reference(bars, 10, 2e6) == 12
    changed = dataclasses.replace(bars, close=np.r_[bars.close[:30], 100, 100, 100, 100])
    assert MODULE.premarket_reference(changed, 10, 2e6) == 12
    early = [flat(539, 1000)] + [flat(m, 12) for m in range(540, 570)]
    assert MODULE.premarket_reference(stock(early), 10, 2e6) == 12
    assert MODULE.premarket_reference(bars.upto(568), 10, 2e6) is None
    stale = [flat(m, 12) for m in range(540, 569)] + [flat(569, 11.7)]
    assert MODULE.premarket_reference(stock(stale), 10, 2e6) is None


def test_reference_requires_distribution_turnover_and_prior_rally():
    assert MODULE.premarket_reference(stock(), 11, 2e6) is None
    assert MODULE.premarket_reference(stock(), 10, 1e9) is None
    sparse = [flat(m, 12) for m in range(556, 570)]
    assert MODULE.premarket_reference(stock(sparse), 10, 2e6) is None
    illiquid = [flat(m, 12, 100) for m in range(540, 570)]
    assert MODULE.premarket_reference(stock(illiquid), 10, 2e6) is None
    weak_last = [flat(m, 12) for m in range(540, 569)] + [flat(569, 12, 100)]
    assert MODULE.premarket_reference(stock(weak_last), 10, 2e6) is None


def test_decision_and_prefix_replay_use_only_premarket_and_first_completed_minute():
    strategy = MODULE.build({})
    data = view()
    (signal,) = day_signals(strategy, data)
    assert signal.minute == 570 and signal.limit_price == pytest.approx(10.8 * 1.005)
    assert signal.expire_minute == 571 and signal.max_hold_minutes == 30
    check_no_lookahead(strategy, data, [signal], list(range(539, 602)))
    assert not day_signals(strategy, dataclasses.replace(data, close_minute=780))
    assert not day_signals(strategy, view(data.symbols["ABC"].upto(569)))


@pytest.mark.parametrize(
    ("open_", "close", "volume"),
    [
        (10.9, 11.0, 10000),
        (10.5, 10.59, 10000),
        (10.5, 11.5, 10000),
        (10.5, 10.8, 100),
    ],
)
def test_rejects_small_discount_no_recovery_no_remaining_discount_and_inactivity(
    open_, close, volume
):
    rows = [flat(m, 12) for m in range(540, 570)]
    rows.append((570, open_, max(open_, close), min(open_, close), close, volume))
    assert not day_signals(MODULE.build({}), view(stock(rows)))


def test_inclusive_recovery_and_discount_boundaries():
    rows = [flat(m, 12) for m in range(540, 570)]
    rows.append((570, 10.8, 10.908, 10.8, 10.908, 10000))
    assert len(day_signals(MODULE.build({}), view(stock(rows)))) == 1


def test_capped_entry_and_exit_study_match_and_the_opening_low_is_never_paid():
    data = view()
    signal = day_signals(MODULE.build({}), data)[0]
    _, cfg = runner.load_config("auction_gap_repair", "development")
    fills = FillConfig(**cfg["fills"])
    risk = RiskConfig(**cfg["risk"])
    (trade,) = simulate_day(
        DayData(data, {"ABC": 999}), [signal], risk=risk, config=fills, costs=COSTS
    ).trades
    assert trade.entry_minute == 571 and trade.entry_price == 10.8
    assert trade.exit_minute == 601 and trade.exit_price == 11.5
    row = measure_extended(
        data.day,
        data.symbols["ABC"],
        signal,
        config=fills,
        costs=COSTS,
        position_dollars=risk.position_dollars,
    )
    assert row["r_30"] - row["fees"] - row["slippage"] == pytest.approx(trade.net / trade.notional)
    missing = [flat(m, 12) for m in range(540, 570)]
    missing += [(570, 10.5, 10.9, 10.4, 10.8, 10000), flat(572, 10.7), flat(602, 11.5)]
    result = simulate_day(
        DayData(view(stock(missing)), {}), [signal], risk=risk, config=fills, costs=COSTS
    )
    assert not result.trades and result.unfilled == 1


def test_fixed_parameters_and_cli_load_outside_repository(tmp_path):
    with pytest.raises(ValueError, match="no parameters"):
        MODULE.build({"discount": 0.05})
    result = subprocess.run(
        [
            sys.executable,
            "-I",
            "-c",
            "from kinn.run import load_strategy; s = load_strategy('auction_gap_repair', {}); "
            "assert s.name == 'auction_gap_repair'",
        ],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert result.returncode == 0, result.stderr
