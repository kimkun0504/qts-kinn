"""Frozen signal mathematics and prefix replay on synthetic premarket bars."""

import subprocess
import sys
from datetime import date
from importlib.util import module_from_spec, spec_from_file_location
from math import log
from pathlib import Path

import numpy as np
import pytest

from kinn import run as runner
from kinn.engine.intraday.data import DayData, DayView, make_symbol_day
from kinn.engine.intraday.simulator import simulate_day
from kinn.engine.intraday.strategy import check_no_lookahead, day_signals
from kinn.risk.sizing import RiskConfig
from tests.test_simulator import COSTS

SOURCE = Path(__file__).resolve().parents[1] / "strategies/premarket_price_discovery/strategy.py"
SPEC = spec_from_file_location("premarket_discovery", SOURCE)
MODULE = module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
PRICES = np.array([10, 10.12, 10.24, 10.36, 10.48, 10.60])
VOLUME = np.full(6, 10_000)


def stock(prices=PRICES, volume=VOLUME, minutes=None):
    m = np.arange(420, 426) if minutes is None else np.asarray(minutes)
    return make_symbol_day(
        "ABC", 1, m, prices, prices, prices, prices, volume, {"prev_close": 8.5, "adv20_prev": 2e6}
    )


def test_mathematics_and_concentration_penalty():
    score = MODULE.discovery_score(PRICES, VOLUME)
    q = PRICES[1:] * VOLUME[1:]
    expected = log(1.06) * (q.sum() ** 2) / (5 * np.square(q).sum())
    assert score == pytest.approx(expected) and score > log(1.05)
    assert MODULE.discovery_score(PRICES, VOLUME * 2) == pytest.approx(score)
    concentrated = VOLUME.copy()
    concentrated[-1] *= 100
    assert MODULE.discovery_score(PRICES, concentrated) < log(1.05)
    choppy = np.array([10, 10.9, 9.8, 10.9, 9.9, 10.6])
    assert MODULE.discovery_score(choppy, VOLUME) < log(1.05)


@pytest.mark.parametrize(
    ("prices", "volume"),
    [
        (np.full(6, 10), VOLUME),
        (PRICES[::-1], VOLUME),
        (np.r_[PRICES[:-1], float("nan")], VOLUME),
        (PRICES, np.r_[VOLUME[:-1], 0]),
        (np.r_[0, PRICES[1:]], VOLUME),
    ],
)
def test_invalid_or_nonpositive_discovery_is_rejected(prices, volume):
    assert MODULE.discovery_score(prices, volume) is None


def test_shape_and_parameters_are_fixed():
    with pytest.raises(ValueError, match="six"):
        MODULE.discovery_score(PRICES[:-1], VOLUME[:-1])
    with pytest.raises(ValueError, match="no parameters"):
        MODULE.build({"threshold": 0.01})


def test_signal_liquidity_gap_and_minute_window():
    bars = stock()
    assert MODULE.first_candidate(bars, 8.5, 2e6)[0] == 425
    assert MODULE.first_candidate(bars, 10, 2e6) is None
    assert MODULE.first_candidate(stock(volume=np.full(6, 100)), 8.5, 2e6) is None
    assert MODULE.first_candidate(bars, 8.5, 1e9) is None
    assert MODULE.first_candidate(stock(minutes=[419, 420, 421, 422, 423, 425]), 8.5, 2e6) is None
    assert MODULE.first_candidate(stock(minutes=np.arange(419, 425)), 8.5, 2e6) is None
    assert MODULE.first_candidate(stock(minutes=np.arange(521, 527)), 8.5, 2e6) is None


def test_first_signal_prefix_replay_and_early_close():
    bars = stock()
    future = make_symbol_day(
        "ABC",
        1,
        np.r_[bars.minute, 426, 455, 456, 570, 959],
        np.r_[PRICES, 10.61, 11, 11, 99, 99],
        np.r_[PRICES, 10.61, 11, 11, 99, 99],
        np.r_[PRICES, 10.61, 11, 11, 99, 99],
        np.r_[PRICES, 10.61, 11, 11, 99, 99],
        np.r_[VOLUME, 10000, 10000, 10000, 10000, 10000],
        bars.prior,
    )
    view = DayView(date(2010, 1, 4), 570, 960, {"ABC": future})
    strategy = MODULE.build({})
    signals = day_signals(strategy, view)
    assert len(signals) == 1 and signals[0].minute == 425
    assert signals[0].limit_price == pytest.approx(PRICES[-1] * 1.01)
    assert signals[0].expire_minute == 426 and signals[0].max_hold_minutes == 30
    check_no_lookahead(strategy, view, signals, list(range(419, 961)))
    assert not day_signals(strategy, DayView(view.day, 570, 780, view.symbols))
    _, cfg = runner.load_config(strategy.name, "development")
    from kinn.engine.intraday.simulator import FillConfig

    result = simulate_day(
        DayData(view, {"ABC": 99}),
        signals,
        risk=RiskConfig(**cfg["risk"]),
        config=FillConfig(**cfg["fills"]),
        costs=COSTS,
    )
    (trade,) = result.trades
    assert trade.entry_minute == 426 and trade.exit_minute == 456
    assert trade.exit_price == 11 and not result.unresolved


def test_cli_load_without_repository_pythonpath(tmp_path):
    result = subprocess.run(
        [
            sys.executable,
            "-I",
            "-c",
            "from kinn.run import load_strategy; "
            "strategy = load_strategy('premarket_price_discovery', {}); "
            "assert strategy.name == 'premarket_price_discovery'",
        ],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert result.returncode == 0, result.stderr
