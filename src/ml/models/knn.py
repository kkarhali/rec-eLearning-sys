"""B4 Item-kNN and B5 SKNN / V-SKNN (draft §4.2.4–4.2.5, ADR-002 §3.4)."""
from __future__ import annotations

import numpy as np

from ..signals import SignalSpec, all_signal_specs, signal_matrix
from .base import Recommender, grid
from .baskets import last_days_query, week_baskets


def item_similarity(R: np.ndarray, shrink: float) -> np.ndarray:
    """sim(i,j) = n_ij/(n_ij+λ) · cos(r_i, r_j) on binary columns, zero diagonal."""
    Rb = (R > 0).astype(np.float64)
    n = Rb.T @ Rb                              # co-occurrence counts n_ij
    norms = np.sqrt(np.diag(n))
    denom = np.outer(norms, norms)
    cos = np.divide(n, denom, out=np.zeros_like(n), where=denom > 0)
    sim = cos * (n / (n + shrink)) if shrink > 0 else cos
    np.fill_diagonal(sim, 0.0)
    return sim


def keep_top_k_per_column(sim: np.ndarray, k: int | None) -> np.ndarray:
    """Keep, for every target item j (column), only its k most similar items N_k(j)."""
    I = sim.shape[0]
    if k is None or k >= I - 1:
        return sim
    out = np.zeros_like(sim)
    idx = np.argpartition(-sim, k - 1, axis=0)[:k]          # k×I row indices per column
    cols = np.broadcast_to(np.arange(I), idx.shape)
    out[idx, cols] = sim[idx, cols]
    return out


class ItemKNN(Recommender):
    """B4: s(u,j) = Σ_{i ∈ N_k(j) ∩ I_u} sim(i,j) · W_ui; similarity on binary columns with shrinkage."""

    name = "B4_ItemKNN"

    def _fit(self, train):
        p = self.params
        S = item_similarity(train.seen, float(p.get("shrink", 0.0)))
        self.sim = keep_top_k_per_column(S, p.get("k"))

    def _score(self):
        W = signal_matrix(self.train, self.params.get("signal", SignalSpec("L0")))
        return W @ self.sim

    @classmethod
    def param_space(cls):
        return grid(k=[20, 50, 100, None], shrink=[0.0, 10.0, 50.0, 100.0], signal=all_signal_specs())


class SKNN(Recommender):
    """B5: session(basket)-kNN on (registration, week) baskets.

    query q = last L active day baskets of u (binary for SKNN, linear decay for V-SKNN);
    sim(q, n) = Σ_{i∈n} q_i / (‖q‖ √|n|);  s(j) = Σ_{n ∈ N_k(q)} sim(q,n) 1[j ∈ n].
    Neighbours are baskets of *other* learners, optionally restricted to the M most recent.
    """

    name = "B5_SKNN"
    chunk = 128

    def _fit(self, train):
        p = self.params
        B, owner, week = week_baskets(train)
        M = p.get("M")
        if M is not None and M < len(owner):
            order = np.lexsort((owner, -week))[:M]           # most recent weeks first
            order = np.sort(order)
            B, owner, week = B[order], owner[order], week[order]
        self.B, self.owner = B, owner
        self.bnorm = np.sqrt(B.sum(axis=1))

    def _score(self):
        p, tr = self.params, self.train
        L = int(p.get("L", 1))
        variant = p.get("variant", "sknn")
        k = int(p.get("k", 100))
        Q = last_days_query(tr, L, "binary" if variant == "sknn" else "linear").astype(np.float32)
        qn = np.sqrt((Q.astype(np.float64) ** 2).sum(axis=1))
        U, I = Q.shape
        out = np.zeros((U, I), dtype=np.float64)
        nB = self.B.shape[0]
        if nB == 0:
            return out
        k = min(k, nB)
        BT = np.ascontiguousarray(self.B.T)
        for s in range(0, U, self.chunk):
            e = min(U, s + self.chunk)
            num = Q[s:e] @ BT                                       # (c, nB)
            den = qn[s:e, None].astype(np.float32) * self.bnorm[None, :].astype(np.float32)
            sim = np.divide(num, den, out=np.zeros_like(num), where=den > 0)
            sim[np.arange(s, e)[:, None] == self.owner[None, :]] = 0.0   # no own baskets
            top = np.argpartition(-sim, k - 1, axis=1)[:, :k]
            ts = np.take_along_axis(sim, top, axis=1)                # (c, k)
            ts[ts < 0] = 0.0
            out[s:e] = np.einsum("ck,cki->ci", ts, self.B[top], dtype=np.float64)
        return out

    @classmethod
    def param_space(cls):
        return grid(L=[1, 3, 7], k=[50, 100, 200, 500], M=[1000, 5000, None], variant=["sknn", "vsknn"])
