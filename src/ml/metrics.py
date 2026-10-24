"""Ranking metrics on the full catalogue (draft §5.4, ADR-002 §3.6.6).

For learner u with top-K list L_u = (l_1..l_K), targets T_u and rel_k = 1[l_k ∈ T_u]:

    P@K    = Σ rel_k / K
    R@K    = Σ rel_k / |T_u|
    HR@K   = 1[Σ rel_k > 0]
    NDCG@K = Σ rel_k / log2(k+1)  /  Σ_{k ≤ min(K,|T_u|)} 1/log2(k+1)
    RR@K   = 1 / min{k : rel_k = 1}   (0 if none);  MRR@K = mean RR@K
    Coverage@K = |∪_u L_u| / |C(t)|
    PopBias@K  = mean popularity percentile (0 = least, 1 = most popular in training) of L_u

|T_u| includes targets outside the catalogue (unreachable ⇒ always a miss). No sampled
negatives: every candidate is ranked. Ties are broken by the fixed keys of
:func:`splits.tiebreak_keys`.
"""
from __future__ import annotations

import numpy as np

DEFAULT_KS = (5, 10, 20)


# --- reference (list-based) implementation used by the unit tests ------------------------------
def list_metrics(ranked, targets, k: int, n_targets: int | None = None) -> dict[str, float]:
    """Metrics of one ranked list against a target set. ``n_targets`` overrides |T_u|."""
    targets = set(targets)
    nt = len(targets) if n_targets is None else n_targets
    top = list(ranked)[:k]
    rel = [1 if x in targets else 0 for x in top]
    hits = sum(rel)
    dcg = sum(r / np.log2(j + 2) for j, r in enumerate(rel))
    idcg = sum(1.0 / np.log2(j + 2) for j in range(min(k, nt)))
    first = next((j + 1 for j, r in enumerate(rel) if r), None)
    return {
        "P": hits / k,
        "R": hits / nt if nt else 0.0,
        "HR": float(hits > 0),
        "NDCG": dcg / idcg if idcg > 0 else 0.0,
        "RR": 1.0 / first if first else 0.0,
    }


def coverage(lists, catalogue_size: int) -> float:
    items = set()
    for l in lists:
        items.update(l)
    return len(items) / catalogue_size


# --- vectorised implementation used by the harness ------------------------------------------------
def rank_order(scores: np.ndarray, cand: np.ndarray, tiebreak: np.ndarray) -> np.ndarray:
    """Full ranking per row: candidates by descending score, ties by tiebreak key, then non-candidates."""
    if np.isnan(scores[cand]).any():
        raise ValueError("NaN score on a candidate")
    s = np.where(cand, scores, -np.inf)
    # np.lexsort: last key is primary
    return np.lexsort((tiebreak, -s, ~cand), axis=-1)


def candidate_ranks(scores: np.ndarray, cand: np.ndarray, tiebreak: np.ndarray) -> np.ndarray:
    """1-based rank of every item within the learner's candidate list (non-candidates get I+1)."""
    order = rank_order(scores, cand, tiebreak)
    U, I = scores.shape
    ranks = np.empty((U, I), dtype=np.int64)
    rows = np.arange(U)[:, None]
    ranks[rows, order] = np.arange(1, I + 1)[None, :]
    ranks[~cand] = I + 1
    return ranks


def popularity_percentile(pop: np.ndarray) -> np.ndarray:
    """Average-rank percentile in [0,1] (0 = least popular, 1 = most popular)."""
    pop = np.asarray(pop, dtype=float)
    n = len(pop)
    if n == 1:
        return np.ones(1)
    order = np.argsort(pop, kind="stable")
    ranks = np.empty(n)
    ranks[order] = np.arange(n, dtype=float)
    # average ranks over ties
    uniq, inv = np.unique(pop, return_inverse=True)
    sums = np.bincount(inv, weights=ranks)
    cnts = np.bincount(inv)
    return (sums / cnts)[inv] / (n - 1)


def evaluate(scores: np.ndarray, cand: np.ndarray, tgt: np.ndarray, unreach: np.ndarray,
             evaluated: np.ndarray, tiebreak: np.ndarray, ks=DEFAULT_KS,
             pop: np.ndarray | None = None, return_topk: bool = False) -> dict:
    """Per-learner metrics for the evaluated learners.

    Returns {"per_user": {metric@K: array over evaluated learners}, "coverage": {K: float},
    "popbias": {K: float}, "n_eval": int}.
    """
    idx = np.flatnonzero(evaluated)
    out: dict = {"n_eval": int(len(idx)), "per_user": {}, "coverage": {}, "popbias": {}}
    U, I = scores.shape
    if len(idx) == 0:
        return out
    sc, cd, tg, tb = scores[idx], cand[idx], tgt[idx], tiebreak[idx]
    kmax = min(max(ks), I)
    order = rank_order(sc, cd, tb)[:, :kmax]
    rows = np.arange(len(idx))[:, None]
    valid = cd[rows, order]
    rel = tg[rows, order] & valid
    nt = tg.sum(axis=1) + unreach[idx]
    disc = 1.0 / np.log2(np.arange(2, kmax + 2))
    cum_disc = np.concatenate([[0.0], np.cumsum(1.0 / np.log2(np.arange(2, I + 2)))])
    pct = popularity_percentile(pop) if pop is not None else None
    for K in ks:
        k = min(K, kmax)
        r = rel[:, :k]
        hits = r.sum(axis=1)
        dcg = (r * disc[:k]).sum(axis=1)
        idcg = cum_disc[np.minimum(K, nt)]
        first = np.where(r.any(axis=1), r.argmax(axis=1) + 1, 0)
        pu = out["per_user"]
        pu[f"P@{K}"] = hits / K
        pu[f"R@{K}"] = np.where(nt > 0, hits / np.maximum(nt, 1), 0.0)
        pu[f"HR@{K}"] = (hits > 0).astype(float)
        pu[f"NDCG@{K}"] = np.where(idcg > 0, dcg / np.where(idcg > 0, idcg, 1), 0.0)
        pu[f"MRR@{K}"] = np.where(first > 0, 1.0 / np.maximum(first, 1), 0.0)
        rec_items = order[:, :k][valid[:, :k]]
        out["coverage"][K] = len(np.unique(rec_items)) / I
        if pct is not None:
            out["popbias"][K] = float(pct[rec_items].mean()) if rec_items.size else float("nan")
    if return_topk:
        out["topk"] = order
        out["topk_valid"] = valid
        out["eval_idx"] = idx
    return out


def summarize(res: dict, mask: np.ndarray | None = None) -> dict[str, float]:
    """Mean of per-learner metrics (optionally over a sub-slice of the evaluated learners)."""
    row = {}
    for name, arr in res["per_user"].items():
        a = arr if mask is None else arr[mask]
        row[name] = float(a.mean()) if a.size else float("nan")
    return row
