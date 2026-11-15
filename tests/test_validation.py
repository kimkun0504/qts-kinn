from datetime import date, timedelta

import numpy as np
import pytest

from kinn.validation import splits, stats

DAYS = [date(2020, 1, 1) + timedelta(days=i) for i in range(100)]


def test_walk_forward_never_tests_before_it_trains():
    folds = splits.walk_forward(DAYS, train=40, test=10)
    assert len(folds) == 6
    for train, test in folds:
        assert max(train) < min(test) and len(train) == 40 and len(test) == 10


def test_purged_kfold_removes_the_purge_and_the_embargo():
    folds = splits.purged_kfold(DAYS, folds=5, purge=2, embargo=3)
    assert sorted(d for _, test in folds for d in test) == DAYS
    train, test = folds[2]
    assert not set(train) & set(test)
    assert DAYS[38] not in train and DAYS[39] not in train and DAYS[37] in train
    assert DAYS[60] not in train and DAYS[62] not in train and DAYS[63] in train


def test_probabilistic_sharpe_matches_the_normal_case():
    rng = np.random.default_rng(0)
    r = rng.normal(0.1, 1.0, 5000)
    s = stats.sharpe(r)
    z = (r - r.mean()) / r.std()
    expected = stats._NORMAL.cdf(
        s * np.sqrt(len(r) - 1) / np.sqrt(1 - (z**3).mean() * s + ((z**4).mean() - 1) / 4 * s**2)
    )
    assert stats.probabilistic_sharpe(r) == pytest.approx(expected)
    assert stats.probabilistic_sharpe(r) > 0.999
    assert 0.2 < stats.probabilistic_sharpe(rng.normal(0, 1, 500)) < 0.999


def test_more_trials_deflate_the_same_result():
    r = np.random.default_rng(1).normal(0.08, 1.0, 1000)
    few = stats.deflated_sharpe(r, trials=2, trial_sharpe_variance=0.002)
    many = stats.deflated_sharpe(r, trials=2000, trial_sharpe_variance=0.002)
    assert few > many and stats.expected_max_sharpe(1, 0.002) == 0
    assert stats.expected_max_sharpe(2000, 0.002) > stats.expected_max_sharpe(10, 0.002) > 0


def test_pbo_is_high_for_noise_and_low_for_a_real_edge():
    rng = np.random.default_rng(2)
    noise = rng.normal(0, 1, (500, 20))
    assert 0.3 < stats.pbo(noise, blocks=8)["pbo"] < 0.8
    edge = noise.copy()
    edge[:, 3] += 0.5
    assert stats.pbo(edge, blocks=8)["pbo"] < 0.05


def test_resampling_tests():
    rng = np.random.default_rng(3)
    strong, none = rng.normal(0.3, 1, 400), rng.normal(0, 1, 400)
    assert stats.sign_flip_pvalue(strong, draws=2000) < 0.01
    assert stats.sign_flip_pvalue(none, draws=2000) > 0.05
    pool = rng.normal(0, 1, 5000)
    assert stats.permutation_pvalue(strong, pool, draws=500) < 0.01
    low, high = stats.bootstrap_mean_ci(strong, draws=1000)
    assert low < strong.mean() < high and low > 0
    groups = np.repeat(np.arange(40), 10)
    wide = stats.bootstrap_mean_ci(np.repeat(rng.normal(0.3, 1, 40), 10), groups=groups, draws=1000)
    narrow = stats.bootstrap_mean_ci(np.repeat(rng.normal(0.3, 1, 40), 10), draws=1000)
    assert wide[1] - wide[0] > narrow[1] - narrow[0]  # clustering widens the interval
