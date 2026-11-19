"""Frozen count windows, first-event ablation and deliberate lookahead canary."""

from dataclasses import replace
from datetime import date

import numpy as np
import pytest

from kinn import run as runner
from kinn.core.types import Signal
from kinn.engine.intraday.data import DayView, make_symbol_day
from kinn.engine.intraday.strategy import check_no_lookahead, day_signals
from kinn.features.base import LookaheadError

NAME = "air_pocket_reversal"
DAY = date(2010, 7, 1)
EXPECTED = [Signal("ABC", 600, expire_minute=601, max_hold_minutes=120)]


def strategy(primary=True):
    return runner.load_strategy(NAME, {"require_collapse": primary})


def module():
    return strategy().signals.__func__.__globals__


def session(*, falling=40, later=False):
    minute = np.arange(570, 723)
    n = len(minute)

    def stock(symbol, company, target=False):
        close = np.full(n, 10.0)
        counts = np.full(n, 100, dtype=np.int64)
        if target:
            close[16:29] = np.linspace(9.9, 8.3, 13)
            close[29:33] = [8.2, 8.3, 8.4, 8.5]
            counts[16:30] = falling
            if later:
                close[36:49] = np.linspace(9.9, 8.3, 13)
                close[49:53] = [8.2, 8.3, 8.4, 8.5]
                counts[36:50] = 1
        return make_symbol_day(
            symbol,
            company,
            minute,
            close,
            close,
            close,
            close,
            np.full(n, 50_000),
            {"prev_close": 10.0, "adv20_prev": 10e6, "marketcap_prev": 1e9},
            transactions=counts,
        )

    stocks = {f"P{i}": stock(f"P{i}", i + 1) for i in range(30)}
    stocks["ABC"] = stock("ABC", 100, True)
    return DayView(DAY, 570, 960, stocks)


def change_target(view, **changes):
    return replace(view, symbols={**view.symbols, "ABC": replace(view.symbols["ABC"], **changes)})


def test_registered_rate_normalization_exact_boundaries_and_no_overflow():
    fn = module()["collapsed"]
    assert fn(1500, 700)
    assert not fn(1500, 701)
    assert fn(15 * 10**20, 7 * 10**20)
    assert not fn(15 * 10**20, 7 * 10**20 + 1)


def test_count_windows_exclude_recovery_bar_and_precede_price_interval():
    view = session()
    bars = view.symbols["ABC"]
    fn = module()["activity_counts"]
    assert fn(bars, 600) == (1500, 560)
    counts = bars.transactions.copy()
    counts[30] = 10**8  # decision bar is tested for availability but excluded from the ratio
    assert fn(replace(bars, transactions=counts), 600) == (1500, 560)
    counts[15] += 1  # anchor bar is the final baseline bar
    assert fn(replace(bars, transactions=counts), 600) == (1501, 560)
    counts[16] += 1  # first decline bar
    assert fn(replace(bars, transactions=counts), 600) == (1501, 561)


def test_primary_control_subset_and_every_prefix():
    view = session()
    for primary in (True, False):
        st = strategy(primary)
        assert day_signals(st, view) == EXPECTED
        check_no_lookahead(st, view, EXPECTED, list(range(570, 724)))
    view = session(falling=100)
    assert not day_signals(strategy(), view)
    assert day_signals(strategy(False), view) == EXPECTED


@pytest.mark.parametrize(
    "failure",
    [
        "count_missing",
        "count_zero",
        "count_fraction",
        "count_nan",
        "volume_zero",
        "close_nan",
        "minute_missing",
    ],
)
def test_observed_history_is_required_for_both_variants(failure):
    view = session()
    bars = view.symbols["ABC"]
    if failure == "count_missing":
        bars = replace(bars, transactions=None)
    elif failure.startswith("count_"):
        counts = bars.transactions.astype(float)
        counts[5] = {"count_zero": 0, "count_fraction": 1.5, "count_nan": np.nan}[failure]
        bars = replace(bars, transactions=counts)
    elif failure == "volume_zero":
        volume = bars.volume.copy()
        volume[5] = 0
        bars = replace(bars, volume=volume)
    elif failure == "close_nan":
        close = bars.close.copy()
        close[5] = np.nan
        bars = replace(bars, close=close)
    else:
        keep = bars.minute != 575
        bars = replace(
            bars,
            **{
                field: getattr(bars, field)[keep]
                for field in ("minute", "open", "high", "low", "close", "volume", "transactions")
            },
        )
    view = replace(view, symbols={**view.symbols, "ABC": bars})
    assert not day_signals(strategy(), view)
    assert not day_signals(strategy(False), view)


def test_failed_first_event_cannot_be_rescued_by_later_activity_or_later_data():
    view = session(falling=100, later=True)
    assert day_signals(strategy(False), view) == EXPECTED
    assert not day_signals(strategy(), view)
    # Missing early history also prevents a later entry in the control.
    counts = view.symbols["ABC"].transactions.copy()
    counts[5] = 0
    assert not day_signals(strategy(False), change_target(view, transactions=counts))


def test_count_availability_does_not_remove_peers_and_both_endpoints_need_31():
    view = session()
    peer = view.symbols["P0"]
    # Peers supply only prices; their missing counts must not remove them from the reference.
    view = replace(view, symbols={**view.symbols, "P0": replace(peer, transactions=None)})
    assert day_signals(strategy(), view) == EXPECTED
    close = peer.close.copy()
    close[15] = np.nan
    view = replace(view, symbols={**view.symbols, "P0": replace(peer, close=close)})
    assert not day_signals(strategy(False), view.upto(600))
    assert all(s.minute > 600 for s in day_signals(strategy(False), view))


def test_future_count_and_price_perturbations_leave_past_signal_unchanged():
    view = session()
    bars = view.symbols["ABC"]
    counts, close = bars.transactions.copy(), bars.close.copy()
    counts[bars.minute > 600] = 10**8
    close[bars.minute > 600] = 100
    changed = change_target(view, transactions=counts, close=close)
    assert [s for s in day_signals(strategy(), changed) if s.minute <= 600] == EXPECTED


def test_deliberate_future_count_lookup_is_detected():
    base = strategy()

    class Cheater(type(base)):
        def signals(self, view, features):
            found = super().signals(view, features)
            return found if len(view.symbols["ABC"].transactions) > 50 else []

    st = Cheater(True)
    view = session()
    with pytest.raises(LookaheadError):
        check_no_lookahead(st, view, day_signals(st, view), [600])


def test_configs_only_differ_in_registered_ablation_and_validation_period():
    _, dev = runner.load_config(NAME, "development")
    _, control = runner.load_config(NAME, "development_control")
    _, validation = runner.load_config(NAME, "validation")
    assert control == {**dev, "params": {"require_collapse": False}}
    assert validation == {**dev, "period": {"start": date(2017, 1, 3), "end": date(2023, 11, 8)}}
    for params in ({"require_collapse": 1}, {"threshold": 0.25}):
        with pytest.raises(ValueError, match="frozen boolean"):
            runner.load_strategy(NAME, params)


@pytest.mark.parametrize(("late", "close_minute"), [(False, 960), (True, 960), (False, 700)])
def test_next_clock_minute_expiry_and_two_hour_exit_with_auction_fallback(late, close_minute):
    from kinn.costs.model import load
    from kinn.engine.intraday.data import DayData
    from kinn.engine.intraday.simulator import FillConfig, simulate_day
    from kinn.risk.sizing import RiskConfig

    meta, config = runner.load_config(NAME, "development")
    view = replace(session(), close_minute=close_minute)
    if late:
        bars = view.symbols["ABC"]
        keep = bars.minute != 601
        view = change_target(
            view,
            **{
                field: getattr(bars, field)[keep]
                for field in ("minute", "open", "high", "low", "close", "volume", "transactions")
            },
        )
    trades = simulate_day(
        DayData(view, {"ABC": 9.2}),
        day_signals(strategy(), view),
        risk=RiskConfig(**config["risk"]),
        config=FillConfig(**config["fills"]),
        costs=load(meta["cost_calibration"]),
    ).trades
    if late:
        assert not trades
    else:
        (trade,) = trades
        assert trade.entry_minute == 601
        assert (trade.exit_minute, trade.exit_reason) == (
            (721, "time") if close_minute == 960 else (700, "auction")
        )
