"""Prepared synthetic contract only: native financial snapshot support is not implemented."""

from dataclasses import dataclass, replace
from datetime import date, timedelta

import pytest

from kinn import run as runner
from kinn.engine.intraday.strategy import check_no_lookahead, day_signals, input_sessions
from kinn.features.base import LookaheadError
from tests.test_filing_aware_dislocation import DAY, EXPECTED, TARGET
from tests.test_filing_aware_dislocation import session as price_session

NAME = "cash_profit_reversal"


@dataclass(frozen=True)
class SnapshotContract:
    """Proposed immutable value, not a native loader or core type."""

    symbol: str = "ABC"
    permaticker: int = 100
    dimension: str = "ART"
    filed: date | None = date(2016, 11, 15)
    reportperiod: date | None = date(2016, 9, 30)
    opinc: float | None = 1e6
    ncfo: float | None = 2e6
    status: str = "available"


@dataclass(frozen=True)
class FinancialViewContract:
    """Proposed pre-open prefix contract. It certifies no native data selection."""

    base: object
    fundamentals: dict

    def __getattr__(self, name):
        return getattr(self.base, name)

    def upto(self, cut):
        return FinancialViewContract(self.base.upto(cut), self.fundamentals)


def strategy(primary=True):
    return runner.load_strategy(NAME, {"require_positive": primary})


def session(snapshot=SnapshotContract(), **kwargs):
    return FinancialViewContract(price_session(**kwargs), {"ABC": snapshot})


def test_positive_pair_and_control_have_identical_signals_and_every_prefix():
    view = session()
    for primary in (True, False):
        st = strategy(primary)
        assert day_signals(st, view) == EXPECTED
        check_no_lookahead(st, view, EXPECTED, list(range(580, 724)))
    # Only one company has a financial entry, but all thirty peers still supply prices.
    assert len(view.fundamentals) == 1 and len(view.symbols) == 31


@pytest.mark.parametrize(
    "changes", [{"opinc": 0}, {"ncfo": 0}, {"opinc": -1}, {"ncfo": -1}, {"opinc": -1, "ncfo": -1}]
)
def test_control_requires_finite_pair_without_positive_signs(changes):
    view = session(replace(SnapshotContract(), **changes))
    assert not day_signals(strategy(), view)
    assert day_signals(strategy(False), view) == EXPECTED


@pytest.mark.parametrize(
    "changes",
    [
        {"status": "missing", "opinc": None, "ncfo": None, "filed": None, "reportperiod": None},
        {"status": "conflict"},
        {"status": "invalid"},
        {"opinc": None},
        {"ncfo": None},
        {"opinc": float("nan")},
        {"ncfo": float("inf")},
        {"opinc": True},
        {"filed": DAY},
        {"filed": DAY + timedelta(days=1)},
        {"filed": DAY - timedelta(days=2), "reportperiod": DAY - timedelta(days=1)},
        {"reportperiod": DAY - timedelta(days=181)},
        {"filed": None},
        {"reportperiod": None},
    ],
)
def test_unknown_stale_future_and_invalid_pairs_cannot_be_repaired(changes):
    view = session(replace(SnapshotContract(), **changes))
    for primary in (True, False):
        assert not day_signals(strategy(primary), view)


def test_exact_freshness_boundary_and_currency_unit_invariance():
    boundary = SnapshotContract(
        filed=DAY - timedelta(days=1), reportperiod=DAY - timedelta(days=180)
    )
    assert day_signals(strategy(), session(boundary)) == EXPECTED
    assert (
        day_signals(strategy(), session(replace(boundary, reportperiod=DAY - timedelta(days=181))))
        == []
    )
    assert day_signals(strategy(), session(replace(boundary, opinc=1e12, ncfo=0.001))) == EXPECTED


@pytest.mark.parametrize(
    "changes",
    [{"symbol": "OTHER"}, {"permaticker": 999}, {"dimension": "MRT"}, {"status": "unsupported"}],
)
def test_wrong_identity_restatement_dimension_or_unknown_status_is_an_error(changes):
    with pytest.raises(ValueError, match="mismatch|unknown"):
        day_signals(strategy(), session(replace(SnapshotContract(), **changes)))


def test_missing_native_adapter_or_parent_entry_cannot_silently_become_zero_events():
    with pytest.raises(RuntimeError, match="native coherent"):
        day_signals(strategy(), price_session())
    with pytest.raises(ValueError, match="exact company"):
        day_signals(strategy(), FinancialViewContract(price_session(), {}))
    with pytest.raises(ValueError, match="unknown inputs"):
        input_sessions(strategy(), "fundamentals_art")


def test_first_price_event_is_fixed_and_future_field_dates_remain_unavailable():
    view = session(target=[*TARGET, (730, 10), (744, 8.5), (745, 8.6), (746, 8.7)])
    assert day_signals(strategy(), view) == EXPECTED
    assert not day_signals(
        strategy(), replace(view, fundamentals={"ABC": replace(SnapshotContract(), opinc=-1)})
    )
    future = session(replace(SnapshotContract(), filed=DAY))
    for cut in (599, 600, 721):
        assert not day_signals(strategy(), future.upto(cut))


def test_deliberate_future_price_lookup_is_caught():
    base = strategy()

    class Cheater(type(base)):
        def signals(self, view, features):
            found = super().signals(view, features)
            return found if len(view.symbols["ABC"].minute) > 4 else []

    st = Cheater(True)
    view = session()
    with pytest.raises(LookaheadError):
        check_no_lookahead(st, view, day_signals(st, view), [600])


@pytest.mark.parametrize(("entry", "close_minute"), [(601, 960), (602, 960), (601, 700)])
def test_next_minute_expiry_and_two_hour_exit_with_auction_fallback(entry, close_minute):
    from kinn.costs.model import load
    from kinn.engine.intraday.data import DayData
    from kinn.engine.intraday.simulator import FillConfig, simulate_day
    from kinn.risk.sizing import RiskConfig

    meta, config = runner.load_config(NAME, "development")
    view = session(target=[*TARGET[:3], (entry, 8.7), TARGET[-1]], close_minute=close_minute)
    trades = simulate_day(
        DayData(view, {"ABC": 9.2}),
        day_signals(strategy(), view),
        risk=RiskConfig(**config["risk"]),
        config=FillConfig(**config["fills"]),
        costs=load(meta["cost_calibration"]),
    ).trades
    if entry == 602:
        assert not trades
    else:
        (trade,) = trades
        assert trade.entry_minute == 601
        assert (trade.exit_minute, trade.exit_reason) == (
            (721, "time") if close_minute == 960 else (700, "auction")
        )


def test_configs_and_only_declared_boolean_contract():
    _, dev = runner.load_config(NAME, "development")
    _, control = runner.load_config(NAME, "development_control")
    _, validation = runner.load_config(NAME, "validation")
    assert control == {**dev, "params": {"require_positive": False}}
    assert validation == {**dev, "period": {"start": "2017-01-03", "end": "2023-11-08"}}
    assert strategy().inputs == strategy(False).inputs == {"fundamentals_art": {"sessions": 1}}
    for params in ({"require_positive": 1}, {"freshness": 365}):
        with pytest.raises(ValueError, match="frozen boolean"):
            runner.load_strategy(NAME, params)
