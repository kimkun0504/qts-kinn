"""The sole new filter uses only filings already usable at the baseline event."""

from dataclasses import replace
from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

import pytest

from kinn import run as runner
from kinn.core.types import TimedReport
from kinn.costs.model import load
from kinn.engine.intraday.data import DayData
from kinn.engine.intraday.simulator import FillConfig, simulate_day
from kinn.engine.intraday.strategy import check_no_lookahead, day_signals
from kinn.features.base import LookaheadError
from kinn.risk.sizing import RiskConfig
from tests.test_filing_aware_dislocation import DAY, EXPECTED, REPORT, TARGET, session

NAME = "timed_filing_dislocation"


def filing(usable=600, **changes):
    accepted = (
        datetime(DAY.year, DAY.month, DAY.day, tzinfo=ZoneInfo("America/New_York"))
        + timedelta(minutes=usable - 1, seconds=30)
    ).astimezone(UTC)
    report = TimedReport(
        "ABC", 100, "original", "8-K", DAY, accepted, ("3.02", "9.01"), False, usable
    )
    return replace(report, **changes)


def test_no_current_filing_keeps_exact_baseline_and_native_prefix_replay():
    strategy = runner.load_strategy(NAME, {})
    baseline = runner.load_strategy("filing_aware_dislocation", {})
    view = session()
    assert strategy.universe.where() == baseline.universe.where()
    assert strategy.inputs == {"form8k": {"sessions": 1}, "form8k_timed": {"sessions": 1}}
    found = day_signals(strategy, view)
    assert found == day_signals(baseline, view) == EXPECTED
    check_no_lookahead(strategy, view, found, list(range(580, 724)))


@pytest.mark.parametrize("usable", [599, 600])
def test_current_typed_filing_usable_at_or_before_decision_excludes(usable):
    view = replace(session(), timed_reports={"ABC": (filing(usable),)})
    assert not day_signals(runner.load_strategy(NAME, {}), view)
    check_no_lookahead(runner.load_strategy(NAME, {}), view, [], list(range(580, 724)))


@pytest.mark.parametrize("usable", [601, 900])
def test_later_filing_never_retroactively_cancels_a_signal(usable):
    view = replace(session(), timed_reports={"ABC": (filing(usable),)})
    strategy = runner.load_strategy(NAME, {})
    assert day_signals(strategy, view) == EXPECTED
    check_no_lookahead(strategy, view, EXPECTED, list(range(580, 905)))


@pytest.mark.parametrize(
    "changes",
    [
        {"symbol": "WRONG"},
        {"permaticker": 999},
        {"form": "8-K/A"},
        {"accession": ""},
        {"items": ()},
        {"accepted": datetime(2016, 12, 5, 14, 59, tzinfo=UTC)},
    ],
)
def test_unmatched_untyped_or_other_session_record_cannot_suppress_event(changes):
    view = replace(session(), timed_reports={"ABC": (filing(**changes),)})
    assert day_signals(runner.load_strategy(NAME, {}), view) == EXPECTED


def test_prior_date_exclusion_remains_and_excluded_peers_stay_in_benchmark():
    strategy = runner.load_strategy(NAME, {})
    assert not day_signals(strategy, session(reports={"ABC": (REPORT,)}))
    peers = {f"P{i:02d}": (filing(symbol=f"P{i:02d}", permaticker=i + 1),) for i in range(30)}
    view = replace(session(), timed_reports=peers)
    assert day_signals(strategy, view) == EXPECTED
    check_no_lookahead(strategy, view, EXPECTED, [599, 600, 601])


def test_future_filing_lookup_canary_detects_an_end_of_day_exclusion():
    base = runner.load_strategy(NAME, {})

    class Cheater(type(base)):
        def signals(self, view, features):
            found = super().signals(view, features)
            return [] if view.timed_reports.get("ABC") else found

    view = replace(session(), timed_reports={"ABC": (filing(900),)})
    strategy = Cheater()
    with pytest.raises(LookaheadError):
        check_no_lookahead(strategy, view, day_signals(strategy, view), [600])


@pytest.mark.parametrize(("entry", "close_minute"), [(601, 960), (602, 960), (601, 700)])
def test_original_entry_expiry_and_two_hour_exit_are_preserved(entry, close_minute):
    meta, config = runner.load_config(NAME, "development")
    view = session(target=[*TARGET[:3], (entry, 8.7), TARGET[-1]], close_minute=close_minute)
    result = simulate_day(
        DayData(view, {"ABC": 9.2}),
        day_signals(runner.load_strategy(NAME, {}), view),
        risk=RiskConfig(**config["risk"]),
        config=FillConfig(**config["fills"]),
        costs=load(meta["cost_calibration"]),
    )
    if entry == 602:
        assert not result.trades and result.unfilled == 1
    else:
        (trade,) = result.trades
        assert trade.entry_minute == 601
        assert trade.exit_minute == (721 if close_minute == 960 else 700)


def test_development_matches_saved_baseline_config_and_validation_changes_only_period():
    _, config = runner.load_config(NAME, "development")
    _, baseline = runner.load_config("filing_aware_dislocation", "development")
    _, validation = runner.load_config(NAME, "validation")
    assert config == baseline
    assert validation == {
        **config,
        "period": {
            "start": DAY.replace(year=2017, month=1, day=3),
            "end": DAY.replace(year=2023, month=11, day=8),
        },
    }
    with pytest.raises(ValueError, match="no tunable parameters"):
        runner.load_strategy(NAME, {"delay": 0})
