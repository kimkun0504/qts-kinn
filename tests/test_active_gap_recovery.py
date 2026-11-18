"""Synthetic trading-gap eligibility, distinct-company coverage and execution replay."""

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

SOURCE = Path(__file__).resolve().parents[1] / "strategies/active_gap_recovery/strategy.py"
SPEC = spec_from_file_location("active_gap_recovery", SOURCE)
MODULE = module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
FIELDS = ("minute", "open", "high", "low", "close", "volume", "transactions")


def stock():
    minutes = np.r_[570, np.arange(590, 600), 605, 606, 635, 636, 959]
    closes = np.r_[10, np.full(10, 11.2), 10.6, 10.61, 10.99, 11, 99]
    opens = closes.copy()
    opens[11] = 10.4
    return make_symbol_day(
        "ABC",
        1,
        minutes,
        opens,
        np.maximum(opens, closes),
        np.minimum(opens, closes),
        closes,
        np.full(len(minutes), 5000),
        {"prev_close": 10, "adv20_prev": 2e6},
        transactions=np.full(len(minutes), 150),
    )


def peer(symbol, company, minutes=None):
    if minutes is None:
        minutes = np.arange(600, 605)
    return make_symbol_day(
        symbol,
        company,
        minutes,
        np.full(len(minutes), 10),
        np.full(len(minutes), 10),
        np.full(len(minutes), 10),
        np.full(len(minutes), 10),
        np.full(len(minutes), 5000),
        {"adv20_prev": 2e6},
        transactions=np.full(len(minutes), 100),
    )


def view(target=None, *, others=10):
    members = {"ABC": stock() if target is None else target}
    members.update({f"P{i}": peer(f"P{i}", i + 2) for i in range(others)})
    return DayView(date(2010, 1, 4), 570, 960, members)


def remove_rows(bars, keep):
    return replace(bars, **{name: getattr(bars, name)[keep] for name in FIELDS})


def test_signal_definition_and_all_clock_prefixes():
    data, strategy = view(), MODULE.build({})
    signals = day_signals(strategy, data)
    assert len(signals) == 1
    assert signals[0].minute == 605
    assert signals[0].expire_minute == 606 and signals[0].max_hold_minutes == 30
    check_no_lookahead(strategy, data, signals, list(range(565, 668)))
    assert not day_signals(strategy, replace(data, close_minute=780))


def test_future_prices_counts_and_future_peer_coverage_cannot_change_event():
    data = view()
    signals = day_signals(MODULE.build({}), data)
    bars = data.symbols["ABC"]
    p, n = bars.close.copy(), bars.transactions.copy()
    p[-1], n[-1] = 0.01, 10_000_000
    changed = replace(bars, close=p, transactions=n)
    modified = replace(
        data, symbols={**data.symbols, "ABC": changed, "FUT": peer("FUT", 80, np.array([900]))}
    )
    assert day_signals(MODULE.build({}), modified) == signals


def test_gap_bounds_and_dense_prior_sequence():
    bars = stock()
    assert MODULE.candidate_gaps(bars, 2e6) == [(599, 605)]
    # Four wholly absent minutes do not qualify; a 31-minute gap does not qualify.
    for returning in (604, 631):
        minutes = bars.minute.copy()
        minutes[11:] += returning - 605
        assert not MODULE.candidate_gaps(replace(bars, minute=minutes), 2e6)
    missing = remove_rows(bars, bars.minute != 595)
    assert not MODULE.candidate_gaps(missing, 2e6)


@pytest.mark.parametrize(
    "failure", ["rally", "discount", "recovery", "counts", "activity", "ohlc", "missing"]
)
def test_price_and_observed_activity_gates(failure):
    bars = stock()
    o, h, low, c, v, n = (getattr(bars, f).astype(float).copy() for f in FIELDS[1:])
    if failure == "rally":
        o[0] = 11
        h[0] = 11
    elif failure == "discount":
        c[11] = h[11] = 11
    elif failure == "recovery":
        o[11] = c[11]
    elif failure == "counts":
        n[11] = 99
    elif failure == "activity":
        v[1:11] = 1
    elif failure == "ohlc":
        low[11] = c[11] + 1
    else:
        n[4] = np.nan
    changed = replace(bars, open=o, high=h, low=low, close=c, volume=v, transactions=n)
    assert not MODULE.candidate_gaps(changed, 2e6)
    with pytest.raises(ValueError, match="observed transaction counts"):
        MODULE.candidate_gaps(replace(bars, transactions=None), 2e6)


def test_other_company_coverage_requires_every_missing_minute_and_unique_identity():
    strategy = MODULE.build({})
    assert not day_signals(strategy, view(others=9))
    data = view()
    missing_peer = remove_rows(data.symbols["P0"], data.symbols["P0"].minute != 602)
    assert not day_signals(strategy, replace(data, symbols={**data.symbols, "P0": missing_peer}))
    nine = view(others=9)
    duplicate = peer("DUP", nine.symbols["P0"].permaticker)
    assert not day_signals(strategy, replace(nine, symbols={**nine.symbols, "DUP": duplicate}))
    invalid = replace(data.symbols["P0"], close=np.zeros(5))
    assert not day_signals(strategy, replace(data, symbols={**data.symbols, "P0": invalid}))


def test_first_qualifying_gap_wins_and_rejected_gap_does_not_block_a_later_one():
    bars = stock()
    keep = bars.minute < 650
    first = {name: getattr(bars, name)[keep] for name in FIELDS}
    minutes = np.r_[np.arange(650, 660), 665, 666, 695, 696]
    p = np.r_[np.full(10, 12), 11.2, 11.21, 11.8, 11.81]
    o = p.copy()
    o[10] = 11
    second = dict(
        minute=minutes,
        open=o,
        high=np.maximum(o, p),
        low=np.minimum(o, p),
        close=p,
        volume=np.full(len(p), 5000),
        transactions=np.full(len(p), 150),
    )
    target = replace(bars, **{name: np.r_[first[name], second[name]] for name in FIELDS})
    data = view(target)
    members = {
        **data.symbols,
        **{f"P{i}": peer(f"P{i}", i + 2, np.r_[600:605, 660:665]) for i in range(10)},
    }
    both = replace(data, symbols=members)
    assert [s.minute for s in day_signals(MODULE.build({}), both)] == [605]
    only_later = replace(both, symbols={**members, "P0": peer("P0", 2, np.arange(660, 665))})
    signals = day_signals(MODULE.build({}), only_later)
    assert [s.minute for s in signals] == [665]
    check_no_lookahead(MODULE.build({}), only_later, signals, list(range(598, 668)))


def test_replay_catches_a_deliberate_future_price_filter():
    class Cheater(MODULE.ActiveGapRecovery):
        def signals(self, data, features):
            signals = super().signals(data, features)
            return signals if data.symbols["ABC"].close[-1] > 50 else []

    strategy, data = Cheater(), view()
    with pytest.raises(LookaheadError):
        check_no_lookahead(strategy, data, day_signals(strategy, data), [605])


def test_next_minute_expiry_and_portfolio_timed_exit():
    data = view()
    (signal,) = day_signals(MODULE.build({}), data)
    _, cfg = runner.load_config("active_gap_recovery", "development")
    risk, fills = RiskConfig(**cfg["risk"]), FillConfig(**cfg["fills"])
    (trade,) = simulate_day(
        DayData(data, {"ABC": 99}), [signal], risk=risk, config=fills, costs=COSTS
    ).trades
    assert trade.entry_minute == 606 and trade.entry_price == pytest.approx(10.61)
    assert trade.exit_minute == 636 and trade.exit_price == pytest.approx(11)
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
    assert row["r_30"] == pytest.approx(10.99 / 10.61 - 1)
    target = data.symbols["ABC"]
    missing = remove_rows(target, target.minute != 606)
    result = simulate_day(
        DayData(replace(data, symbols={**data.symbols, "ABC": missing}), {}),
        [signal],
        risk=risk,
        config=fills,
        costs=COSTS,
    )
    assert not result.trades and result.unfilled == 1
    with pytest.raises(ValueError, match="no tunable parameters"):
        MODULE.build({"hold": 15})
