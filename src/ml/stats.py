"""Statistical inference written in numpy (no scipy) — ADR-002 §3.6.8, §3.7; draft §5.6–5.7.

* unit of analysis: the presentation (mean over the three origins, after averaging seeds);
* 95 % CI: cluster bootstrap over presentations (10,000 resamples, fixed seed);
* p-value: exact sign-flip permutation test (2^n sign vectors; Monte-Carlo above ``exact_max_n``);
* Holm step-down correction over the family of main comparisons;
* D-15 verdict with δ = 0.02 NDCG@10.
"""
from __future__ import annotations

import itertools

import numpy as np

DELTA = 0.02
ALPHA = 0.05


def cluster_bootstrap_ci(diffs, n_boot: int = 10_000, seed: int = 0, alpha: float = ALPHA):
    """Percentile CI of the mean of per-presentation differences, resampling presentations."""
    d = np.asarray(diffs, dtype=float)
    n = len(d)
    if n == 0:
        return float("nan"), float("nan"), float("nan")
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, n, size=(n_boot, n))
    means = d[idx].mean(axis=1)
    lo, hi = np.quantile(means, [alpha / 2, 1 - alpha / 2])
    return float(d.mean()), float(lo), float(hi)


def sign_flip_test(diffs, exact_max_n: int = 20, n_mc: int = 200_000, seed: int = 0) -> float:
    """Two-sided p = P(|mean(s·Δ)| ≥ |mean(Δ)|) under random sign flips.

    Exact enumeration of all 2^n sign vectors for n ≤ exact_max_n (n = 13 ⇒ 8,192), otherwise
    Monte-Carlo with the observed vector counted (p = (b+1)/(B+1)).
    """
    d = np.asarray(diffs, dtype=float)
    n = len(d)
    if n == 0:
        return float("nan")
    obs = abs(d.mean())
    tol = 1e-12 * max(1.0, obs)
    if n <= exact_max_n:
        signs = np.array(list(itertools.product((1.0, -1.0), repeat=n)))
        stats = np.abs(signs @ d) / n
        return float((stats >= obs - tol).mean())
    rng = np.random.default_rng(seed)
    signs = rng.choice((-1.0, 1.0), size=(n_mc, n))
    stats = np.abs(signs @ d) / n
    return float(((stats >= obs - tol).sum() + 1) / (n_mc + 1))


def holm(pvals) -> np.ndarray:
    """Holm-adjusted p-values: p̃_(i) = max_{j ≤ i} min(1, (m − j + 1) p_(j))."""
    p = np.asarray(pvals, dtype=float)
    m = len(p)
    order = np.argsort(p, kind="stable")
    adj_sorted = np.minimum(1.0, (m - np.arange(m)) * p[order])
    adj_sorted = np.maximum.accumulate(adj_sorted)
    out = np.empty(m)
    out[order] = adj_sorted
    return out


def verdict(mean: float, lo: float, hi: float, p_holm: float, delta: float = DELTA,
            alpha: float = ALPHA) -> str:
    """D-15 decision rule (one-sided superiority hypotheses H1, H2-a, H4-b)."""
    if mean >= delta and lo > 0 and p_holm < alpha:
        return "confirmed"
    if hi < 0:
        return "refuted_reverse"
    if hi < delta:
        return "refuted"
    return "inconclusive"


def verdict_bidirectional(mean: float, lo: float, hi: float, p_holm: float, delta: float = DELTA,
                          alpha: float = ALPHA) -> str:
    """RQ3 (GRU-lite vs best non-neural sequential): superior / equivalent / inferior / inconclusive."""
    if mean >= delta and lo > 0 and p_holm < alpha:
        return "superior"
    if lo > -delta and hi < delta:
        return "equivalent"
    if mean <= -delta and hi < 0 and p_holm < alpha:
        return "inferior"
    return "inconclusive"


def compare(diffs, n_boot: int = 10_000, seed: int = 0) -> dict:
    """Mean, cluster-bootstrap CI and sign-flip p for a vector of per-presentation differences."""
    mean, lo, hi = cluster_bootstrap_ci(diffs, n_boot=n_boot, seed=seed)
    return {"n": len(diffs), "mean": mean, "ci_lo": lo, "ci_hi": hi, "p": sign_flip_test(diffs)}
