"""Synthetic mathematical and missing-input checks; platform replay remains a prerequisite."""

import subprocess
import sys
from dataclasses import replace
from datetime import date
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

import numpy as np
import pytest

from kinn import run as runner
from kinn.core.types import CurrentReport, Signal
from kinn.engine.intraday.data import DayData, DayView, make_symbol_day
from kinn.engine.intraday.simulator import FillConfig, simulate_day
from kinn.engine.intraday.strategy import check_no_lookahead, day_signals
from kinn.features.base import LookaheadError
from kinn.risk.sizing import RiskConfig
from kinn.validation.event_study import measure_extended
from tests.test_simulator import COSTS

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


def complete_view(counts=None):
    prices = np.r_[PRICES, 11, 12, 12, 99]
    volume = np.r_[100000, VOLUME, 10000, 10000, 10000, 10000]
    observed = np.r_[1000, COUNTS, 100, 100, 100, 100] if counts is None else counts
    bars = make_symbol_day(
        "ABC",
        1,
        np.r_[np.arange(570, 581), 581, 700, 701, 959],
        prices,
        prices,
        prices,
        prices,
        volume,
        {"prev_close": 10, "adv20_prev": 2e6},
        transactions=observed,
    )
    report = CurrentReport("ABC", 1, date(2010, 1, 1), (22,), ("2.02",), True)
    return DayView(date(2010, 1, 4), 570, 960, {"ABC": bars}, reports={"ABC": (report,)})


def test_full_prefix_replay_truncates_future_counts_and_preserves_the_frozen_signal():
    view = complete_view()
    strategy = MODULE.build({})
    (signal,) = day_signals(strategy, view)
    assert signal.minute == 580 and signal.expire_minute == 581
    assert signal.limit_price == pytest.approx(1.005 * 11)
    check_no_lookahead(strategy, view, [signal], list(range(568, 703)))
    assert not day_signals(strategy, replace(view, close_minute=780))
    # Later print counts cannot alter a decision already made at 09:40.
    changed = np.r_[1000, COUNTS, 99999999, 99999999, 99999999, 99999999]
    assert day_signals(strategy, complete_view(changed)) == [signal]


def test_prefix_canary_detects_deliberate_use_of_future_transaction_counts():
    view = complete_view()
    bars = view.symbols["ABC"]
    counts = bars.transactions.copy()
    counts[-1] = 1000000
    changed = replace(view, symbols={"ABC": replace(bars, transactions=counts)})

    class FutureCountBuyer:
        name, features = "future_count_canary", ()

        def signals(self, day, features):
            stock = day.symbols["ABC"]
            return (
                [Signal("ABC", 570)]
                if len(stock.minute) and stock.transactions[-1] > 100000
                else []
            )

    cheat = FutureCountBuyer()
    with pytest.raises(LookaheadError, match="later bars are removed"):
        check_no_lookahead(cheat, changed, day_signals(cheat, changed), [580])


@pytest.mark.parametrize("change", ["same_day", "wrong_company", "not_earnings"])
def test_only_matching_pre_session_earnings_are_available(change):
    view = complete_view()
    (report,) = view.reports["ABC"]
    bad = replace(
        report,
        **(
            {"filed": view.day}
            if change == "same_day"
            else {"permaticker": 2}
            if change == "wrong_company"
            else {"earnings": False}
        ),
    )
    assert not day_signals(MODULE.build({}), replace(view, reports={"ABC": (bad,)}))


def test_missing_minute_and_missing_window_count_do_not_create_a_signal():
    view = complete_view()
    bars = view.symbols["ABC"]
    missing = np.arange(len(bars.minute)) != 5
    trimmed = replace(
        bars,
        **{
            k: getattr(bars, k)[missing]
            for k in ("minute", "open", "high", "low", "close", "volume", "transactions")
        },
    )
    assert not day_signals(MODULE.build({}), replace(view, symbols={"ABC": trimmed}))
    counts = bars.transactions.astype(float)
    counts[5] = np.nan
    assert not day_signals(
        MODULE.build({}), replace(view, symbols={"ABC": replace(bars, transactions=counts)})
    )


def test_matched_entry_and_two_hour_liquidation_use_the_registered_execution_policy():
    view = complete_view()
    (signal,) = day_signals(MODULE.build({}), view)
    _, cfg = runner.load_config("earnings_trade_size_shift", "development")
    fills = FillConfig(**cfg["fills"])
    risk = RiskConfig(**cfg["risk"])
    result = simulate_day(
        DayData(view, {"ABC": 99}), [signal], risk=risk, config=fills, costs=COSTS
    )
    (trade,) = result.trades
    assert trade.entry_minute == 581 and trade.entry_price == 11
    assert trade.exit_minute == 701 and trade.exit_price == 12 and not result.unresolved
    row = measure_extended(
        view.day,
        view.symbols["ABC"],
        signal,
        config=fills,
        costs=COSTS,
        position_dollars=risk.position_dollars,
    )
    assert row["r_120"] - row["fees"] - row["slippage"] == pytest.approx(trade.net / trade.notional)
    assert row["r_120"] - row["fees"] - 2 * row["slippage"] == pytest.approx(
        trade.net_2x / trade.notional
    )
