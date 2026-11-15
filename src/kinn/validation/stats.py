"""Overfitting statistics: Deflated Sharpe, PBO, and resampling tests.

Sharpe ratios here are per period (not annualised) unless a function says otherwise.
References: Bailey & Lopez de Prado (2014), "The Deflated Sharpe Ratio"; Bailey, Borwein,
Lopez de Prado & Zhu (2017), "The Probability of Backtest Overfitting".
"""

from __future__ import annotations

import math
from itertools import combinations
from statistics import NormalDist

import numpy as np

_NORMAL = NormalDist()
_EULER = 0.5772156649015329


def sharpe(returns: np.ndarray) -> float:
    returns = np.asarray(returns, dtype=float)
    spread = returns.std(ddof=1)
    return float(returns.mean() / spread) if spread > 0 else 0.0


def probabilistic_sharpe(returns: np.ndarray, benchmark: float = 0.0) -> float:
    """P(true Sharpe > benchmark), allowing for sample length, skew and fat tails."""
    r = np.asarray(returns, dtype=float)
    n = len(r)
    if n < 3 or r.std(ddof=1) == 0:
        return float("nan")
    s = sharpe(r)
    z = (r - r.mean()) / r.std(ddof=0)
    skew, kurt = float((z**3).mean()), float((z**4).mean())
    denominator = math.sqrt(max(1 - skew * s + (kurt - 1) / 4 * s * s, 1e-12))
    return _NORMAL.cdf((s - benchmark) * math.sqrt(n - 1) / denominator)


def expected_max_sharpe(trials: int, trial_sharpe_variance: float) -> float:
    """The Sharpe the best of ``trials`` skill-less attempts is expected to show."""
    if trials <= 1:
        return 0.0
    return math.sqrt(trial_sharpe_variance) * (
        (1 - _EULER) * _NORMAL.inv_cdf(1 - 1 / trials)
        + _EULER * _NORMAL.inv_cdf(1 - 1 / (trials * math.e))
    )


def deflated_sharpe(returns: np.ndarray, *, trials: int, trial_sharpe_variance: float) -> float:
    """P(true Sharpe > 0) after charging for ``trials`` attempts. Above 0.95 is the usual bar."""
    return probabilistic_sharpe(returns, expected_max_sharpe(trials, trial_sharpe_variance))


def pbo(performance: np.ndarray, *, blocks: int = 10) -> dict:
    """Probability of backtest overfitting by combinatorially symmetric cross-validation.

    ``performance`` has one row per period and one column per trial (configuration). For every
    way of choosing half the blocks as in-sample, pick the best trial in-sample and see where
    it ranks out of sample. PBO is how often it lands in the bottom half.
    """
    matrix = np.asarray(performance, dtype=float)
    periods, trials = matrix.shape
    if trials < 2 or blocks % 2 or periods < blocks:
        raise ValueError("PBO needs at least 2 trials and an even number of blocks <= periods")
    pieces = np.array_split(np.arange(periods), blocks)
    logits = []
    for chosen in combinations(range(blocks), blocks // 2):
        inside = np.concatenate([pieces[k] for k in chosen])
        outside = np.concatenate([pieces[k] for k in range(blocks) if k not in chosen])
        best = int(np.argmax([sharpe(matrix[inside, j]) for j in range(trials)]))
        out_scores = np.array([sharpe(matrix[outside, j]) for j in range(trials)])
        rank = (out_scores < out_scores[best]).sum() + 1  # 1 = worst
        omega = rank / (trials + 1)
        logits.append(math.log(omega / (1 - omega)))
    logits = np.array(logits)
    return {"pbo": float((logits <= 0).mean()), "splits": len(logits),
            "median_logit": float(np.median(logits))}  # fmt: skip


def sign_flip_pvalue(values: np.ndarray, *, draws: int = 10_000, seed: int = 0) -> float:
    """One-sided p-value for mean > 0: how often random sign flips match the observed mean."""
    v = np.asarray(values, dtype=float)
    rng = np.random.default_rng(seed)
    observed = v.mean()
    signs = rng.choice((-1.0, 1.0), size=(draws, len(v)))
    return float(((signs * v).mean(axis=1) >= observed).sum() + 1) / (draws + 1)


def permutation_pvalue(
    treated: np.ndarray, pool: np.ndarray, *, draws: int = 10_000, seed: int = 0
) -> float:
    """One-sided p-value that ``treated`` has a higher mean than random same-size draws
    from ``pool`` (for example: event returns against returns at random times)."""
    treated, pool = np.asarray(treated, dtype=float), np.asarray(pool, dtype=float)
    rng = np.random.default_rng(seed)
    observed = treated.mean()
    hits = sum(
        rng.choice(pool, size=len(treated), replace=False).mean() >= observed for _ in range(draws)
    )
    return (hits + 1) / (draws + 1)


def bootstrap_mean_ci(
    values: np.ndarray, *, level: float = 0.95, draws: int = 5_000, seed: int = 0,
    groups: np.ndarray | None = None,
) -> tuple[float, float]:  # fmt: skip
    """Confidence interval for the mean. With ``groups`` (for example the session of each
    trade) whole groups are resampled, which respects same-day correlation."""
    v = np.asarray(values, dtype=float)
    rng = np.random.default_rng(seed)
    if groups is None:
        means = v[rng.integers(0, len(v), size=(draws, len(v)))].mean(axis=1)
    else:
        _, inverse = np.unique(np.asarray(groups), return_inverse=True)
        sums = np.bincount(inverse, weights=v)
        sizes = np.bincount(inverse)
        pick = rng.integers(0, len(sums), size=(draws, len(sums)))
        means = sums[pick].sum(axis=1) / sizes[pick].sum(axis=1)
    tail = (1 - level) / 2
    low, high = np.quantile(means, [tail, 1 - tail])
    return float(low), float(high)
