"""Execution and run-store contracts on synthetic bars only; no market-data query."""

import dataclasses
import json
import subprocess
import sys
from datetime import date, datetime
from zoneinfo import ZoneInfo

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from kinn import run as runner
from kinn.core.settings import Settings
from kinn.core.types import Signal
from kinn.engine.intraday.data import DayData, DayView, make_symbol_day
from kinn.engine.intraday.simulator import FillConfig, simulate_day, simulate_signal
from kinn.engine.intraday.strategy import check_no_lookahead, day_signals
from kinn.risk.sizing import RiskConfig
from kinn.validation import event_study
from tests.test_simulator import COSTS, flat, session

EXT = FillConfig(session="extended_v1", participation=0.05)
RISK = RiskConfig(position_dollars=1000, buying_power=1000, max_positions=1)


def order(minute=967, **changes):
    return dataclasses.replace(
        Signal("AAA", minute, limit_price=10.05, expire_minute=minute + 1, max_hold_minutes=15),
        **changes,
    )


def run(data, signals=None, *, config=EXT, risk=RISK):
    return simulate_day(data, signals or [order()], risk=risk, config=config, costs=COSTS)


def walk(data, signal=None, *, config=EXT):
    return simulate_signal(
        data.view.symbols["AAA"],
        signal or order(),
        100,
        config=config,
        costs=COSTS,
        open_minute=570,
        close_minute=960,
        official_close=999.0,
    )


def test_next_clock_entry_and_scheduled_exit_ignore_regular_auction():
    data = session(
        [
            flat(959, 999),
            flat(967, 10),
            flat(968, 10),
            flat(982, 10.5),
            flat(983, 10.5),
            flat(1200, 1000),
        ],
        official_close=999.0,
    )
    entry, exits, reason, release = walk(data)
    assert [f.minute for f in entry] == [968]
    assert [f.minute for f in exits] == [983]
    assert reason == "time" and release == 984
    assert all(f.kind == "marketable_limit" and f.slippage > 0 for f in entry + exits)
    (trade,) = run(data).trades
    assert trade.exit_price == 10.5 and trade.exit_minute == 983
    assert trade.net_2x == pytest.approx(trade.net - trade.slippage)
    assert trade.commission > 0 and trade.fees > 0


@pytest.mark.parametrize("minute", [239, 569, 959, 1198])
def test_explicit_extended_boundary_bars(minute):
    data = session([flat(minute, 10), flat(minute + 1, 10)], official_close=999)
    entry, _, _, _ = walk(data, order(minute))
    assert [f.minute for f in entry] == [minute + 1]


@pytest.mark.parametrize("minute", [238, 1199, 1200])
def test_cannot_fill_before_four_or_at_or_after_twenty(minute):
    assert not walk(session([flat(minute, 10), flat(minute + 1, 10)]), order(minute))[0]


def test_low_touch_cannot_create_opening_fill_and_missing_next_minute_expires():
    crossing = session([flat(967, 10), (968, 11, 11, 9, 9.5, 10000), flat(969, 10)])
    assert not walk(crossing)[0]
    missing = session([flat(967, 10), flat(969, 10)])
    assert not walk(missing)[0]
    config = dataclasses.replace(EXT, entry_start_minute=970, entry_end_minute=1000)
    assert not walk(session([flat(968, 10), flat(970, 10)]), config=config)[0]


def test_both_baseline_and_stress_execution_must_respect_price_cap():
    data = session([flat(967, 10), flat(968, 10), flat(983, 10)])
    # At $10 the half-tick floor gives 0.01/share baseline and 0.02 stress.
    assert not walk(data, order(limit_price=10.015))[0]
    entry = walk(data, order(limit_price=10.03))[0]
    assert entry and entry[0].price + 2 * entry[0].slippage / 100 <= 10.03


def test_partial_entry_expires_partial_exit_retries_and_each_order_pays_minimum():
    data = session(
        [
            flat(967, 10),
            flat(968, 10, 1000),
            flat(969, 9.9, 10000),
            flat(982, 10),
            flat(983, 10, 400),
            flat(984, 10, 600),
        ]
    )
    entry, exits, _, _ = walk(data)
    assert [f.quantity for f in entry] == [50]
    assert [(f.minute, f.quantity) for f in exits] == [(983, 20), (984, 30)]
    (trade,) = run(data).trades
    assert trade.quantity == 50
    assert trade.commission == pytest.approx(3 * COSTS.commission_min)


def test_exit_cap_uses_previous_completed_close_then_reprices_on_retry():
    data = session(
        [
            flat(967, 10),
            flat(968, 10),
            flat(982, 10),
            (983, 9.5, 20, 9.4, 9.5, 10000),
            flat(984, 9.5),
        ]
    )
    _, exits, _, _ = walk(data)
    assert [f.minute for f in exits] == [984]  # first attempt gaps below 9.80
    # Missing minutes do not fill, and the known stale close remains the limit reference.
    sparse = session([flat(967, 10), flat(968, 10), flat(985, 9.5)])
    assert not walk(sparse)[1]


def test_no_later_liquidity_preserves_unresolved_shares_and_never_creates_auction():
    data = session(
        [flat(967, 10), flat(968, 10), flat(983, 10, 400), flat(1199, 9.5, 0), flat(1200, 500)],
        official_close=999,
    )
    result = run(data)
    assert not result.trades and not result.unfilled
    (position,) = result.unresolved
    assert position.bought == 99 and position.sold == 20 and position.held == 79
    assert position.mark_minute == 983 and position.mark_price == 10
    assert position.marked_net < 0
    assert position.marked_net_2x == pytest.approx(position.marked_net - position.slippage)
    entry, exits, reason, release = walk(data)
    assert reason == "unresolved" and release == 1200
    assert all(f.kind != "auction" for f in entry + exits)


def test_unresolved_position_keeps_capital_and_daily_loss_limit_active():
    bars_a = [flat(967, 10), flat(968, 10), flat(990, 8)]
    bars_b = [flat(990, 10), flat(991, 10), flat(1006, 10)]
    a, b = session(bars_a).view.symbols["AAA"], session(bars_b, symbol="BBB").view.symbols["BBB"]
    data = DayData(DayView(date(2010, 1, 4), 570, 960, {"AAA": a, "BBB": b}), {})
    signals = [order(), dataclasses.replace(order(990), symbol="BBB")]
    result = run(data, signals)
    assert len(result.unresolved) == 1 and result.rejected_capital == 1
    result = run(
        data,
        signals,
        risk=RiskConfig(position_dollars=1000, buying_power=2000, daily_loss_limit=50),
    )
    assert len(result.unresolved) == 1 and result.rejected_risk == 1


@pytest.mark.parametrize(
    "bad",
    [Signal("AAA", 967), order(stop_pct=0.1), order(target_pct=0.1), order(max_hold_minutes=0)],
)
def test_extended_profile_refuses_unsupported_order_types(bad):
    with pytest.raises(ValueError, match="extended_v1"):
        walk(session([flat(968, 10)]), bad)


@pytest.mark.parametrize(
    "changes",
    [
        {"session": "unknown"},
        {"participation": 0},
        {"entry_start_minute": 200},
        {"entry_end_minute": 1200},
        {"extended_slippage_multiplier": float("nan")},
        {"liquidation_limit_pct": 1},
    ],
)
def test_execution_profile_rejects_invalid_configuration(changes):
    with pytest.raises(ValueError):
        dataclasses.replace(EXT, **changes)


def test_regular_defaults_still_ignore_after_hours_and_honor_early_closes():
    data = session(
        [flat(600, 10), flat(601, 10), flat(775, 10.5), flat(968, 999)],
        close_minute=780,
        official_close=10.5,
    )
    result = run(data, [Signal("AAA", 600)], config=FillConfig())
    assert result.trades[0].exit_minute == 775
    assert not run(data, [order()], config=FillConfig()).trades


def test_extended_study_and_portfolio_use_identical_fills_fees_and_expiry():
    data = session([flat(967, 10), flat(968, 10, 1000), flat(982, 10.5), flat(983, 10.5)])
    row = event_study.measure_extended(
        data.view.day,
        data.view.symbols["AAA"],
        order(),
        config=EXT,
        costs=COSTS,
        position_dollars=1000,
    )
    (trade,) = run(data).trades
    assert row["completed"] and row["shares"] == trade.quantity == 50
    assert row["r_15"] - row["fees"] - row["slippage"] == pytest.approx(trade.net / trade.notional)
    assert row["r_15"] - row["fees"] - 2 * row["slippage"] == pytest.approx(
        trade.net_2x / trade.notional
    )
    assert row["exit_minute"] == trade.exit_minute and row["r_close"] is None
    row2 = event_study.measure_extended(
        data.view.day,
        data.view.symbols["AAA"],
        order(expire_minute=967),
        config=EXT,
        costs=COSTS,
        position_dollars=1000,
    )
    assert row2 is None


def test_unresolved_events_stay_visible_and_invalidate_the_study():
    data = session([flat(967, 10), flat(968, 10)])
    row = event_study.measure_extended(
        data.view.day,
        data.view.symbols["AAA"],
        order(),
        config=EXT,
        costs=COSTS,
        position_dollars=1000,
    )
    assert row["held"] == 99 and row["r_15"] is None and row["marked_net"] < 0
    summary = event_study.summarize(pa.Table.from_pylist([row], schema=event_study.EXTENDED_SCHEMA))
    assert summary["events"] == 1 and summary["unresolved_positions"] == 1
    assert not summary["eligible_for_portfolio"] and summary["curve"] == {}


def candidate_day(day, *, unresolved=False):
    prices = [9.8, 9.6, 9.4, 9, 8.98, 8.95, 8.97]
    rows = [flat(570, 9.4), flat(900, 10.3), flat(959, 10)]
    rows.extend(flat(961 + i, price) for i, price in enumerate(prices))
    rows.append(flat(968, 8.98))
    if not unresolved:
        rows.extend([flat(982, 9.1), flat(983, 9.15)])
    cols = list(zip(*rows, strict=True))
    sd = make_symbol_day("AAA", 1, *cols, {"prev_close": 8.5, "adv20_prev": 5e7})
    return DayData(DayView(day, 570, 960, {"AAA": sd}), {"AAA": 999})


def test_strategy_prefix_replay_and_early_close_exclusion():
    strategy = runner.load_strategy("close_unwind_impact_decay", {})
    data = candidate_day(date(2010, 1, 4))
    signals = day_signals(strategy, data.view)
    assert len(signals) == 1 and signals[0].minute == 967
    assert signals[0].limit_price == pytest.approx(8.97 * 1.005)
    check_no_lookahead(strategy, data.view, signals, list(range(570, 984)))
    assert not day_signals(strategy, dataclasses.replace(data.view, close_minute=780))


def test_strategy_loads_outside_the_pytest_pythonpath(tmp_path):
    result = subprocess.run(
        [
            sys.executable,
            "-I",
            "-c",
            "from kinn.run import load_strategy; "
            "strategy = load_strategy('close_unwind_impact_decay', {}); "
            "assert strategy.name == 'close_unwind_impact_decay'",
        ],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize(
    ("utc", "day"),
    [
        ("2010-03-12T21:08:00+00:00", date(2010, 3, 12)),
        ("2010-03-15T20:08:00+00:00", date(2010, 3, 15)),
    ],
)
def test_local_bar_boundaries_do_not_shift_at_daylight_saving(utc, day):
    local = datetime.fromisoformat(utc).astimezone(ZoneInfo("America/New_York"))
    assert local.date() == day and local.hour * 60 + local.minute == 968
    data = candidate_day(day)
    signal = day_signals(runner.load_strategy("close_unwind_impact_decay", {}), data.view)[0]
    assert run(data, [signal]).trades[0].entry_minute == 968


@pytest.mark.parametrize("study", [False, True])
@pytest.mark.parametrize("unresolved", [False, True])
def test_registered_runner_persists_execution_contract_and_unresolved_exposure(
    tmp_path, monkeypatch, study, unresolved
):
    day = date(2010, 1, 4)

    class Store:
        build_id, info = "synthetic", {"bars_id": "synthetic"}

        def __init__(self, *args, **kwargs):
            pass

        def sessions(self, start, end):
            assert start < date(2023, 11, 9) and end < date(2023, 11, 9)
            return [day]

    settings = Settings(tmp_path / "raw", tmp_path / "processed", tmp_path / "runs")
    monkeypatch.setattr(runner, "DataStore", Store)
    monkeypatch.setattr(
        runner, "load_day", lambda *a, **kw: candidate_day(day, unresolved=unresolved)
    )
    monkeypatch.setattr(
        runner.registry,
        "git_state",
        lambda repo: {
            "commit": "synthetic",
            "branch": "agent/gpt/test",
            "dirty": False,
        },
    )
    folder = runner.start_run(
        "close_unwind_impact_decay",
        "development",
        settings=settings,
        agent="test",
        kind="event_study" if study else "backtest",
    )
    assert runner.continue_run(folder, settings=settings)
    manifest = json.loads((folder / "manifest.json").read_text())
    assert manifest["execution"]["session"] == "extended_v1"
    assert manifest["resolved_config"]["fills"]["entry_start_minute"] == 968
    assert manifest["status"] == "complete" and manifest["agent"] == "test"
    summary = json.loads((folder / ("study.json" if study else "metrics.json")).read_text())
    assert summary["counts"]["unresolved_positions"] == int(unresolved)
    assert summary["counts"]["lookahead_checks"] == 1
    if study:
        events = pq.read_table(folder / "events.parquet").to_pylist()
        assert len(events) == 1 and events[0]["completed"] == (not unresolved)
        assert summary["eligible_for_portfolio"] == (not unresolved)
        assert "unresolved positions" in (folder / "study.md").read_text()
    else:
        assert summary["execution_risk"]["eligible"] == (not unresolved)
        positions = pq.read_table(folder / "unresolved.parquet").to_pylist()
        assert len(positions) == int(unresolved)
        equity = pq.read_table(folder / "marked_equity.parquet").to_pylist()
        if unresolved:
            assert summary["trades"] == 0 and equity[0]["net"] < 0
            assert "invalidate" in (folder / "tearsheet.md").read_text()
