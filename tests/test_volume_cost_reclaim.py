"""Reference algebra, history availability, first-event selection and replay."""

from dataclasses import replace
from datetime import date

import numpy as np
import pytest

from kinn import run as runner
from kinn.core.types import Signal
from kinn.engine.intraday.data import DayView, make_symbol_day
from kinn.engine.intraday.strategy import check_no_lookahead, day_signals
from kinn.features.base import LookaheadError

NAME = "volume_cost_reclaim"
DAY = date(2010, 7, 1)
EXPECTED = [Signal("ABC", 600, expire_minute=601, max_hold_minutes=120)]


def strategy(primary=True):
    return runner.load_strategy(NAME, {"require_reference": primary})


def module():
    return strategy().signals.__func__.__globals__


def session(*, rejected=False, later=False):
    minute = np.arange(570, 723)
    n = len(minute)

    def stock(symbol, company, target=False):
        close = np.full(n, 10.0)
        volume = np.full(n, 50_000, dtype=np.int64)
        if target:
            close[16:29] = np.linspace(9.9, 9.05, 13)
            close[29:33] = [9.0, 9.15, 9.2, 9.3]
            volume[28:30] = 2_500_000
            if later:
                close[36:49] = np.linspace(9.9, 9.05, 13)
                close[49:53] = [9.0, 9.15, 9.2, 9.3]
                volume[48:50] = 2_500_000
        high = close.copy()
        if target:
            high[28:30] += 0.05
            if later:
                high[48:50] += 0.05
            if rejected:
                high[16] = 1000
        return make_symbol_day(
            symbol,
            company,
            minute,
            close,
            high,
            close,
            close,
            volume,
            {"prev_close": 10.0, "adv20_prev": 10e6, "marketcap_prev": 1e9},
        )

    stocks = {f"P{i}": stock(f"P{i}", i + 1) for i in range(30)}
    stocks["ABC"] = stock("ABC", 100, True)
    return DayView(DAY, 570, 960, stocks)


def change(view, **fields):
    return replace(view, symbols={**view.symbols, "ABC": replace(view.symbols["ABC"], **fields)})


def test_weighted_reference_excludes_anchor_and_recovery_bar():
    bars = session().symbols["ABC"]
    fn = module()["reference_terms"]
    weighted, shares = fn(bars, 600)
    assert shares == sum(map(int, bars.volume[16:30]))
    assert weighted == pytest.approx(sum(bars.high[16:30] * bars.volume[16:30]))
    high, volume = bars.high.copy(), bars.volume.copy()
    high[15] = high[30] = 1e9
    volume[15] = volume[30] = 10**10
    assert fn(replace(bars, high=high, volume=volume), 600) == (weighted, shares)


def test_reference_boundary_and_highs_are_used_instead_of_closes():
    fn = module()["above_reference"]
    assert fn(10.0, 140_000.0, 14_000)
    assert not fn(9.9999, 140_000.0, 14_000)
    assert day_signals(strategy(), session()) == EXPECTED
    rejected = session(rejected=True)
    assert day_signals(strategy(False), rejected) == EXPECTED
    assert not day_signals(strategy(), rejected)
    bars = rejected.symbols["ABC"]
    assert 9.15 * sum(bars.volume[16:30]) > sum(bars.close[16:30] * bars.volume[16:30])
    assert 9.15 * sum(bars.volume[16:30]) < sum(bars.high[16:30] * bars.volume[16:30])


def test_reference_is_invariant_to_common_volume_units():
    bars = session().symbols["ABC"]
    fn = module()["reference_terms"]
    above = module()["above_reference"]
    original = fn(bars, 600)
    scaled = fn(replace(bars, volume=bars.volume * 100), 600)
    assert scaled[0] == pytest.approx(100 * original[0]) and scaled[1] == 100 * original[1]
    assert above(9.15, *original) == above(9.15, *scaled)


@pytest.mark.parametrize(
    "failure",
    ["minute", "volume_zero", "volume_fraction", "high_nan", "high_below_close", "low_above_open"],
)
def test_both_variants_require_valid_observed_ohlcv(failure):
    view = session()
    bars = view.symbols["ABC"]
    if failure == "minute":
        keep = bars.minute != 590
        changes = {
            name: getattr(bars, name)[keep]
            for name in ("minute", "open", "high", "low", "close", "volume")
        }
    elif failure.startswith("volume"):
        volume = bars.volume.astype(float)
        volume[20] = 0 if failure == "volume_zero" else 0.5
        changes = {"volume": volume}
    elif failure == "low_above_open":
        low = bars.low.copy()
        low[20] = 11
        changes = {"low": low}
    else:
        high = bars.high.copy()
        high[20] = np.nan if failure == "high_nan" else 1
        changes = {"high": high}
    view = change(view, **changes)
    assert not day_signals(strategy(), view)
    assert not day_signals(strategy(False), view)


def test_primary_control_and_all_prefixes_without_transactions_or_quotes():
    view = session()
    for primary in (True, False):
        st = strategy(primary)
        assert day_signals(st, view) == EXPECTED
        check_no_lookahead(st, view, EXPECTED, list(range(570, 724)))
    assert all(b.transactions is None for b in view.symbols.values())


def test_first_rejection_cannot_be_rescued_by_later_reclaim():
    view = session(rejected=True, later=True)
    assert day_signals(strategy(False), view) == EXPECTED
    assert not day_signals(strategy(), view)
    close = view.symbols["ABC"].close.copy()
    close[30] = 9.05
    open_ = view.symbols["ABC"].open.copy()
    open_[30] = 9.05
    # Remove the first price event only; the later registered reference would pass.
    modified = change(view, close=close, open=open_)
    signals = day_signals(strategy(), modified)
    assert signals and signals[0].minute == 620


def test_first_missing_history_cannot_be_rescued_and_peers_stay_in_reference():
    view = session(later=True)
    bars = view.symbols["ABC"]
    volume = bars.volume.copy()
    volume[20] = 0
    assert not day_signals(strategy(False), change(view, volume=volume))
    peer = view.symbols["P0"]
    high = peer.high.copy()
    high[20] = np.nan
    view = replace(view, symbols={**view.symbols, "P0": replace(peer, high=high)})
    assert day_signals(strategy(), view) == EXPECTED
    close = peer.close.copy()
    close[15] = np.nan
    view = replace(view, symbols={**view.symbols, "P0": replace(peer, close=close)})
    assert not day_signals(strategy(False), view.upto(600))


def test_future_price_volume_and_high_perturbations_do_not_change_past():
    view = session()
    bars = view.symbols["ABC"]
    fields = {
        name: getattr(bars, name).copy() for name in ("open", "high", "low", "close", "volume")
    }
    for values in fields.values():
        values[bars.minute > 600] = 1000
    changed = change(view, **fields)
    assert [s for s in day_signals(strategy(), changed) if s.minute <= 600] == EXPECTED


def test_replay_detects_deliberate_future_reference_lookup():
    base = strategy()

    class Cheater(type(base)):
        def signals(self, view, features):
            found = super().signals(view, features)
            return found if len(view.symbols["ABC"].volume) > 50 else []

    st = Cheater(True)
    view = session()
    with pytest.raises(LookaheadError):
        check_no_lookahead(st, view, day_signals(st, view), [600])


@pytest.mark.parametrize(("late", "close_minute"), [(False, 960), (True, 960), (False, 700)])
def test_entry_expiry_and_two_hour_exit_with_auction_fallback(late, close_minute):
    from kinn.costs.model import load
    from kinn.engine.intraday.data import DayData
    from kinn.engine.intraday.simulator import FillConfig, simulate_day
    from kinn.risk.sizing import RiskConfig

    meta, config = runner.load_config(NAME, "development")
    view = replace(session(), close_minute=close_minute)
    if late:
        bars = view.symbols["ABC"]
        keep = bars.minute != 601
        view = change(
            view,
            **{
                name: getattr(bars, name)[keep]
                for name in ("minute", "open", "high", "low", "close", "volume")
            },
        )
    trades = simulate_day(
        DayData(view, {"ABC": 10.0}),
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


def test_only_registered_params_and_config_differences():
    _, dev = runner.load_config(NAME, "development")
    _, control = runner.load_config(NAME, "development_control")
    _, validation = runner.load_config(NAME, "validation")
    assert control == {**dev, "params": {"require_reference": False}}
    assert validation == {**dev, "period": {"start": "2017-01-03", "end": "2023-11-08"}}
    for params in ({"require_reference": 1}, {"margin": 0.005}):
        with pytest.raises(ValueError, match="frozen boolean"):
            runner.load_strategy(NAME, params)
