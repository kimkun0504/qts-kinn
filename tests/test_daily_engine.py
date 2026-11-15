"""The daily engine's accounting: corporate actions, costs, borrow, delistings, resuming."""

import numpy as np
import pytest

from kinn.costs import model as cost_model
from kinn.engine.daily.engine import BookConfig, BookState, DailyEngine
from kinn.execution.auction import AuctionExecution
from kinn.portfolio.construct import Limits, RankedBook
from kinn.risk.model import SingleIndexRisk
from tests.daily_helpers import Fixed, make_data

COSTS = cost_model.load("ibkr_pro_tiered")
LONG_ONE = Limits(gross=0.5, net=0.5, max_weight=0.5, long_only=True, beta=None, sector=None)
PAIR = Limits(gross=1.0, max_weight=0.5, beta=None, sector=None)


def engine(data, scores, *, limits=LONG_ONE, count=1, rebalance=1000, at="close", **config):
    return DailyEngine(
        data=data, alphas=[(Fixed(scores), 1.0)], risk_model=SingleIndexRisk(window=3, min_obs=2),
        constructor=RankedBook(count=count), execution=AuctionExecution(at=at, min_trade=0.0),
        limits=limits, costs=COSTS,
        config=BookConfig(
            account=10_000.0, rebalance=rebalance, lookahead_check_rate=1.0, **config
        ),
        start_index=4,
    )  # fmt: skip


def noisy(t, n, level=100.0, seed=0):
    """Prices with a little noise in the history rows so the risk model has variance."""
    rng = np.random.default_rng(seed)
    close = np.full((t, n), level)
    close[:3] *= 1 + rng.normal(0, 0.01, (3, n))
    return close


def run(eng, data):
    state = BookState.from_dict({"cash": 10_000.0, "positions": {}}, data, eng.start_index)
    return state, eng.run(state, eng.start_index, len(data.dates))


def test_buy_and_hold_ends_with_the_price_move_less_exact_costs():
    close = noisy(8, 2)
    close[5:, 0] = 110.0  # bought at 100 on session 4, then +10%
    data = make_data(close)
    state, result = run(engine(data, [1.0, 0.0]), data)
    (fill,) = result.fills
    assert (fill.symbol, fill.shares, fill.price) == ("S0", 50.0, 100.0)  # half of $10,000
    commission, fees = COSTS.order_fees(side="buy", value=5000, marketable=0, passive=0, auction=50)
    slippage = COSTS.auction_slippage(price=100.0, shares=50)
    assert fill.commission == commission and fill.fees == fees and fill.slippage == slippage
    assert state.equity() == pytest.approx(10_000 + 50 * 10 - commission - fees - slippage)
    last = result.daily[-1]
    assert last["equity"] == pytest.approx(state.equity()) and last["n_long"] == 1
    assert sum(r["pnl_2x"] for r in result.daily) == pytest.approx(
        sum(r["pnl"] for r in result.daily) - slippage
    )


def test_a_split_changes_the_share_count_and_not_the_equity():
    close = noisy(8, 2)
    close[6:, 0] = 50.0
    split = np.ones((8, 2))
    split[6, 0] = 2.0
    data = make_data(close, split=split)
    state, result = run(engine(data, [1.0, 0.0]), data)
    assert state.shares[0] == 100 and state.last_price[0] == 50.0
    assert result.daily[1]["equity"] == pytest.approx(result.daily[-1]["equity"])
    assert all(abs(r["pnl"]) < 1e-9 for r in result.daily[1:])


def test_dividends_are_paid_to_longs_and_charged_to_shorts():
    close = noisy(8, 2)
    dividend = np.zeros((8, 2))
    dividend[6] = [1.0, 2.0]
    data = make_data(close, dividend=dividend)
    state, result = run(engine(data, [1.0, -1.0], limits=PAIR, borrow_rate=0.0), data)
    assert state.shares.tolist() == [50.0, -50.0]
    day = result.daily[2]
    assert day["dividends"] == pytest.approx(50 * 1.0 - 50 * 2.0) and day["pnl"] == pytest.approx(
        -50
    )
    assert day["long_pnl"] == pytest.approx(50) and day["short_pnl"] == pytest.approx(-100)


def test_shorts_pay_the_borrow_fee_every_session():
    data = make_data(noisy(8, 2))
    _, result = run(engine(data, [1.0, -1.0], limits=PAIR, borrow_rate=0.252), data)
    assert result.daily[0]["borrow"] == 0.0  # nothing held before the first rebalance
    assert result.daily[1]["borrow"] == pytest.approx(5000 * 0.252 / 252)
    assert result.daily[1]["pnl"] == pytest.approx(-5.0)


def test_a_company_whose_bars_stop_is_closed_at_its_last_price_with_the_forced_cost():
    close = noisy(14, 2)
    close[6:, 0] = np.nan
    data = make_data(close)
    state, result = run(engine(data, [1.0, 0.0]), data)
    assert state.shares[0] == 0 and result.counts["forced_exits"] == 1
    forced = result.fills[-1]
    assert forced.reason == "delisted" and forced.price == 100.0
    assert forced.day == data.dates[10]  # the fifth session without a bar
    assert forced.slippage == pytest.approx(
        COSTS.auction_slippage(price=100, shares=50, forced=True)
    )


def test_a_run_resumed_from_saved_state_matches_an_uninterrupted_one():
    rng = np.random.default_rng(1)
    close = 100 * np.cumprod(1 + rng.normal(0, 0.02, (30, 6)), axis=0)
    data = make_data(close)
    scores = [3.0, 2.0, 1.0, -1.0, -2.0, -3.0]
    make = lambda: engine(data, scores, limits=PAIR, count=2, rebalance=5)  # noqa: E731
    _, whole = run(make(), data)
    eng = make()
    state = BookState.from_dict({"cash": 10_000.0, "positions": {}}, data, 4)
    first = eng.run(state, 4, 17)
    saved = state.to_dict(data.permatickers)
    resumed = BookState.from_dict(saved, data, 17)
    second = make().run(resumed, 17, 30)
    assert first.daily + second.daily == whole.daily
    assert first.fills + second.fills == whole.fills


@pytest.mark.parametrize(
    ("rule", "expected"), [("daily", 26), ("weekly", 6), ("monthly", 2), (10, 3)]
)
def test_rebalance_rhythm_is_a_setting(rule, expected):
    data = make_data(noisy(30, 2))
    eng = engine(data, [1.0, -1.0], limits=PAIR, rebalance=rule)
    assert sum(eng.is_rebalance(i) for i in range(4, 30)) == expected


def test_execution_at_the_open_fills_at_the_open_price():
    close = noisy(8, 2)
    data = make_data(close, open_=close * 0.99)
    _, result = run(engine(data, [1.0, 0.0], at="open"), data)
    assert result.fills[0].price == pytest.approx(99.0)
    assert result.daily[0]["pnl"] > 0  # bought at the open, marked at the close


def test_a_runaway_gross_exposure_can_trigger_an_early_rebalance():
    close = noisy(12, 2)
    close[6:, 1] = 160.0  # the short runs away: equity falls while the position grows
    data = make_data(close)
    quiet = engine(data, [1.0, -1.0], limits=PAIR, borrow_rate=0.0)
    _, held = run(quiet, data)
    assert held.counts["early_rebalances"] == 0 and len(held.fills) == 2
    alert = engine(data, [1.0, -1.0], limits=PAIR, borrow_rate=0.0, rebalance_if_gross_above=1.1)
    _, cut = run(alert, data)
    assert cut.counts["early_rebalances"] >= 1 and len(cut.fills) > 2
    gross = (cut.daily[-1]["long_value"] + cut.daily[-1]["short_value"]) / cut.daily[-1]["equity"]
    assert gross <= 1.1
