"""Synthetic mathematical and missing-input checks; platform replay remains a prerequisite."""

import subprocess
import sys
from datetime import date
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

import numpy as np
import pytest

from kinn.core.types import CurrentReport
from kinn.engine.intraday.data import DayView, make_symbol_day
from kinn.engine.intraday.strategy import day_signals

SOURCE = Path(__file__).resolve().parents[1] / "strategies/earnings_trade_size_shift/strategy.py"
SPEC = spec_from_file_location("earnings_trade_size_shift", SOURCE)
MODULE = module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
VOLUME = np.array([1000] * 5 + [4000] * 5)
COUNTS = np.array([100] * 5 + [200] * 5)
PRICES = np.linspace(10.5, 11, 11)


def test_average_size_can_expand_while_count_increases_and_exact_boundary_passes():
    assert MODULE.trade_size_expansion(VOLUME, COUNTS) == 2
    assert MODULE.trade_size_expansion(VOLUME * 3, COUNTS * 3) == 2
    smaller = VOLUME.copy()
    smaller[-1] -= 1
    assert MODULE.trade_size_expansion(smaller, COUNTS) is None


@pytest.mark.parametrize(
    "counts",
    [
        np.full(10, 1),
        np.r_[np.full(5, 200), np.full(5, 100)],
        np.r_[COUNTS[:-1], 0],
        np.r_[COUNTS[:-1], float("nan")],
        np.r_[COUNTS[:-1], 200.5],
    ],
)
def test_sparse_declining_missing_and_fractional_counts_are_rejected(counts):
    assert MODULE.trade_size_expansion(VOLUME, counts) is None


def test_price_advance_liquidity_and_opening_auction_exclusion():
    volume = np.r_[100_000_000, VOLUME]
    counts = np.r_[float("nan"), COUNTS]
    assert MODULE.candidate_score(PRICES, volume, counts, 10, 2e6) == 2
    assert MODULE.candidate_score(PRICES, volume, counts, 11, 2e6) is None
    assert MODULE.candidate_score(np.linspace(10.5, 10.7, 11), volume, counts, 10, 2e6) is None
    assert MODULE.candidate_score(PRICES, volume, counts, 10, 1e9) is None


def test_shape_errors_are_explicit():
    with pytest.raises(ValueError, match="ten aligned"):
        MODULE.trade_size_expansion(VOLUME[:-1], COUNTS[:-1])
    with pytest.raises(ValueError, match="eleven aligned"):
        MODULE.candidate_score(PRICES, VOLUME, COUNTS, 10, 2e6)


def test_strategy_refuses_to_silently_impute_unavailable_transactions():
    volume = np.r_[100000, VOLUME]
    bars = make_symbol_day(
        "ABC",
        1,
        np.arange(570, 581),
        PRICES,
        PRICES,
        PRICES,
        PRICES,
        volume,
        {"prev_close": 10, "adv20_prev": 2e6},
    )
    report = CurrentReport("ABC", 1, date(2010, 1, 1), (22,), ("2.02",), True)
    view = DayView(date(2010, 1, 4), 570, 960, {"ABC": bars}, reports={"ABC": (report,)})
    with pytest.raises(ValueError, match="observed transaction counts"):
        day_signals(MODULE.build({}), view)
    assert not day_signals(MODULE.build({}), DayView(view.day, 570, 960, view.symbols))


def test_fixed_parameters_and_isolated_cli_load(tmp_path):
    with pytest.raises(ValueError, match="no parameters"):
        MODULE.build({"ratio": 1.5})
    code = "from kinn.run import load_strategy; s=load_strategy('earnings_trade_size_shift', {}); "
    code += "assert s.name == 'earnings_trade_size_shift'"
    result = subprocess.run(
        [sys.executable, "-I", "-c", code], cwd=tmp_path, capture_output=True, text=True, timeout=15
    )
    assert result.returncode == 0, result.stderr
