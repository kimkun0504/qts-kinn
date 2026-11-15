"""Portfolio construction, the risk model and auction execution."""

import numpy as np
import pytest

from kinn.execution.auction import AuctionExecution
from kinn.portfolio.construct import Inputs, Limits, MeanVariance, RankedBook
from kinn.risk.model import RiskEstimate, SingleIndexRisk
from tests.daily_helpers import make_data

N = 60


def inputs(seed=0, **over):
    rng = np.random.default_rng(seed)
    risk = RiskEstimate(
        beta=rng.normal(1.0, 0.3, N), specific_var=rng.uniform(0.01, 0.03, N) ** 2,
        total_var=rng.uniform(0.015, 0.035, N) ** 2, market_var=0.01**2,
        sector=np.arange(N) % 4,
    )  # fmt: skip
    base = dict(
        z=rng.normal(0, 1, N), risk=risk, current=np.zeros(N), eligible=np.ones(N, bool),
        tradable=np.ones(N, bool), shortable=np.ones(N, bool), cost=np.full(N, 0.0015),
    )  # fmt: skip
    return Inputs(**{**base, **over})


def test_optimizer_respects_every_limit():
    limits = Limits()
    x = inputs()
    w = MeanVariance().weights(x, limits)
    assert np.abs(w).sum() <= limits.gross + 1e-6
    assert abs(w.sum()) <= limits.net_band + limits.min_weight * 3
    assert np.abs(w).max() <= limits.max_weight + 1e-9
    assert abs(x.risk.beta @ w) <= limits.beta + 0.02
    for code in range(4):
        assert abs(w[x.risk.sector == code].sum()) <= limits.sector + 0.02
    held = w[w != 0]
    assert len(held) >= 20 and np.abs(held).min() >= limits.min_weight
    assert np.corrcoef(w, x.z)[0, 1] > 0.5  # long the high scores, short the low ones


def test_optimizer_never_shorts_what_cannot_be_shorted_and_long_only_means_it():
    shortable = np.arange(N) % 2 == 0
    w = MeanVariance().weights(inputs(shortable=shortable), Limits())
    assert (w[~shortable] >= 0).all() and (w < 0).any()
    long_only = Limits(gross=1.0, net=1.0, long_only=True, beta=None, sector=None)
    w = MeanVariance().weights(inputs(), long_only)
    assert (w >= 0).all() and w.sum() == pytest.approx(1.0, abs=0.1)


def test_positions_that_left_the_universe_are_closed_and_untradable_ones_are_kept():
    current = np.zeros(N)
    current[0], current[1] = 0.04, -0.03
    eligible = np.ones(N, bool)
    eligible[0] = False  # left the universe, still tradable
    tradable = np.ones(N, bool)
    tradable[1] = False  # halted
    for constructor in (MeanVariance(), RankedBook(count=10)):
        w = constructor.weights(
            inputs(current=current, eligible=eligible, tradable=tradable), Limits()
        )
        assert w[0] == 0.0 and w[1] == -0.03


def test_trading_costs_stop_trades_a_small_edge_cannot_pay_for():
    rng = np.random.default_rng(3)
    current = np.zeros(N)
    current[:15], current[15:30] = 0.05, -0.05
    z = np.where(current > 0, 1.0, np.where(current < 0, -1.0, 0.0)) + rng.normal(0, 0.05, N)
    cheap = MeanVariance().weights(inputs(z=z, current=current, cost=np.full(N, 0.0)), Limits())
    dear = MeanVariance().weights(inputs(z=z, current=current, cost=np.full(N, 0.05)), Limits())
    assert np.abs(dear - current).sum() < 0.5 * np.abs(cheap - current).sum() + 1e-9
    assert np.abs(dear - current).sum() < 0.05


def test_ranked_book_is_equal_weight_in_the_best_and_worst_names():
    x = inputs()
    w = RankedBook(count=10).weights(x, Limits(gross=1.0))
    order = np.argsort(x.z)
    assert set(np.flatnonzero(w > 0)) == set(order[-10:]) and np.allclose(w[w > 0], 0.05)
    assert set(np.flatnonzero(w < 0)) == set(order[:10]) and np.allclose(w[w < 0], -0.05)


def test_single_index_model_recovers_betas_and_specific_risk():
    rng = np.random.default_rng(0)
    t, n = 400, 30
    true_beta = rng.uniform(0.5, 1.5, n)
    market = rng.normal(0, 0.01, t)
    returns = true_beta * market[:, None] + rng.normal(0, 0.02, (t, n))
    close = 100 * np.cumprod(1 + returns, axis=0)
    estimate = SingleIndexRisk(window=390, beta_shrink=0.0).estimate(make_data(close).view(t - 1))
    # The model's market is the average stock, so betas are relative to an average of 1.
    assert np.corrcoef(estimate.beta, true_beta)[0, 1] > 0.9
    assert np.mean(estimate.beta) == pytest.approx(1.0, abs=0.05)
    assert np.sqrt(np.median(estimate.specific_var)) == pytest.approx(0.02, rel=0.15)


def test_risk_model_gives_no_estimate_without_enough_history():
    close = 100 + np.random.default_rng(0).normal(0, 1, (50, 4)).cumsum(axis=0)
    estimate = SingleIndexRisk(window=252, min_obs=126).estimate(make_data(close).view(49))
    assert np.isnan(estimate.beta).all()


def test_auction_execution_sizes_caps_and_skips():
    ex = AuctionExecution(max_adv_fraction=0.01, min_trade=200.0)
    delta = ex.orders(
        target=np.array([0.05, 0.001, 0.0, 0.05, 0.05]), shares=np.array([0.0, 0.0, 7.0, 0.0, 0.0]),
        equity=100_000.0, ref_price=np.array([50.0, 50.0, 50.0, 50.0, np.nan]),
        adv=np.array([1e8, 1e8, 1e8, 100_000.0, 1e8]), tradable=np.ones(5, bool),
    )  # fmt: skip
    # full size; too small to bother; a full exit is never skipped; capped at 1% of volume; no price
    assert delta.tolist() == [100.0, 0.0, -7.0, 20.0, 0.0]
