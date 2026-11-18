"""Synthetic proposed-input contract tests; no real loader or input build is exercised."""

from dataclasses import dataclass, replace
from datetime import UTC, date, datetime
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

import numpy as np
import pytest

from kinn import run as runner
from kinn.engine.intraday.data import DayData, DayView, make_symbol_day
from kinn.engine.intraday.simulator import FillConfig, simulate_day
from kinn.engine.intraday.strategy import check_no_lookahead, day_signals, input_sessions
from kinn.features.base import LookaheadError
from kinn.risk.sizing import RiskConfig
from kinn.validation.event_study import measure_extended
from tests.test_simulator import COSTS

SOURCE = Path(__file__).resolve().parents[1] / "strategies/timed_earnings_discovery/strategy.py"
SPEC = spec_from_file_location("timed_earnings_discovery", SOURCE)
MODULE = module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


@dataclass(frozen=True)
class FilingFixture:
    """Proposed TimedReport fields, deliberately confined to this synthetic test."""

    symbol: str = "ABC"
    permaticker: int = 1
    accession: str = "initial"
    form: str = "8-K"
    filed: date = date(2010, 1, 4)
    accepted: datetime = datetime(2010, 1, 4, 21, 0, 30, tzinfo=UTC)
    items: tuple = ("2.02", "9.01")
    earnings: bool = True
    usable_minute: int = 961


@dataclass(frozen=True)
class ViewFixture:
    """Synthetic prefix behavior only; never used as a research-data loader."""

    day: date
    open_minute: int
    close_minute: int
    symbols: dict
    timed_reports: dict

    def upto(self, cut):
        return replace(
            self,
            symbols={s: b.upto(cut) for s, b in self.symbols.items()},
            timed_reports={
                s: tuple(r for r in rows if r.usable_minute <= cut)
                for s, rows in self.timed_reports.items()
            },
        )


def stock():
    minute = np.array([959, 960, 961, 962, 963, 964, 993, 994, 1199])
    price = np.array([10, 1000, 10.2, 10.4, 10.6, 10.61, 11, 11, 99])
    return make_symbol_day(
        "ABC",
        1,
        minute,
        price,
        price + 0.001,
        price - 0.001,
        price,
        np.full(len(minute), 20000),
        {"adv20_prev": 2e6},
    )


def view(*, bars=None, filings=None):
    return ViewFixture(
        date(2010, 1, 4),
        570,
        960,
        {"ABC": stock() if bars is None else bars},
        {"ABC": (FilingFixture(),) if filings is None else filings},
    )


def test_frozen_timing_limit_and_full_prefix_replay():
    data, strategy = view(), MODULE.build({})
    signals = day_signals(strategy, data)
    assert len(signals) == 1
    assert signals[0].minute == 963 and signals[0].expire_minute == 964
    assert signals[0].limit_price == 10.70 and signals[0].max_hold_minutes == 30
    check_no_lookahead(strategy, data, signals, list(range(955, 999)))
    assert not data.upto(960).timed_reports["ABC"]
    assert data.upto(961).timed_reports["ABC"]
    assert not day_signals(strategy, replace(data, close_minute=780))


def test_summer_and_winter_utc_offsets_use_new_york_time():
    winter = FilingFixture()
    summer = replace(
        winter, filed=date(2010, 7, 1), accepted=datetime(2010, 7, 1, 20, 0, 30, tzinfo=UTC)
    )
    data = replace(view(filings=(summer,)), day=date(2010, 7, 1))
    assert day_signals(MODULE.build({}), data)[0].minute == 963
    with pytest.raises(ValueError, match="timezone-aware"):
        day_signals(
            MODULE.build({}), view(filings=(replace(winter, accepted=datetime(2010, 1, 4, 16)),))
        )
    with pytest.raises(ValueError, match="complete-minute delay"):
        day_signals(MODULE.build({}), view(filings=(replace(winter, usable_minute=960),)))


@pytest.mark.parametrize(
    "failure", ["form", "item", "flag", "symbol", "company", "accession", "time"]
)
def test_original_earnings_identity_and_hour_contract(failure):
    report = FilingFixture()
    changes = {
        "form": {"form": "8-K/A"},
        "item": {"items": ("9.01",)},
        "flag": {"earnings": False},
        "symbol": {"symbol": "OTHER"},
        "company": {"permaticker": 2},
        "accession": {"accession": ""},
        "time": {"accepted": datetime(2010, 1, 4, 22, tzinfo=UTC)},
    }
    assert not day_signals(MODULE.build({}), view(filings=(replace(report, **changes[failure]),)))


def test_missing_post_minute_and_insufficient_turnover_fail_without_imputation():
    bars = stock()
    keep = bars.minute != 962
    missing = replace(
        bars,
        **{k: getattr(bars, k)[keep] for k in ("minute", "open", "high", "low", "close", "volume")},
    )
    assert not day_signals(MODULE.build({}), view(bars=missing))
    volume = bars.volume.copy()
    volume[bars.minute == 962] = 1
    assert not day_signals(MODULE.build({}), view(bars=replace(bars, volume=volume)))


def test_first_filing_cannot_be_rescued_by_a_later_qualifying_filing():
    minutes = np.array([959, 961, 962, 963, 965, 966, 967])
    price = np.array([10, 10, 10, 10.01, 10.2, 10.4, 10.7])
    bars = make_symbol_day(
        "ABC",
        1,
        minutes,
        price,
        price,
        price,
        price,
        np.full(len(price), 20000),
        {"adv20_prev": 2e6},
    )
    later = replace(
        FilingFixture(),
        accession="later",
        accepted=datetime(2010, 1, 4, 21, 4, tzinfo=UTC),
        usable_minute=965,
    )
    data = view(bars=bars, filings=(later, FilingFixture()))
    assert not day_signals(MODULE.build({}), data)
    (signal,) = day_signals(MODULE.build({}), view(bars=bars, filings=(later,)))
    assert signal.minute == 967


def test_acceptance_bar_and_future_prices_do_not_change_the_event():
    data = view()
    original = day_signals(MODULE.build({}), data)
    bars = data.symbols["ABC"]
    close = bars.close.copy()
    close[bars.minute == 960] = 0.01
    close[-1] = 0.01
    assert (
        day_signals(MODULE.build({}), replace(data, symbols={"ABC": replace(bars, close=close)}))
        == original
    )


def test_checker_detects_a_deliberate_future_filing_dependency():
    class Cheater(MODULE.TimedEarningsDiscovery):
        def signals(self, data, features):
            found = super().signals(data, features)
            return found if len(data.timed_reports["ABC"]) > 1 else []

    future = replace(
        FilingFixture(),
        accession="future",
        accepted=datetime(2010, 1, 4, 21, 20, tzinfo=UTC),
        usable_minute=981,
    )
    data = view(filings=(FilingFixture(), future))
    strategy = Cheater()
    with pytest.raises(LookaheadError):
        check_no_lookahead(strategy, data, day_signals(strategy, data), [963])


def test_existing_extended_simulator_applies_next_minute_and_after_hours_exit():
    data = view()
    (signal,) = day_signals(MODULE.build({}), data)
    _, cfg = runner.load_config("timed_earnings_discovery", "development")
    risk, fills = RiskConfig(**cfg["risk"]), FillConfig(**cfg["fills"])
    result = simulate_day(DayData(data, {}), [signal], risk=risk, config=fills, costs=COSTS)
    (trade,) = result.trades
    assert not result.unresolved
    assert trade.entry_minute == 964 and trade.exit_minute == 994
    assert trade.entry_price == 10.61 and trade.exit_price == 11
    assert fills.extended_slippage_multiplier == 2
    assert fills.liquidation_limit_pct == 0.02


def test_unimplemented_input_is_not_bypassed_and_params_are_frozen():
    strategy = MODULE.build({})
    with pytest.raises(RuntimeError, match="authorization and adapter"):
        day_signals(strategy, DayView(date(2010, 1, 4), 570, 960, {"ABC": stock()}))
    with pytest.raises(ValueError, match="unknown inputs"):
        input_sessions(strategy, "form8k_timed")
    with pytest.raises(ValueError, match="no tunable parameters"):
        MODULE.build({"gain": 0.1})


@pytest.mark.parametrize("seconds", [0, 59])
def test_acceptance_seconds_and_last_permitted_entry_minute(seconds):
    bars = stock()
    minutes = bars.minute.copy()
    minutes[:-1] += 59
    late = replace(
        FilingFixture(),
        accepted=datetime(2010, 1, 4, 21, 59, seconds, tzinfo=UTC),
        usable_minute=1020,
    )
    data = view(bars=replace(bars, minute=minutes), filings=(late,))
    (signal,) = day_signals(MODULE.build({}), data)
    assert signal.minute == 1022 and signal.expire_minute == 1023
    _, cfg = runner.load_config("timed_earnings_discovery", "development")
    result = simulate_day(
        DayData(data, {}),
        [signal],
        risk=RiskConfig(**cfg["risk"]),
        config=FillConfig(**cfg["fills"]),
        costs=COSTS,
    )
    (trade,) = result.trades
    assert trade.entry_minute == 1023 and trade.exit_minute == 1053
    assert not result.unresolved


def test_entry_above_registered_cap_stays_unfilled_after_expiry():
    data = view()
    (signal,) = day_signals(MODULE.build({}), data)
    bars = data.symbols["ABC"]
    prices = bars.close.copy()
    prices[bars.minute == 964] = 10.9
    changed = replace(bars, open=prices, close=prices, high=prices + 0.001, low=prices - 0.001)
    _, cfg = runner.load_config("timed_earnings_discovery", "development")
    result = simulate_day(
        DayData(replace(data, symbols={"ABC": changed}), {}),
        [signal],
        risk=RiskConfig(**cfg["risk"]),
        config=FillConfig(**cfg["fills"]),
        costs=COSTS,
    )
    assert result.unfilled == 1 and not result.trades and not result.unresolved


def test_failed_liquidation_retains_exposure_and_has_no_completed_event_return():
    data = view()
    (signal,) = day_signals(MODULE.build({}), data)
    bars = data.symbols["ABC"]
    prices = bars.close.copy()
    prices[bars.minute == 994], prices[bars.minute == 1199] = 10.5, 10
    changed = replace(bars, open=prices, close=prices, high=prices + 0.001, low=prices - 0.001)
    _, cfg = runner.load_config("timed_earnings_discovery", "development")
    fills = FillConfig(**cfg["fills"])
    result = simulate_day(
        # An official regular close must not make the residual disappear.
        DayData(replace(data, symbols={"ABC": changed}), {"ABC": 1000}),
        [signal],
        risk=RiskConfig(**cfg["risk"]),
        config=fills,
        costs=COSTS,
    )
    assert not result.trades and len(result.unresolved) == 1
    assert result.unresolved[0].held > 0
    row = measure_extended(
        data.day, changed, signal, config=fills, costs=COSTS, position_dollars=2000
    )
    assert not row["completed"] and row["held"] > 0 and row["r_30"] is None
    assert row["marked_net"] is not None and row["marked_net_2x"] is not None
