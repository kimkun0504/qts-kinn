"""Execution rules, each on a hand-built session where the right answer is obvious."""

from datetime import date

import pytest

from kinn.core.types import Signal
from kinn.costs import model as cost_model
from kinn.engine.intraday.data import DayData, DayView, make_symbol_day
from kinn.engine.intraday.simulator import FillConfig, simulate_day
from kinn.risk.sizing import RiskConfig

COSTS = cost_model.load("ibkr_pro_tiered")
DAY = date(2020, 1, 2)
RISK = RiskConfig(position_dollars=1000.0, buying_power=10_000.0)
FULL = FillConfig(participation=1.0)


def session(bars, *, symbol="AAA", official_close=None, adv=5e7, close_minute=960):
    """bars: list of (minute, open, high, low, close, volume)."""
    cols = list(zip(*bars, strict=True)) if bars else [[]] * 6
    sd = make_symbol_day(
        symbol,
        1,
        cols[0],
        cols[1],
        cols[2],
        cols[3],
        cols[4],
        cols[5],
        {"prev_close": 10.0, "adv20_prev": adv},
    )
    closes = {} if official_close is None else {symbol: official_close}
    return DayData(DayView(DAY, 570, close_minute, {symbol: sd}), closes)


def run(data, signals, risk=RISK, config=FULL):
    return simulate_day(data, signals, risk=risk, config=config, costs=COSTS)


def flat(minute, price, volume=10_000):
    return (minute, price, price, price, price, volume)


def test_a_market_order_fills_at_the_next_bars_open_never_the_signal_bar():
    data = session(
        [flat(600, 10.0), (601, 10.5, 10.6, 10.4, 10.5, 10_000), flat(955, 11.0)],
        official_close=11.0,
    )
    (trade,) = run(data, [Signal("AAA", 600)]).trades
    assert trade.entry_minute == 601 and trade.entry_price == 10.5
    assert trade.exit_minute == 955 and trade.exit_reason == "flatten"


def test_a_premarket_signal_waits_for_the_open():
    data = session([flat(500, 9.0), flat(570, 10.0), flat(955, 10.0)], official_close=10.0)
    (trade,) = run(data, [Signal("AAA", 480)]).trades
    assert trade.entry_minute == 570


@pytest.mark.parametrize(("low", "filled"), [(9.50, False), (9.495, False), (9.49, True)])
def test_a_limit_order_needs_a_trade_through(low, filled):
    data = session(
        [flat(600, 10.0), (601, 9.8, 9.8, low, 9.6, 10_000), flat(955, 9.7)], official_close=9.7
    )
    result = run(data, [Signal("AAA", 600, limit_price=9.50)])
    assert len(result.trades) == int(filled) and result.unfilled == int(not filled)
    if filled:
        assert result.trades[0].entry_price == 9.50  # at the limit, no price improvement


def test_price_improvement_is_off_by_default_and_can_be_turned_on():
    bars = [flat(600, 10.0), (601, 9.0, 9.2, 8.9, 9.1, 10_000), flat(955, 9.1)]
    signal = Signal("AAA", 600, limit_price=9.50)
    assert run(session(bars, official_close=9.1), [signal]).trades[0].entry_price == 9.50
    improved = FillConfig(participation=1.0, limit_fills_at_limit=False)
    trades = run(session(bars, official_close=9.1), [signal], config=improved).trades
    assert trades[0].entry_price == 9.0


def test_a_limit_order_expires():
    data = session([flat(600, 10.0), flat(610, 10.0), (620, 9.0, 9.0, 9.0, 9.0, 10_000)])
    result = run(data, [Signal("AAA", 600, limit_price=9.5, expire_minute=615)])
    assert not result.trades and result.unfilled == 1


def test_a_stop_gapped_through_fills_at_the_open_not_at_the_stop():
    data = session([flat(600, 10.0), flat(601, 10.0), (602, 9.0, 9.1, 8.9, 9.0, 10_000)])
    (trade,) = run(data, [Signal("AAA", 600, stop_pct=0.05)]).trades
    assert trade.exit_reason == "stop" and trade.exit_price == 9.0  # stop was 9.50


def test_a_stop_touched_inside_a_bar_fills_at_the_stop():
    data = session([flat(600, 10.0), flat(601, 10.0), (602, 9.9, 9.9, 9.4, 9.8, 10_000)])
    (trade,) = run(data, [Signal("AAA", 600, stop_pct=0.05)]).trades
    assert trade.exit_reason == "stop" and trade.exit_price == pytest.approx(9.5)


def test_when_stop_and_target_are_both_touched_the_stop_wins():
    data = session([flat(600, 10.0), flat(601, 10.0), (602, 10.0, 11.5, 9.0, 10.0, 10_000)])
    (trade,) = run(data, [Signal("AAA", 600, stop_pct=0.05, target_pct=0.05)]).trades
    assert trade.exit_reason == "stop"


def test_no_profit_is_taken_in_the_entry_bar_but_a_stop_there_is_hit():
    up = session(
        [
            flat(600, 10.0),
            (601, 10.0, 11.0, 10.0, 11.0, 10_000),
            flat(602, 11.0),
            (603, 11.0, 11.2, 11.0, 11.0, 10_000),
        ]
    )
    (trade,) = run(up, [Signal("AAA", 600, target_pct=0.05)]).trades
    assert trade.exit_reason == "target" and trade.exit_minute == 602  # not 601
    assert trade.exit_price == pytest.approx(10.5)
    down = session([flat(600, 10.0), (601, 10.0, 10.0, 9.0, 9.2, 10_000), flat(602, 9.2)])
    (trade,) = run(down, [Signal("AAA", 600, stop_pct=0.05)]).trades
    assert trade.exit_reason == "stop" and trade.entry_minute == trade.exit_minute == 601


def test_participation_cap_spreads_a_fill_over_bars():
    data = session(
        [
            flat(600, 10.0),
            flat(601, 10.0, 400),
            flat(602, 10.0, 400),
            flat(603, 10.0, 4000),
            flat(955, 10.0, 100_000),
        ],
        official_close=10.0,
    )
    config = FillConfig(participation=0.1)
    (trade,) = run(data, [Signal("AAA", 600)], config=config).trades
    assert trade.quantity == 100 and trade.entry_minute == 601  # 40 + 40 + 20 shares


def test_no_bar_means_no_fill_and_the_auction_takes_the_rest():
    # Trading stops after the entry (a halt): nothing can be sold until the closing auction.
    data = session([flat(600, 10.0), flat(601, 10.0)], official_close=9.0)
    (trade,) = run(data, [Signal("AAA", 600, stop_pct=0.02)]).trades
    assert trade.exit_reason == "auction" and trade.exit_minute == 960 and trade.exit_price == 9.0
    no_close = session([flat(600, 10.0), flat(601, 10.0)])
    (forced,) = run(no_close, [Signal("AAA", 600)]).trades
    assert forced.exit_reason == "forced" and forced.slippage > trade.slippage


def test_positions_are_flat_before_the_close_and_entries_stop_before_it():
    data = session(
        [flat(600, 10.0), flat(601, 10.0), flat(954, 10.2), flat(955, 10.3), flat(956, 10.4)],
        official_close=10.5,
    )
    (trade,) = run(data, [Signal("AAA", 600)]).trades
    assert trade.exit_minute == 955 and trade.exit_price == 10.3
    late = run(data, [Signal("AAA", 950)])
    assert not late.trades and late.unfilled == 1
    early_close = session(
        [flat(600, 10.0), flat(601, 10.0), flat(775, 10.2), flat(900, 99.0)],
        official_close=10.2,
        close_minute=780,
    )
    (trade,) = run(early_close, [Signal("AAA", 600)]).trades
    assert trade.exit_minute == 775


def test_max_hold_exits_on_time():
    data = session(
        [flat(600, 10.0), flat(601, 10.0), flat(630, 10.1), flat(631, 10.2), flat(700, 10.5)]
    )
    (trade,) = run(data, [Signal("AAA", 600, max_hold_minutes=30)]).trades
    assert trade.exit_reason == "time" and trade.exit_minute == 631


def test_resting_orders_reserve_buying_power_and_symbols_do_not_stack():
    bars = [flat(600, 10.0), flat(601, 10.0), flat(700, 10.0), flat(955, 10.0)]
    sds = {s: session(bars, symbol=s).view.symbols[s] for s in ("AAA", "BBB", "CCC")}
    data = DayData(DayView(DAY, 570, 960, sds), {s: 10.0 for s in sds})
    risk = RiskConfig(position_dollars=1000.0, buying_power=2000.0)
    resting = Signal("AAA", 600, limit_price=5.0)  # never fills, but holds capital
    result = run(
        data, [resting, Signal("BBB", 600), Signal("CCC", 600), Signal("BBB", 650)], risk=risk
    )
    assert [t.symbol for t in result.trades] == ["BBB"]
    assert result.unfilled == 1 and result.rejected_capital == 2
    # Once the resting order expires its capital is free again.
    expiring = Signal("AAA", 600, limit_price=5.0, expire_minute=620)
    result = run(data, [expiring, Signal("BBB", 600), Signal("CCC", 650)], risk=risk)
    assert sorted(t.symbol for t in result.trades) == ["BBB", "CCC"]


def test_a_share_that_costs_more_than_the_position_is_rejected():
    data = session([flat(600, 5000.0), flat(601, 5000.0)])
    result = run(data, [Signal("AAA", 600)])
    assert not result.trades and result.rejected_size == 1


def test_costs_add_up_and_2x_doubles_only_the_slippage():
    data = session(
        [flat(600, 10.0), flat(601, 10.0), flat(955, 10.0)], official_close=10.0, adv=1e6
    )
    (trade,) = run(data, [Signal("AAA", 600)]).trades
    assert trade.quantity == 100 and trade.gross == 0
    assert trade.commission == pytest.approx(0.70)  # two orders at the $0.35 minimum
    # 25 bps half-spread at this liquidity, on both marketable legs of $1,000; no impact (flat bars)
    assert trade.slippage == pytest.approx(2 * 1000 * 0.0025)
    expected_fees = (
        2 * 100 * (0.0030 + 0.00020 + 0.000003) + 0.70 * 0.00074
        + 1000 * 0.0000206 + 100 * 0.000195
    )  # fmt: skip
    assert trade.fees == pytest.approx(expected_fees)
    assert trade.net == pytest.approx(-(trade.commission + trade.fees + trade.slippage))
    assert trade.net_2x == pytest.approx(trade.net - trade.slippage)


def test_commission_rules():
    assert COSTS.commission(100, 1000.0) == pytest.approx(0.35)  # minimum
    assert COSTS.commission(1000, 10_000.0) == pytest.approx(3.5)  # per share
    assert COSTS.commission(10, 2.0) == pytest.approx(0.02)  # capped at 1% of value
    assert COSTS.half_spread_bps(20.0, 1e8) == 2.5  # half a tick is the floor: 0.005 / 20
    assert COSTS.half_spread_bps(100.0, 1e8) == 2
    assert COSTS.half_spread_bps(4.0, 3e5) == pytest.approx(75.0)  # under $5 pays 1.5x
    assert COSTS.half_spread_bps(1.0, None) == pytest.approx(150.0)


def _three_symbols(prices_b):
    flat_bars = [
        flat(600, 10.0),
        flat(601, 10.0),
        flat(621, 10.0),
        flat(700, 10.0),
        flat(955, 10.0),
    ]
    sds = {
        "AAA": session(flat_bars, symbol="AAA").view.symbols["AAA"],
        "BBB": session(prices_b, symbol="BBB").view.symbols["BBB"],
        "CCC": session(flat_bars, symbol="CCC").view.symbols["CCC"],
    }
    return DayData(DayView(DAY, 570, 960, sds), {"AAA": 10.0, "BBB": prices_b[-1][4], "CCC": 10.0})


def test_entry_cap_limits_filled_entries_in_a_session():
    data = _three_symbols([flat(600, 10.0), flat(601, 10.0), flat(955, 10.0)])
    signals = [Signal("AAA", 600), Signal("BBB", 600), Signal("CCC", 650)]
    capped = run(data, signals, risk=RiskConfig(position_dollars=1000.0, max_entries_per_session=2))
    assert len(capped.trades) == 2 and capped.rejected_risk == 1
    assert len(run(data, signals).trades) == 3


def test_daily_loss_limit_stops_new_entries_once_the_session_is_down():
    falling = [flat(600, 10.0), flat(601, 10.0), flat(640, 9.0), flat(955, 9.0)]  # BBB loses 10%
    data = _three_symbols(falling)
    signals = [Signal("BBB", 600), Signal("AAA", 620), Signal("CCC", 650)]
    limit = RiskConfig(position_dollars=1000.0, daily_loss_limit=50.0)
    result = run(data, signals, risk=limit)
    # AAA enters at 621, before BBB has fallen. CCC would enter at 700, with BBB down $100.
    assert sorted(t.symbol for t in result.trades) == ["AAA", "BBB"] and result.rejected_risk == 1
    assert len(run(data, signals).trades) == 3
