"""The Lab's simulator and book, on small hand-made markets (decision 0023)."""

from __future__ import annotations

import math

import numpy as np
import pytest

from kinn.costs.model import load as load_costs
from kinn.lab import book
from kinn.lab.engine import REASONS, Costs, Market, simulate
from kinn.lab.settings import SettingsError, parse

ROWS = 40


def market(
    close,
    *,
    open_=None,
    high=None,
    low=None,
    adj_close=None,
    eligible=None,
    universe_return=None,
    universe_intraday=None,
) -> Market:
    close = np.asarray(close, dtype=np.float32).reshape(ROWS, -1)
    open_ = close if open_ is None else np.asarray(open_, dtype=np.float32).reshape(close.shape)
    high = (
        np.maximum(open_, close)
        if high is None
        else np.asarray(high, np.float32).reshape(close.shape)
    )
    low = (
        np.minimum(open_, close)
        if low is None
        else np.asarray(low, np.float32).reshape(close.shape)
    )
    return Market(
        open=open_,
        high=high,
        low=low,
        close=close,
        adj_close=close.copy()
        if adj_close is None
        else np.asarray(adj_close, np.float32).reshape(close.shape),
        eligible=np.ones(close.shape, bool) if eligible is None else eligible,
        adv=np.full(close.shape, 5e6, np.float32),
        dollar_volume=np.full(close.shape, 1e6, np.float32),
        universe_return=np.zeros(ROWS, np.float32) if universe_return is None else universe_return,
        universe_intraday=np.zeros(ROWS, np.float32)
        if universe_intraday is None
        else universe_intraday,
    )


def run(m: Market, entries, *, exits=None, **settings):
    sections = {"exit": {}, "entry": {}, "book": {}}
    for key, value in settings.items():
        section = (
            "entry"
            if key in ("mode", "top_n", "rank_order", "side")
            else ("book" if key in ("position_size", "max_positions", "borrow_rate") else "exit")
        )
        sections[section][key] = value
    s = parse(sections)
    costs = Costs(load_costs("ibkr_pro_tiered"))
    return simulate(m, np.asarray(entries), exits, s, costs, 0, ROWS - 2)


def flat(price=10.0, stocks=1):
    return np.full((ROWS, stocks), price, dtype=np.float32)


def signal_at(*rows, stocks=1, col=0):
    entries = np.zeros((ROWS, stocks), bool)
    for r in rows:
        entries[r, col] = True
    return entries


def test_a_signal_buys_the_next_open_and_sells_the_close_of_the_hold():
    close = np.linspace(10, 14, ROWS).astype(np.float32)
    open_ = close - 0.05
    (trade,) = run(market(close, open_=open_), signal_at(5), hold_days=3)
    assert (trade.signal_row, trade.entry_row, trade.exit_row) == (5, 6, 8)
    assert REASONS[trade.reason] == "hold"
    assert trade.entry_price == pytest.approx(open_[6])
    assert trade.exit_price == pytest.approx(close[8])
    assert trade.gross == pytest.approx(close[8] / open_[6] - 1, rel=1e-5)


def test_the_stop_fills_at_its_level_and_wins_over_the_target_on_the_same_day():
    close = flat()
    low, high = flat(), flat()
    low[8], high[8] = 8.5, 12.5  # both touched on row 8
    (trade,) = run(
        market(close, low=low, high=high),
        signal_at(5),
        hold_days=10,
        stop_loss=0.1,
        take_profit=0.2,
    )
    assert REASONS[trade.reason] == "stop" and trade.exit_row == 8
    assert trade.gross == pytest.approx(-0.1, abs=1e-6)


def test_the_target_fills_at_its_level():
    high = flat()
    high[9] = 12.5
    (trade,) = run(market(flat(), high=high), signal_at(5), hold_days=10, take_profit=0.2)
    assert REASONS[trade.reason] == "target" and trade.exit_row == 9
    assert trade.gross == pytest.approx(0.2, abs=1e-6)


def test_a_gap_through_the_stop_fills_at_the_open_not_the_stop():
    open_, low, close = flat(), flat(), flat()
    open_[9], low[9], close[9] = 7.0, 7.0, 7.5
    (trade,) = run(market(close, open_=open_, low=low), signal_at(5), hold_days=10, stop_loss=0.1)
    assert REASONS[trade.reason] == "stop" and trade.exit_row == 9
    assert trade.gross == pytest.approx(-0.3, abs=1e-6)


def test_the_exit_signal_sells_at_the_next_open():
    open_ = flat()
    open_[11] = 11.0
    exits = signal_at(10)
    (trade,) = run(market(flat(), open_=open_), signal_at(5), exits=exits, hold_days=20)
    assert REASONS[trade.reason] == "exit signal" and trade.exit_row == 11
    assert trade.gross == pytest.approx(0.1, abs=1e-6)


def test_one_position_per_stock_and_a_new_one_after_the_exit():
    trades = run(market(flat()), signal_at(5, 6, 7, 8, 9), hold_days=4)
    assert [(t.entry_row, t.exit_row) for t in trades] == [(6, 9), (10, 13)]


def test_a_split_in_the_hold_is_not_a_loss():
    close = flat(100.0)
    close[12:] = 50.0  # 2-for-1 on row 12
    adj = flat(50.0)  # anchored adjustment: the same price in today's terms
    (trade,) = run(market(close, adj_close=adj), signal_at(5), hold_days=10)
    assert trade.gross == pytest.approx(0.0, abs=1e-6)
    assert trade.entry_price == pytest.approx(100.0) and trade.exit_price == pytest.approx(50.0)


def test_no_entry_when_the_stock_is_not_eligible_that_morning():
    eligible = np.ones((ROWS, 1), bool)
    eligible[6] = False
    assert run(market(flat(), eligible=eligible), signal_at(5), hold_days=3) == []


def test_a_stock_that_stops_trading_sells_at_its_last_close():
    close = flat()
    close[10:] = np.nan
    (trade,) = run(market(close), signal_at(5), hold_days=10)
    assert REASONS[trade.reason] == "stopped trading" and trade.exit_row == 9


def test_a_hold_past_the_end_of_the_data_sells_at_the_last_close():
    (trade,) = run(market(flat()), signal_at(30), hold_days=20)
    assert REASONS[trade.reason] == "data end" and trade.exit_row == ROWS - 1


def test_costs_come_off_both_ways_and_twice_the_slippage_costs_more():
    (trade,) = run(market(flat(25.0)), signal_at(5), hold_days=5, position_size=5000)
    assert trade.gross == 0
    assert trade.net_2x < trade.net < 0
    assert (trade.gross - trade.net) * trade.value == pytest.approx(
        trade.cost_entry + trade.cost_exit, rel=1e-9
    )
    assert trade.shares == 200 and trade.value == pytest.approx(5000)


def test_the_benchmark_is_the_universe_over_the_same_sessions():
    ur = np.full(ROWS, 0.01, np.float32)
    ui = np.full(ROWS, 0.004, np.float32)
    (trade,) = run(
        market(flat(), universe_return=ur, universe_intraday=ui), signal_at(5), hold_days=3
    )
    # Entry open of row 6 to the close of row 8: row 6's open-to-close, then rows 7 and 8.
    assert trade.benchmark == pytest.approx(1.004 * math.exp(2 * math.log1p(0.01)) - 1, rel=1e-5)


def test_rank_mode_takes_the_top_scores_each_day():
    scores = np.full((ROWS, 3), np.nan)
    scores[5] = [1.0, 3.0, 2.0]
    trades = run(market(flat(stocks=3)), scores, mode="rank", top_n=2, hold_days=3)
    assert sorted(t.stock for t in trades) == [1, 2]
    trades = run(
        market(flat(stocks=3)), scores, mode="rank", top_n=1, rank_order="lowest", hold_days=3
    )
    assert [t.stock for t in trades] == [0]


def test_rank_mode_keeps_one_position_per_stock():
    scores = np.full((ROWS, 2), np.nan)
    scores[5:10] = [2.0, 1.0]
    trades = run(market(flat(stocks=2)), scores, mode="rank", top_n=1, hold_days=3)
    # Stock 0 is held rows 6-8, so on the next two days the best free stock is stock 1, and
    # on row 7 neither is free.
    assert [(t.stock, t.entry_row) for t in trades] == [(0, 6), (1, 7), (0, 9), (1, 10)]


def test_the_book_caps_open_positions_and_a_slot_frees_after_the_exit_day():
    close = flat(stocks=3)
    entries = np.zeros((ROWS, 3), bool)
    entries[5] = [True, True, False]
    entries[8, 2] = True  # enters row 9, the day the first two exit: no slot yet
    trades = run(market(close), entries, hold_days=4)
    taken = book.select(trades, cap=2)
    assert taken.tolist() == [True, True, False]
    later = np.zeros((ROWS, 3), bool)
    later[5] = [True, True, False]
    later[9, 2] = True  # entry row 10, after the exit row 9
    trades = run(market(close), later, hold_days=4)
    assert book.select(trades, cap=2).tolist() == [True, True, True]


def test_the_book_profit_adds_up_to_the_trades_it_took():
    close = np.linspace(10, 16, ROWS).astype(np.float32).reshape(ROWS, 1).repeat(2, axis=1)
    close[:, 1] = np.linspace(20, 15, ROWS)
    m = market(close)
    entries = np.zeros((ROWS, 2), bool)
    entries[[3, 12, 25], 0] = True
    entries[[4, 20], 1] = True
    trades = run(m, entries, hold_days=6)
    taken = book.select(trades, cap=1)
    daily = book.daily(trades, taken, m)
    expected = sum(t.value * t.net for t, k in zip(trades, taken, strict=True) if k)
    assert daily["pnl"].sum() == pytest.approx(expected, rel=1e-6)
    assert daily["positions"].max() == 1


def test_a_short_gains_what_the_price_loses_and_pays_to_borrow():
    close = np.linspace(20, 16, ROWS).astype(np.float32)
    (trade,) = run(market(close), signal_at(5), hold_days=10, side="short", borrow_rate=0.05)
    (long,) = run(market(close), signal_at(5), hold_days=10)
    assert trade.short and (trade.entry_row, trade.exit_row) == (6, 15)
    assert trade.gross == pytest.approx(-long.gross, rel=1e-6) and trade.gross > 0
    assert trade.borrow == pytest.approx(trade.value * 0.05 * 10 / 252, rel=1e-9)
    assert (trade.gross - trade.net) * trade.value == pytest.approx(
        trade.cost_entry + trade.cost_exit, rel=1e-9
    )
    free = run(market(close), signal_at(5), hold_days=10, side="short", borrow_rate=0)[0]
    assert free.net - trade.net == pytest.approx(trade.borrow / trade.value, rel=1e-6)


def test_a_short_stop_is_above_the_entry_and_wins_over_the_target():
    close, low, high = flat(), flat(), flat()
    low[8], high[8] = 7.5, 11.5  # both touched on row 8
    (trade,) = run(
        market(close, low=low, high=high),
        signal_at(5),
        hold_days=10,
        stop_loss=0.1,
        take_profit=0.2,
        side="short",
    )
    assert REASONS[trade.reason] == "stop" and trade.exit_row == 8
    assert trade.exit_price == pytest.approx(11.0) and trade.gross == pytest.approx(-0.1, abs=1e-6)


def test_a_short_target_is_below_the_entry():
    low = flat()
    low[9] = 7.5
    (trade,) = run(
        market(flat(), low=low), signal_at(5), hold_days=10, take_profit=0.2, side="short"
    )
    assert REASONS[trade.reason] == "target" and trade.exit_price == pytest.approx(8.0)
    assert trade.gross == pytest.approx(0.2, abs=1e-6)


def test_a_gap_up_through_a_short_stop_fills_at_the_open():
    open_, high, close = flat(), flat(), flat()
    open_[9], high[9], close[9] = 13.0, 13.0, 12.5
    m = market(close, open_=open_, high=high)
    (trade,) = run(m, signal_at(5), hold_days=10, stop_loss=0.1, side="short")
    assert REASONS[trade.reason] == "stop" and trade.exit_row == 9
    assert trade.gross == pytest.approx(-0.3, abs=1e-6)


def test_a_short_against_a_rising_universe_beats_it_by_both():
    ur = np.full(ROWS, 0.01, np.float32)
    m = market(flat(), universe_return=ur)
    (trade,) = run(m, signal_at(5), hold_days=3, side="short", borrow_rate=0)
    (long,) = run(m, signal_at(5), hold_days=3)
    assert trade.benchmark == pytest.approx(-long.benchmark, rel=1e-6) and trade.benchmark < 0


def test_the_book_marks_a_short_and_adds_up_to_its_trades():
    close = np.linspace(20, 14, ROWS).astype(np.float32).reshape(ROWS, 1).repeat(2, axis=1)
    close[:, 1] = np.linspace(10, 13, ROWS)
    m = market(close)
    entries = np.zeros((ROWS, 2), bool)
    entries[[3, 12, 25], 0] = True
    entries[[4, 20], 1] = True
    trades = run(m, entries, hold_days=6, side="short")
    taken = book.select(trades, cap=2)
    daily = book.daily(trades, taken, m)
    expected = sum(t.value * t.net for t, k in zip(trades, taken, strict=True) if k)
    assert daily["pnl"].sum() == pytest.approx(expected, rel=1e-6)
    first = trades[0]
    assert first.stock == 0 and daily["pnl"][first.entry_row + 1] > 0


def test_both_sides_buy_one_end_and_short_the_other_with_a_cap_each():
    scores = np.full((ROWS, 6), np.nan)
    scores[5] = [6.0, 5.0, 4.0, 3.0, 2.0, 1.0]
    m = market(flat(stocks=6))
    trades = run(m, scores, mode="rank", top_n=2, hold_days=3, side="both")
    assert [(t.stock, t.short) for t in trades] == [(0, False), (1, False), (5, True), (4, True)]
    assert trades[2].priority > trades[3].priority
    lowest = run(m, scores, mode="rank", top_n=1, hold_days=3, side="both", rank_order="lowest")
    assert [(t.stock, t.short) for t in lowest] == [(5, False), (0, True)]
    few = np.full((ROWS, 3), np.nan)
    few[5] = [3.0, 2.0, 1.0]
    trades = run(market(flat(stocks=3)), few, mode="rank", top_n=2, hold_days=3, side="both")
    assert [(t.stock, t.short) for t in trades] == [(0, False), (1, False), (2, True)]
    assert book.select(trades, cap=1).tolist() == [True, False, True]


def test_both_sides_need_ranking():
    with pytest.raises(SettingsError, match="needs entry.mode 'rank'"):
        parse({"entry": {"side": "both"}})


def test_the_signal_path_is_as_held():
    from kinn.lab import metrics

    close = np.linspace(20, 10, ROWS).astype(np.float32)
    m = market(close)
    (short,) = run(m, signal_at(5), hold_days=5, side="short")
    (long,) = run(m, signal_at(5), hold_days=5)
    as_short = metrics.signal_path([short], m.adj_close, m.universe_cum, 5)
    as_long = metrics.signal_path([long], m.adj_close, m.universe_cum, 5)
    at = as_short["horizons"].index(5)
    assert as_short["stock"][at] > 0 and as_short["stock"][at] == pytest.approx(
        -as_long["stock"][at]
    )


def test_the_factor_report_sorts_returns_by_score():
    from kinn.lab import metrics

    rows, stocks, hold = 80, 40, 5
    drift = np.linspace(-0.002, 0.002, stocks)
    close = 50 * np.exp(np.cumsum(np.tile(drift, (rows, 1)), axis=0)).astype(np.float32)
    ones = np.ones((rows, stocks), dtype=np.float32)
    market = Market(
        open=close.copy(), high=close * 1.01, low=close * 0.99, close=close, adj_close=close,
        eligible=np.ones((rows, stocks), dtype=bool), adv=ones * 1e6, dollar_volume=ones * 1e6,
        universe_return=np.zeros(rows, dtype=np.float32),
        universe_intraday=np.zeros(rows, dtype=np.float32),
    )  # fmt: skip
    scores = np.tile(np.arange(stocks, dtype=np.float64), (rows, 1))
    dates = np.array([f"2015-{1 + i // 28:02d}-{1 + i % 28:02d}" for i in range(rows)])
    report = metrics.factor_report(scores, market, dates, 0, rows - 1, hold, "highest")
    excess = [b["excess"] for b in report["buckets"]]
    assert excess == sorted(excess) and excess[0] < 0 < excess[-1]
    assert report["spread"] > 0 and report["ic"]["mean"] > 0.99
    assert report["ic"]["days"] == rows - hold and report["ic_by_year"][0]["year"] == 2015
    low = metrics.factor_report(scores, market, dates, 0, rows - 1, hold, "lowest")
    assert low["spread"] == -report["spread"]
    few = scores.copy()
    few[:, 5:] = np.nan
    assert metrics.factor_report(few, market, dates, 0, rows - 1, hold, "highest") is None


def test_beta_and_correlation_to_spy():
    from kinn.lab import metrics

    rng = np.random.default_rng(1)
    market_ret = rng.normal(0, 0.01, 200)
    spy = 100 * np.cumprod(1 + market_ret)
    book = 0.5 * market_ret[1:]
    beta, correlation = metrics._against(book, spy, 1, 199)
    assert beta == pytest.approx(0.5) and correlation == pytest.approx(1.0)
    assert metrics._against(book[:10], spy, 1, 10) == (None, None)
