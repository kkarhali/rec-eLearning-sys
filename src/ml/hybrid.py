"""Behaviour- and context-aware hybrid: linear rank fusion of ≤ 4 components (D-11, ADR-002 §3.3).

    r̃_m(u,i) = 1 − (rank_m(u,i) − 1) / (|C_u| − 1)       (rank inside the learner's candidates)
    score(u,i) = Σ_m w_m r̃_m(u,i),   Σ w_m = 1, w_m ≥ 0, grid step 0.1 on the simplex

Weights are tuned on the validation window only. A component enters the combination only
through the acceptance rule (development presentations 2013 only):
  * the cluster-bootstrap 95 % CI (over presentations) of the validation NDCG@10 lift
    (task A) excludes zero, and
  * for stochastic components, the lift exceeds the SD across seeds.
Greedy forward search (draft §4.4.3): start from the best single component, add the accepted
component with the largest lift, stop when nothing is accepted or 4 components are reached.
"""
from __future__ import annotations

import itertools
from dataclasses import dataclass, field

import numpy as np

from .metrics import candidate_ranks, evaluate, summarize
from .stats import cluster_bootstrap_ci

MAX_COMPONENTS = 4


def rank_normalize(scores: np.ndarray, cand: np.ndarray, tiebreak: np.ndarray) -> np.ndarray:
    """r̃ in [0,1] inside each learner's candidate list (1 = top); 0 for non-candidates."""
    ranks = candidate_ranks(scores, cand, tiebreak).astype(np.float64)
    n = cand.sum(axis=1, keepdims=True).astype(np.float64)
    denom = np.maximum(n - 1.0, 1.0)
    r = 1.0 - (ranks - 1.0) / denom
    r = np.where(n > 1, r, 1.0)
    return np.where(cand, r, 0.0)


def simplex_grid(m: int, step: float = 0.1) -> np.ndarray:
    """All weight vectors on the simplex with the given step: C(1/step + m − 1, m − 1) points."""
    n = int(round(1.0 / step))
    pts = [c for c in itertools.product(range(n + 1), repeat=m) if sum(c) == n]
    return np.array(pts, dtype=np.float64) / n


def fuse(rtilde: list[np.ndarray], weights) -> np.ndarray:
    out = np.zeros_like(rtilde[0])
    for w, r in zip(weights, rtilde):
        if w:
            out += w * r
    return out


def tune_weights(rtilde: list[np.ndarray], cand, tgt, unreach, evaluated, tiebreak,
                 step: float = 0.1, metric: str = "NDCG@10"):
    """Grid search on the simplex; returns (best weights, best value, all values)."""
    grid = simplex_grid(len(rtilde), step)
    vals = np.empty(len(grid))
    for g, w in enumerate(grid):
        res = evaluate(fuse(rtilde, w), cand, tgt, unreach, evaluated, tiebreak, ks=(10,))
        vals[g] = summarize(res).get(metric, np.nan) if res["n_eval"] else np.nan
    best = int(np.nanargmax(vals))
    return grid[best], float(vals[best]), vals


@dataclass
class AcceptanceDecision:
    component: str
    mean_lift: float
    ci: tuple[float, float]
    seed_sd: float | None
    accepted: bool


def accept_component(name: str, lifts_per_presentation, seed_sd: float | None = None,
                     n_boot: int = 10_000, seed: int = 0) -> AcceptanceDecision:
    """ADR-002 §3.3 acceptance rule for one candidate component."""
    lifts = np.asarray(lifts_per_presentation, dtype=float)
    mean, lo, hi = cluster_bootstrap_ci(lifts, n_boot=n_boot, seed=seed)
    ok = lo > 0
    if seed_sd is not None:
        ok = ok and mean > seed_sd
    return AcceptanceDecision(name, mean, (lo, hi), seed_sd, bool(ok))


@dataclass
class ForwardResult:
    combination: list[str]
    history: list[list[AcceptanceDecision]] = field(default_factory=list)


def greedy_forward(components: list[str], evaluate_combo, stochastic: set[str] = frozenset(),
                   max_components: int = MAX_COMPONENTS, n_boot: int = 10_000, seed: int = 0) -> ForwardResult:
    """Greedy forward selection under the acceptance rule.

    ``evaluate_combo(tuple_of_names)`` must return (per_presentation_values, seed_sd) where the
    values are validation NDCG@10 (task A) per development presentation (mean over origins),
    with weights tuned on validation for every (presentation, origin), and seed_sd the SD across
    seeds of the presentation-mean (None if deterministic).
    """
    singles = {c: np.asarray(evaluate_combo((c,))[0], dtype=float) for c in components}
    base = max(components, key=lambda c: singles[c].mean())
    combo = [base]
    base_vals = singles[base]
    result = ForwardResult(combination=combo)
    while len(combo) < max_components:
        decisions = []
        for m in components:
            if m in combo:
                continue
            vals, sd = evaluate_combo(tuple(combo + [m]))
            lifts = np.asarray(vals, dtype=float) - base_vals
            decisions.append((accept_component(m, lifts, sd if m in stochastic else None,
                                               n_boot=n_boot, seed=seed), np.asarray(vals, dtype=float)))
        result.history.append([d for d, _ in decisions])
        accepted = [(d, v) for d, v in decisions if d.accepted]
        if not accepted:
            break
        best, vals = max(accepted, key=lambda dv: dv[0].mean_lift)
        combo.append(best.component)
        base_vals = vals
    result.combination = combo
    return result
