"""Behaviour- and context-aware hybrid: linear rank fusion of ≤ 4 components
(D-11, ADR-002 §3.3 as amended by ADR-004 §2.4: D-29, D-30, D-32).

    r̃_m(u,i) = 1 − (rank_m(u,i) − 1) / (|C_u| − 1)   rank inside the learner's candidates,
                                                      **mid-rank on ties** (D-32); r̃ = 1 if |C_u| = 1
    score(u,i) = Σ_m w_m r̃_m(u,i),   Σ w_m = 1, w_m ≥ 0

Weight grid inside the 20-setting budget (D-29): simplex step 1/4 for 2–3 components (5, 15 points),
1/3 for 4 components (20 points); step 0.1 only as a development sensitivity analysis.
The final ordering of the fused score uses the fixed keys of ``splits.tiebreak_keys``.

Acceptance rule (development presentations 2013 only, D-30): weights are tuned on the validation
window, but the lift is measured on the 2013 **test** windows (t, t+14]; a component enters if the
cluster bootstrap-t 95 % CI over the nine presentations of the NDCG@10 lift (task A) excludes zero
and, for stochastic components, the lift exceeds the SD across seeds. Greedy forward search from
the best single component, ≤ 4 components. Personalisation floor: if the accepted combination
holds no personal component {(2) WRMF, (3) Item-kNN, (4) sequential, (5) CBF}, the personal
component with the largest estimated lift is added and flagged ``floor``.
"""
from __future__ import annotations

import itertools
from dataclasses import dataclass, field

import numpy as np

from .metrics import evaluate, summarize
from .stats import cluster_bootstrap_t_ci

MAX_COMPONENTS = 4


def mid_ranks(scores: np.ndarray, cand: np.ndarray) -> np.ndarray:
    """1-based rank within the candidates, ties get the average (mid) rank (D-32)."""
    U, I = scores.shape
    s = np.where(cand, scores, -np.inf)
    order = np.argsort(-s, axis=1, kind="stable")
    ss = np.take_along_axis(s, order, axis=1)
    pos = np.arange(1, I + 1, dtype=np.float64)[None, :].repeat(U, axis=0)
    # group equal consecutive values per row and average their positions
    new_group = np.ones((U, I), dtype=bool)
    new_group[:, 1:] = ss[:, 1:] != ss[:, :-1]
    gid = np.cumsum(new_group, axis=1) - 1 + (np.arange(U) * I)[:, None]
    flat = gid.ravel()
    sums = np.bincount(flat, weights=pos.ravel(), minlength=U * I)
    cnts = np.bincount(flat, minlength=U * I)
    avg = (sums / np.maximum(cnts, 1))[flat].reshape(U, I)
    ranks = np.empty((U, I))
    np.put_along_axis(ranks, order, avg, axis=1)
    return ranks


def rank_normalize(scores: np.ndarray, cand: np.ndarray, tiebreak: np.ndarray | None = None) -> np.ndarray:
    """r̃ in [0,1] inside each learner's candidate list (1 = top, mid-rank on ties); 0 off-candidates.

    ``tiebreak`` is accepted for backward compatibility and ignored (D-32: ties are not broken here).
    """
    ranks = mid_ranks(scores, cand)
    n = cand.sum(axis=1, keepdims=True).astype(np.float64)
    r = 1.0 - (ranks - 1.0) / np.maximum(n - 1.0, 1.0)
    r = np.where(n > 1, r, 1.0)
    return np.where(cand, r, 0.0)


def simplex_grid(m: int, step: float | None = None) -> np.ndarray:
    """Weight vectors on the simplex. Default step (D-29): 1/4 for m ≤ 3, 1/3 for m = 4."""
    if step is None:
        step = 1.0 if m == 1 else (1 / 4 if m <= 3 else 1 / 3)
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
                 step: float | None = None, metric: str = "NDCG@10"):
    """Grid search on the simplex (validation window); returns (best weights, best value, all values).

    ``step=None`` uses the budgeted grid of D-29 (≤ 20 points); ``step=0.1`` is the sensitivity grid.
    """
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
    """Acceptance rule for one candidate component (ADR-002 §3.3, ADR-004 §2.4).

    ``lifts_per_presentation``: NDCG@10 lift (task A) on the 2013 **test** windows, one value per
    development presentation (mean over origins), with weights tuned on validation.
    """
    lifts = np.asarray(lifts_per_presentation, dtype=float)
    mean, lo, hi = cluster_bootstrap_t_ci(lifts, n_boot=n_boot, seed=seed)
    ok = lo > 0
    if seed_sd is not None:
        ok = ok and mean > seed_sd
    return AcceptanceDecision(name, mean, (lo, hi), seed_sd, bool(ok))


@dataclass
class ForwardResult:
    combination: list[str]
    history: list[list[AcceptanceDecision]] = field(default_factory=list)
    floor_component: str | None = None      # added by the personalisation floor (D-30)


def greedy_forward(components: list[str], evaluate_combo, stochastic: set[str] = frozenset(),
                   max_components: int = MAX_COMPONENTS, n_boot: int = 10_000, seed: int = 0,
                   personal: set[str] = frozenset()) -> ForwardResult:
    """Greedy forward selection under the acceptance rule, with the personalisation floor.

    ``evaluate_combo(tuple_of_names)`` must return (per_presentation_values, seed_sd) where the
    values are NDCG@10 (task A) on the 2013 **test** windows per development presentation (mean
    over origins), with weights tuned on validation for every (presentation, origin) (D-30), and
    seed_sd the SD across seeds of the presentation-mean (None if deterministic).
    ``personal``: names of personal components; if the accepted combination contains none of them,
    the one with the largest estimated lift over the final combination is added (flagged).
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
    if personal and not (set(combo) & set(personal)) and len(combo) < max_components:
        lifts = {}
        for m in [c for c in components if c in personal]:      # deterministic order (not set order)
            if m not in combo:
                vals, _ = evaluate_combo(tuple(combo + [m]))
                lifts[m] = float(np.mean(np.asarray(vals, dtype=float) - base_vals))
        if lifts:
            m = max(lifts, key=lifts.get)
            combo.append(m)
            result.floor_component = m
    result.combination = combo
    return result
