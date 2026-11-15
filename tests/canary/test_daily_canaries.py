"""Canaries for the daily engine: known-answer runs that must come out as expected."""

import numpy as np
import pytest

from kinn.alpha.base import LookaheadError
from kinn.costs import model as cost_model
from kinn.engine.daily.engine import BookConfig, BookState, DailyEngine
from kinn.execution.auction import AuctionExecution
from kinn.portfolio.construct import Limits, MeanVariance, RankedBook
from kinn.risk.model import SingleIndexRisk
from tests.daily_helpers import Trailing, make_data

COSTS = cost_model.load("ibkr_pro_tiered")
T, N, START = 330, 40, 70


def random_walk(seed=0, vol=0.02):
    rng = np.random.default_rng(seed)
    close = 100 * np.cumprod(1 + rng.normal(0, vol, (T, N)), axis=0)
    return make_data(close, open_=np.vstack([close[:1], close[:-1]]))  # opens at the prior close


def book(data, alpha, constructor=None, at="close", **config):
    return DailyEngine(
        data=data, alphas=[(alpha, 1.0)], risk_model=SingleIndexRisk(window=60, min_obs=40),
        constructor=constructor or MeanVariance(), execution=AuctionExecution(at=at),
        limits=Limits(sector=None), costs=COSTS,
        config=BookConfig(account=100_000.0, **{"rebalance": "weekly", **config}),
        start_index=START,
    )  # fmt: skip


def run(engine):
    state = BookState.from_dict({"cash": 100_000.0, "positions": {}}, engine.data, START)
    return engine.run(state, START, T)


class Peeking:
    """Reads the session's own return through the view's back door."""

    name, lookback = "peeking", 1

    def scores(self, view):
        return view._data.ret[view._i].astype(float)


class Noise:
    name, lookback = "noise", 1

    def scores(self, view):
        return np.random.default_rng(view.day.toordinal()).normal(size=N)


def test_canary_an_alpha_that_reads_the_sessions_own_return_is_caught():
    with pytest.raises(LookaheadError):
        run(book(random_walk(), Peeking(), at="open", lookahead_check_rate=1.0))


def test_canary_without_the_check_the_peeking_alpha_would_look_brilliant():
    result = run(
        book(random_walk(), Peeking(), at="open", rebalance="daily", lookahead_check_rate=0.0)
    )
    assert sum(r["pnl"] for r in result.daily) > 50_000  # which is why the check exists


def test_canary_a_random_book_on_random_prices_loses_about_its_costs():
    losses, costs = [], []
    for seed in range(6):
        result = run(book(random_walk(seed), Noise(), RankedBook(count=10), borrow_rate=0.0))
        losses.append(sum(r["pnl"] for r in result.daily))
        costs.append(sum(r["commission"] + r["fees"] + r["slippage"] for r in result.daily))
    assert np.mean(costs) > 500
    # Before costs the book earns nothing on average; noise across six books is a few thousand.
    assert abs(np.mean(losses) + np.mean(costs)) < 2500
    assert np.mean(losses) < 0


def test_canary_the_same_book_gives_the_same_fills_every_time():
    a = run(book(random_walk(), Trailing(20), lookahead_check_rate=1.0))
    b = run(book(random_walk(), Trailing(20), lookahead_check_rate=1.0))
    assert a.fills == b.fills and a.daily == b.daily and len(a.fills) > 100
    assert a.counts["lookahead_checks"] == a.counts["rebalances"] > 30
