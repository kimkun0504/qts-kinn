"""Check filing selection, unchanged peer returns and next-minute timing."""

from dataclasses import replace
from datetime import date

import pytest

from kinn import run as runner
from kinn.core.types import CurrentReport, Signal
from kinn.costs.model import load
from kinn.engine.intraday.data import DayData, DayView, make_symbol_day
from kinn.engine.intraday.simulator import FillConfig, simulate_day
from kinn.engine.intraday.strategy import check_no_lookahead, day_signals
from kinn.risk.sizing import RiskConfig

NAME = "filing_aware_dislocation"
DAY = date(2016, 12, 2)
REPORT = CurrentReport("ABC", 100, date(2016, 12, 1), (22, 91), ("2.02", "9.01"), True)
TARGET = [(585, 10), (599, 8.5), (600, 8.6), (601, 8.7), (721, 9.1)]
EXPECTED = [Signal("ABC", 600, expire_minute=601, max_hold_minutes=120)]


def stock(symbol, perma, rows, *, cap=500e6, adv=10e6, volume=5_000):
    minute, price = zip(*rows, strict=True)
    return make_symbol_day(
        symbol,
        perma,
        minute,
        price,
        price,
        price,
        price,
        [volume] * len(minute),
        {"marketcap_prev": cap, "adv20_prev": adv},
    )


def session(
    target=TARGET,
    *,
    reports=None,
    peers=30,
    target_cap=500e6,
    peer_cap=500e6,
    peer_before=100,
    peer_after=100,
    close_minute=960,
):
    rows = [(585, 100), (599, peer_before), (600, peer_after), (601, 101), (721, 99)]
    members = {f"P{i:02d}": stock(f"P{i:02d}", i + 1, rows, cap=peer_cap) for i in range(peers)}
    members["ABC"] = stock("ABC", 100, target, cap=target_cap)
    return DayView(DAY, 570, close_minute, members, reports=reports or {})


def test_unfiled_candidate_keeps_original_entry_and_passes_replay():
    strategy = runner.load_strategy(NAME, {})
    assert strategy.inputs == {"form8k": {"sessions": 1}}
    view = session()
    found = day_signals(strategy, view)
    assert found == EXPECTED
    assert day_signals(strategy, view.upto(599)) == []
    check_no_lookahead(strategy, view, found, [585, 599, 600, 601, 721])


@pytest.mark.parametrize("report", [REPORT, replace(REPORT, items=("9.01",), earnings=False)])
def test_available_typed_filing_excludes_the_candidate(report):
    assert day_signals(runner.load_strategy(NAME, {}), session(reports={"ABC": (report,)})) == []


@pytest.mark.parametrize(
    "report",
    [
        replace(REPORT, filed=DAY),
        replace(REPORT, filed=date(2016, 12, 5)),
        replace(REPORT, permaticker=200),
        replace(REPORT, symbol="XYZ"),
        replace(REPORT, codes=(34,), items=(), earnings=False),
    ],
)
def test_unavailable_or_unmatched_report_cannot_suppress_a_past_signal(report):
    view = session(reports={"ABC": (report,)})
    assert day_signals(runner.load_strategy(NAME, {}), view) == EXPECTED


def test_excluded_peer_stays_in_reference_basket():
    filings = {
        f"P{i:02d}": (replace(REPORT, symbol=f"P{i:02d}", permaticker=i + 1),) for i in range(30)
    }
    assert day_signals(runner.load_strategy(NAME, {}), session(reports=filings)) == EXPECTED


@pytest.mark.parametrize(
    "kwargs",
    [
        {"peers": 29},
        {"peer_cap": 3e9},
        {"peer_after": 97},
        {"peer_before": 99},
        {"target": [(584, 10), *TARGET[1:]]},
        {"target": [TARGET[0], (598, 8.5), *TARGET[2:]]},
        {"target": [TARGET[0], (599, 8.55), *TARGET[2:]]},
        {"target_cap": 10e9},
    ],
)
def test_still_requires_a_same_size_synchronous_reference_and_recovery(kwargs):
    assert day_signals(runner.load_strategy(NAME, {}), session(**kwargs)) == []


@pytest.mark.parametrize(("entry", "close_minute"), [(601, 960), (602, 960), (601, 700)])
def test_expiry_and_two_hour_exit_with_early_close_fallback(entry, close_minute):
    meta, config = runner.load_config(NAME, "development")
    strategy = runner.load_strategy(NAME, config["params"])
    view = session(target=[*TARGET[:3], (entry, 8.7), TARGET[-1]], close_minute=close_minute)
    trades = simulate_day(
        DayData(view, {"ABC": 9.2}),
        day_signals(strategy, view),
        risk=RiskConfig(**config["risk"]),
        config=FillConfig(**config["fills"]),
        costs=load(meta["cost_calibration"]),
    ).trades
    if entry == 602:
        assert trades == []
    else:
        (trade,) = trades
        assert trade.entry_minute == 601
        assert (trade.exit_minute, trade.exit_reason) == (
            (721, "time") if close_minute == 960 else (700, "auction")
        )


def test_configs_only_change_dates():
    _, dev = runner.load_config(NAME, "development")
    _, val = runner.load_config(NAME, "validation")
    assert dev["period"] == {"start": date(2003, 9, 10), "end": date(2016, 12, 30)}
    assert val["period"] == {"start": date(2017, 1, 3), "end": date(2023, 11, 8)}
    assert val == {**dev, "period": val["period"]}
