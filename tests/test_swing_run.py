"""Swing runs: which signals the rule finds, how the book fills its slots, and a run end to end."""

from __future__ import annotations

import json
import math
from datetime import date, timedelta

import pyarrow as pa
import pytest
import yaml

from kinn import swing_run
from kinn.costs import model as cost_model
from kinn.swing_run import Rule, Signal

RULE = Rule(jump=0.15, volume=5, cap_min=5e7, cap_max=3e8, hold=3)
DAYS = [date(2020, 3, 2) + timedelta(days=i) for i in range(8)]  # consecutive, for simplicity


def _panel(closes, *, volume=None, cap=1e8, gap_before=None, permaticker=1, symbol="AAA"):
    """One stock's rows. ``closes[i]`` is day i's close; it opens at the previous close."""
    rows, previous = [], closes[0]
    for i, close in enumerate(closes):
        prev_date = DAYS[i] - timedelta(days=1)
        if gap_before == i:
            prev_date = DAYS[i] - timedelta(days=200)
        rows.append({
            "date": DAYS[i], "permaticker": permaticker, "symbol": symbol,
            "category": "Domestic Common Stock", "open": previous, "low": min(previous, close),
            "close": close, "prev_close": previous, "prev_date": prev_date,
            "dollar_volume": (volume or [1e6] * len(closes))[i], "adv20_prev": 1e6,
            "marketcap_prev": cap,
        })  # fmt: skip
        previous = close
    return rows


def _events(day, permaticker=1, codes="22|91"):
    return pa.table({"permaticker": [permaticker], "date": [day], "eventcodes": [codes]})


def _find(rows, events, rule=RULE):
    return swing_run.find_signals(
        pa.Table.from_pylist(rows), events, rule, DAYS[0], DAYS[-1], DAYS[-1]
    )


JUMP = [10, 10, 11, 12, 12.6, 12.6, 13.86, 13.86]  # +10% then +9.1%: 20% over days 2 and 3
BUSY = [1e6, 1e6, 6e6, 1e6, 1e6, 1e6, 1e6, 1e6]


def test_a_jump_on_earnings_with_volume_is_bought_next_open_and_held_for_the_hold():
    (signal,) = _find(_panel(JUMP, volume=BUSY), _events(DAYS[2]))
    assert signal.day == DAYS[3] and signal.volume == pytest.approx(6.0)
    assert signal.dates == tuple(DAYS[4:7]) and signal.complete and not signal.forced
    assert signal.entry_price == 12  # day 4 opens at day 3's close
    assert math.exp(sum(signal.returns)) - 1 == pytest.approx(13.86 / 12 - 1)


@pytest.mark.parametrize(
    "change",
    [
        {"events": _events(DAYS[2], codes="71|91")},  # an 8-K, but not earnings
        {"events": _events(DAYS[5])},  # earnings filed after the signal day
        {"volume": [1e6] * 8},  # no unusual volume
        {"cap": 4e7},  # too small
        {"cap": 4e8},  # too large
        {"gap_before": 3},  # back from a long halt: no two-day return
    ],
)
def test_each_condition_of_the_rule_is_needed(change):
    events = change.pop("events", _events(DAYS[2]))
    assert _find(_panel(JUMP, **{"volume": BUSY, **change}), events) == []


def test_a_hold_cut_short_is_open_if_the_data_ends_and_forced_if_the_stock_stops():
    cut = _panel(JUMP, volume=BUSY)[:6]  # two sessions after the signal, then nothing
    events = _events(DAYS[2])
    table = pa.Table.from_pylist(cut)
    (at_end,) = swing_run.find_signals(table, events, RULE, DAYS[0], DAYS[5], DAYS[5])
    assert not at_end.complete and not at_end.forced
    (stopped,) = swing_run.find_signals(table, events, RULE, DAYS[0], DAYS[7], DAYS[7])
    assert not stopped.complete and stopped.forced


def _signal(day_index, symbol, volume, *, returns=(0.0, 0.1, 0.0), complete=True, forced=False):
    dates = tuple(DAYS[day_index + 1 : day_index + 1 + len(returns)])
    return Signal(DAYS[day_index], hash(symbol) % 1000, symbol, volume, 5e5, dates, returns,
                  10.0, complete, forced)  # fmt: skip


def _simulate(signals, slots=1):
    return swing_run.simulate(
        signals, account=2000.0 * slots, slots=slots, costs=cost_model.load("ibkr_pro_tiered"),
        allowance_bps=[[1e6, 10], [0, 25]], spread_bps=[[1e6, 43], [0, 100]],
    )  # fmt: skip


def test_the_busiest_signal_takes_the_slot_and_a_slot_frees_the_day_after_the_exit():
    first, rival = _signal(0, "AAA", 6.0), _signal(0, "BBB", 9.0)
    overlapping, after = _signal(2, "CCC", 7.0), _signal(3, "DDD", 7.0)
    trades, counts, _ = _simulate([first, rival, overlapping, after])
    assert [t.symbol for t in trades] == ["BBB", "DDD"]  # BBB exits on day 3; DDD enters day 4
    assert counts["signals"] == 4 and counts["rejected_capital"] == 2


def test_a_trade_pays_the_allowance_each_way_and_twice_that_at_2x():
    (trade,), _, extra = _simulate([_signal(0, "AAA", 6.0)])
    assert trade.quantity == 200 and trade.notional == 2000 and trade.day == DAYS[3]
    exit_value = 2000 * math.exp(0.1)
    assert trade.gross == pytest.approx(exit_value - 2000)
    assert trade.slippage == pytest.approx(0.0025 * (2000 + exit_value))
    assert trade.net == pytest.approx(trade.gross - trade.commission - trade.fees - trade.slippage)
    assert trade.net_2x == pytest.approx(trade.net - trade.slippage)
    crossed = (trade.gross - trade.commission - trade.fees - 0.01 * (2000 + exit_value)) / 2000
    assert extra["spread_crossed_mean_return"] == pytest.approx(crossed)


def test_an_unfinished_hold_is_not_a_trade_and_a_stopped_stock_pays_the_forced_exit_cost():
    open_at_end = _signal(0, "AAA", 6.0, returns=(0.0,), complete=False)
    stopped = _signal(4, "BBB", 6.0, returns=(0.0, -0.5), complete=False, forced=True)
    (trade,), counts, _ = _simulate([open_at_end, stopped])
    assert counts["open_at_end"] == 1 and counts["forced_exits"] == 1
    assert trade.symbol == "BBB" and trade.exit_reason == "forced"
    exit_value = 2000 * math.exp(-0.5)
    assert trade.slippage == pytest.approx(0.0025 * 2000 + 0.02 * exit_value)


def test_a_run_end_to_end_on_the_synthetic_build(built, tmp_path, monkeypatch):
    folder = tmp_path / "strategies" / "drift"
    (folder / "configs").mkdir(parents=True)
    (folder / "strategy.yaml").write_text(
        "name: drift\nfamily: drift\nprior_trials: 0\ncost_calibration: ibkr_pro_tiered\n"
    )
    config = {
        "period": {"start": "2023-10-02", "end": "2023-11-08"},
        "rule": {"jump": 0.0, "volume": 0.0, "cap_min": 0, "cap_max": 1e15, "hold": 3},
        "book": {"account": 20000, "slots": 10},
        "costs": {"allowance_bps": [[0, 25]], "spread_bps": [[0, 100]]},
    }
    (folder / "configs" / "smoke.yaml").write_text(yaml.safe_dump(config))
    monkeypatch.setenv("KINN_STRATEGIES_DIR", str(tmp_path / "strategies"))
    run_dir = swing_run.run("drift", "smoke", settings=built, scratch=True, agent="test")
    manifest = json.loads((run_dir / "manifest.json").read_text())
    metrics = json.loads((run_dir / "metrics.json").read_text())
    assert manifest["kind"] == "swing" and manifest["status"] == "complete"
    assert metrics["trades"] == metrics["counts"]["signals"] - metrics["counts"]["open_at_end"]
    assert (run_dir / "tearsheet.md").exists() and "swing" in metrics
    assert swing_run.headline(run_dir).startswith(f"{metrics['trades']} trades")


def test_the_holdout_is_refused_without_the_owners_token(built, tmp_path, monkeypatch):
    from kinn.data.seal import HoldoutError

    folder = tmp_path / "strategies" / "drift"
    (folder / "configs").mkdir(parents=True)
    (folder / "strategy.yaml").write_text(
        "name: drift\nfamily: drift\nprior_trials: 0\ncost_calibration: ibkr_pro_tiered\n"
    )
    (folder / "configs" / "late.yaml").write_text(
        "period: {start: 2023-11-09, end: 2023-11-10}\n"
        "rule: {jump: 0.15, volume: 5, cap_min: 0, cap_max: 1e15, hold: 3}\n"
        "book: {account: 20000, slots: 10}\n"
        "costs: {allowance_bps: [[0, 25]], spread_bps: [[0, 100]]}\n"
    )
    monkeypatch.setenv("KINN_STRATEGIES_DIR", str(tmp_path / "strategies"))
    monkeypatch.delenv("KINN_UNSEAL_TOKEN", raising=False)
    with pytest.raises(HoldoutError):
        swing_run.run("drift", "late", settings=built, scratch=True, agent="test")
    with pytest.raises(HoldoutError):
        swing_run.run("drift", "late", settings=built, scratch=True, agent="test", unseal=True)


# ---- The quality test: up over the year, or net debt ----

HISTORY = 255
LONG = [date(2019, 1, 1) + timedelta(days=i) for i in range(HISTORY + len(JUMP))]
QUALITY = Rule(jump=0.15, volume=5, cap_min=5e7, cap_max=3e8, hold=3, skip_fallen_cash_rich=True)


def _with_history(base):
    """The jump of ``JUMP`` after 255 sessions at ``base``; the signal's close is 12."""
    closes, volume = [base] * HISTORY + JUMP, [1e6] * HISTORY + BUSY
    rows, previous = [], closes[0]
    for day, close, dollars in zip(LONG, closes, volume, strict=True):
        rows.append({
            "date": day, "permaticker": 1, "symbol": "AAA", "category": "Domestic Common Stock",
            "open": previous, "low": min(previous, close), "close": close,
            "prev_close": previous, "prev_date": day - timedelta(days=1),
            "dollar_volume": dollars, "adv20_prev": 1e6, "marketcap_prev": 1e8,
        })  # fmt: skip
        previous = close
    return pa.Table.from_pylist(rows)


def _reports(cash, debt, *, filed=LONG[100]):
    return pa.table({"permaticker": [1], "datekey": [filed], "cashnequsd": [float(cash)],
                     "debtusd": [float(debt)]})  # fmt: skip


def _quality(base, reports, rule=QUALITY):
    events = _events(LONG[HISTORY + 2])
    first = LONG[HISTORY]  # the two sessions before the jump are loaded but not signal days
    return swing_run.find_signals(_with_history(base), events, rule, first, LONG[-1], LONG[-1],
                                  reports)  # fmt: skip


def test_a_signal_carries_its_years_return_and_net_cash():
    (signal,) = _quality(15, _reports(5, 1), rule=RULE)  # the plain rule takes everything
    assert signal.day == LONG[HISTORY + 3]
    assert signal.year_return == pytest.approx(12 / 15 - 1) and signal.net_cash == 4
    (bare,) = swing_run.find_signals(_with_history(15), _events(LONG[HISTORY + 2]), RULE,
                                     LONG[HISTORY], LONG[-1], LONG[-1])  # fmt: skip
    assert bare.net_cash is None and bare.year_return == pytest.approx(-0.2)


def test_fallen_and_cash_rich_is_skipped_and_either_fact_alone_is_enough():
    assert _quality(15, _reports(5, 1)) == []  # down 20% over the year, net cash
    assert len(_quality(8, _reports(5, 1))) == 1  # up 50%, net cash
    assert len(_quality(15, _reports(1, 5))) == 1  # down, but net debt
    assert _quality(15, _reports(5, 5)) == []  # cash equal to debt is not net debt
    assert _quality(12, _reports(5, 1)) == []  # flat over the year is not up


def test_a_missing_fact_does_not_qualify_and_a_report_filed_that_day_is_not_used():
    assert _quality(15, None) == []  # down, and nothing known about the balance sheet
    signal_day = LONG[HISTORY + 3]
    assert _quality(15, _reports(1, 5, filed=signal_day)) == []  # filed on the signal day
    assert len(_quality(15, _reports(1, 5, filed=signal_day - timedelta(days=1)))) == 1
    # Too little history for a year's return: only net debt can qualify it.
    short = _with_history(8).slice(100)
    events = _events(LONG[HISTORY + 2])
    args = (events, QUALITY, LONG[HISTORY], LONG[-1], LONG[-1])
    assert swing_run.find_signals(short, *args, _reports(5, 1)) == []
    assert len(swing_run.find_signals(short, *args, _reports(1, 5))) == 1


def test_the_rule_reads_its_switch_from_a_config():
    rule = Rule.from_config({"jump": 0.15, "volume": 5, "cap_min": 5e7, "cap_max": 3e8,
                             "hold": 15, "skip_fallen_cash_rich": True})  # fmt: skip
    assert rule.hold == 15 and rule.skip_fallen_cash_rich is True and rule.jump == 0.15
    assert Rule.from_config({"jump": 0.15, "volume": 5, "cap_min": 5e7, "cap_max": 3e8,
                             "hold": 15}).skip_fallen_cash_rich is False  # fmt: skip
