"""Day-basket helpers shared by the sequential baselines (D-06: unordered day baskets)."""
from __future__ import annotations

import numpy as np


def day_keys(train) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Unique active (u, d) pairs of catalogue events, sorted by u then d; plus event → basket id."""
    key = train.ev_u.astype(np.int64) * 100_000 + (train.ev_d.astype(np.int64) + 50_000)
    uniq, inv = np.unique(key, return_inverse=True)
    bu = (uniq // 100_000).astype(np.int64)
    bd = (uniq % 100_000 - 50_000).astype(np.int64)
    return bu, bd, inv


def recency_rank(bu: np.ndarray) -> np.ndarray:
    """For baskets sorted by (u, d ascending): 0 for the most recent basket of each user, 1 next …"""
    n = len(bu)
    if n == 0:
        return np.zeros(0, dtype=np.int64)
    last_of_user = np.r_[bu[1:] != bu[:-1], True]
    # position from the end within each user block
    idx = np.arange(n)
    ends = np.flatnonzero(last_of_user)
    block_end = ends[np.searchsorted(ends, idx)]
    return block_end - idx


def last_days_query(train, L: int, weighting: str = "binary") -> np.ndarray:
    """U×I query of the last L active days.

    weighting = "binary": q_i = 1 if i in any of the last L baskets (SKNN);
    weighting = "linear": q_i = Σ_baskets (L − r)/L with r = 0 for the latest basket (V-SKNN).
    """
    bu, bd, inv = day_keys(train)
    r = recency_rank(bu)
    keep_b = r < L
    ev_keep = keep_b[inv]
    Q = np.zeros((train.n_users, train.n_items), dtype=np.float64)
    if weighting == "binary":
        Q[train.ev_u[ev_keep], train.ev_i[ev_keep]] = 1.0
    elif weighting == "linear":
        w = (L - r[inv[ev_keep]]) / L
        np.add.at(Q, (train.ev_u[ev_keep], train.ev_i[ev_keep]), w)
    else:
        raise ValueError(weighting)
    return Q


def week_baskets(train) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """(registration, week) baskets: binary matrix nB×I (float32), owner u, week."""
    wk = np.floor_divide(train.ev_d, 7).astype(np.int64)
    key = train.ev_u.astype(np.int64) * 10_000 + (wk + 1_000)
    uniq, inv = np.unique(key, return_inverse=True)
    B = np.zeros((len(uniq), train.n_items), dtype=np.float32)
    B[inv, train.ev_i] = 1.0
    return B, (uniq // 10_000).astype(np.int64), (uniq % 10_000 - 1_000).astype(np.int64)


def consecutive_day_transitions(train) -> np.ndarray:
    """N_aj = Σ_u Σ_l 1[a ∈ S_{u,d_l}] 1[j ∈ S_{u,d_{l+1}}] over consecutive active days."""
    bu, bd, inv = day_keys(train)
    I = train.n_items
    nb = len(bu)
    if nb < 2:
        return np.zeros((I, I))
    # basket b and b+1 are consecutive for the same user iff bu[b] == bu[b+1]
    has_next = np.r_[bu[1:] == bu[:-1], False]
    # items per basket as a binary matrix in sparse (row, col) form
    rows = inv
    cols = train.ev_i.astype(np.int64)
    order = np.argsort(rows, kind="stable")
    rows, cols = rows[order], cols[order]
    starts = np.searchsorted(rows, np.arange(nb + 1))
    N = np.zeros(I * I, dtype=np.float64)
    src_b = np.flatnonzero(has_next)
    # expand pairs (a in basket b) × (j in basket b+1)
    len_a = starts[src_b + 1] - starts[src_b]
    len_j = starts[src_b + 2] - starts[src_b + 1]
    tot = len_a * len_j
    if tot.sum() == 0:
        return N.reshape(I, I)
    pair_b = np.repeat(np.arange(len(src_b)), tot)
    off = np.arange(tot.sum()) - np.repeat(np.cumsum(tot) - tot, tot)
    la = len_a[pair_b]
    lj = len_j[pair_b]
    a_pos = starts[src_b[pair_b]] + off // lj
    j_pos = starts[src_b[pair_b] + 1] + off % lj
    del la
    N += np.bincount(cols[a_pos] * I + cols[j_pos], minlength=I * I)
    return N.reshape(I, I)
