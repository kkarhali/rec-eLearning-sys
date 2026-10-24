"""Statistical inference written in numpy (no scipy) — ADR-002 §3.6.8, §3.7; draft §5.6–5.7.

* unit of analysis: the presentation (mean over the three origins, after averaging seeds);
* 95 % CI for the verdict: calibrated cluster **bootstrap-t** over presentations (ADR-004 §2.2, D-25;
  B = 10,000, fixed seed); the percentile interval is kept for the appendix only;
* p-value: two-sided exact sign-flip test (2^n sign vectors; Monte-Carlo above ``exact_max_n``) (D-24);
  descriptive one-sided margin test on Δ − δ;
* Holm step-down correction over the fixed family {H1, H2-a, H3, H4-a}, m = 4 (D-23);
* precedence verdict tables of ADR-004 §2.2 (one-sided, and six-level for H3) with δ = 0.02.
"""
from __future__ import annotations

import itertools

import numpy as np

DELTA = 0.02
ALPHA = 0.05


def cluster_bootstrap_t_ci(diffs, n_boot: int = 10_000, seed: int = 0, alpha: float = ALPHA):
    """Calibrated cluster bootstrap-t CI (ADR-004 §2.2):

        t*_b = (m_b − Δ̄) / (max(s_b, 1e−12)/√n),
        CI = [Δ̄ − q*_{1−α/2}·s/√n, Δ̄ − q*_{α/2}·s/√n]
    """
    d = np.asarray(diffs, dtype=float)
    n = len(d)
    if n < 2:
        return float(d.mean()) if n else float("nan"), float("nan"), float("nan")
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, n, size=(n_boot, n))
    samp = d[idx]
    m_b = samp.mean(axis=1)
    s_b = samp.std(axis=1, ddof=1)
    mean = d.mean()
    se = d.std(ddof=1) / np.sqrt(n)
    t_star = (m_b - mean) / (np.maximum(s_b, 1e-12) / np.sqrt(n))
    q_lo, q_hi = np.quantile(t_star, [alpha / 2, 1 - alpha / 2])
    return float(mean), float(mean - q_hi * se), float(mean - q_lo * se)


def cluster_bootstrap_ci(diffs, n_boot: int = 10_000, seed: int = 0, alpha: float = ALPHA):
    """Percentile CI of the mean of per-presentation differences (appendix only since ADR-004)."""
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


def margin_test(diffs, delta: float = DELTA) -> float:
    """Descriptive one-sided sign-flip p for H0: mean(Δ − δ) ≤ 0 (ADR-004 §2.1; does not change the verdict)."""
    d = np.asarray(diffs, dtype=float) - delta
    n = len(d)
    obs = d.mean()
    tol = 1e-12 * max(1.0, abs(obs))
    signs = np.array(list(itertools.product((1.0, -1.0), repeat=n))) if n <= 20 else \
        np.random.default_rng(0).choice((-1.0, 1.0), size=(200_000, n))
    return float(((signs @ d) / n >= obs - tol).mean())


def verdict(mean: float, lo: float, hi: float, p_holm: float, delta: float = DELTA,
            alpha: float = ALPHA) -> str:
    """One-sided precedence table (H1, H2-a, H4-a; ADR-004 §2.2): first matching row wins."""
    if mean >= delta and lo > 0 and p_holm < alpha:
        return "confirmed"
    if hi < 0:
        return "refuted_reverse"
    if hi < delta:
        return "refuted"
    return "inconclusive"


def verdict_bidirectional(mean: float, lo: float, hi: float, p_holm: float, delta: float = DELTA,
                          alpha: float = ALPHA) -> str:
    """H3 six-level precedence table (ADR-004 §2.2, D-26)."""
    if mean >= delta and lo > 0 and p_holm < alpha:
        return "superior_confirmed"
    if mean <= -delta and hi < 0 and p_holm < alpha:
        return "inferior_confirmed"
    if lo > -delta and hi < delta:
        return "equivalent"
    if hi < 0:
        return "inferior"
    if hi < delta:
        return "refuted"
    return "inconclusive"


def confirmed_with_margin(lo: float, delta: float = DELTA) -> bool:
    """Descriptive tag: lower CI bound above δ (ADR-004 §2.1)."""
    return lo > delta


def compare(diffs, n_boot: int = 10_000, seed: int = 0) -> dict:
    """Mean, bootstrap-t CI (verdict), percentile CI (appendix) and two-sided sign-flip p."""
    mean, lo, hi = cluster_bootstrap_t_ci(diffs, n_boot=n_boot, seed=seed)
    _, plo, phi = cluster_bootstrap_ci(diffs, n_boot=n_boot, seed=seed)
    return {"n": len(diffs), "mean": mean, "ci_lo": lo, "ci_hi": hi, "pct_lo": plo, "pct_hi": phi,
            "p": sign_flip_test(diffs)}


def confirmation_power(mu: float, sigma: float, n: int = 13, delta: float = DELTA, n_sim: int = 1000,
                       n_boot: int = 2000, holm_factor: float = 4.0, alpha: float = ALPHA,
                       seed: int = 0) -> float:
    """P(verdict = 'confirmed') when the per-presentation differences are N(mu, sigma²), n units.

    Applies the full one-sided rule of ADR-004 §2.2: Δ̄ ≥ δ, bootstrap-t lower bound > 0 and
    holm_factor · p < α (holm_factor = m = 4 is the conservative bound for the smallest p in the family).
    """
    rng = np.random.default_rng(seed)
    D = rng.normal(mu, sigma, size=(n_sim, n))
    signs = np.array(list(itertools.product((1.0, -1.0), repeat=n))) if n <= 16 else \
        rng.choice((-1.0, 1.0), size=(20_000, n))
    hits = 0
    idx = rng.integers(0, n, size=(n_boot, n))
    for d in D:
        mean = d.mean()
        if mean < delta:
            continue
        samp = d[idx]
        m_b, s_b = samp.mean(axis=1), samp.std(axis=1, ddof=1)
        se = d.std(ddof=1) / np.sqrt(n)
        t_star = (m_b - mean) / (np.maximum(s_b, 1e-12) / np.sqrt(n))
        lo = mean - np.quantile(t_star, 1 - alpha / 2) * se
        if lo <= 0:
            continue
        p = float((np.abs(signs @ d) / n >= abs(mean) - 1e-12).mean())
        hits += holm_factor * p < alpha
    return hits / n_sim


def mde80(sigma: float, n: int = 13, delta: float = DELTA, power: float = 0.8, grid=None, **kw) -> float:
    """Smallest true mean difference with confirmation power ≥ ``power`` (ADR-004 §2.2, written before freeze)."""
    grid = np.arange(delta, delta + 6 * sigma + 0.05, 0.0025) if grid is None else grid
    for mu in grid:
        if confirmation_power(float(mu), sigma, n=n, delta=delta, **kw) >= power:
            return float(mu)
    return float("nan")
