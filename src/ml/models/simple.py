"""Non-personalised and trivial baselines: B1 Random, B2 Pop, B3 Recent-Pop, B8 Personal-repeat."""
from __future__ import annotations

import math
import zlib

import numpy as np

from ..signals import TAU_SPACE, SignalSpec, signal_matrix
from .base import Recommender, grid


class RandomRec(Recommender):
    """B1: uniform random ranking (scale anchor; HR@K ≈ 1 − C(N−|T|,K)/C(N,K))."""

    name = "B1_Random"
    stochastic = True

    def _score(self):
        tr = self.train
        rng = np.random.default_rng([self.seed, zlib.crc32(f"{tr.pres}|{tr.cut}|{tr.phase}".encode())])
        return rng.random((tr.n_users, tr.n_items))


class Pop(Recommender):
    """B2: s(i) = number of distinct learners with W_ui > 0 over the whole training period."""

    name = "B2_Pop"

    def _score(self):
        tr = self.train
        return np.broadcast_to(tr.popularity(), (tr.n_users, tr.n_items)).copy()


def recent_popularity(train, w: int) -> np.ndarray:
    """Distinct learners with an access to i in (t0 − w, t0]."""
    m = train.ev_d > train.t0 - w
    pairs = np.unique(train.ev_u[m].astype(np.int64) * train.n_items + train.ev_i[m])
    return np.bincount(pairs % train.n_items, minlength=train.n_items).astype(np.float64)


class RecentPop(Recommender):
    """B3: s(i; t0, w) = |{u : ∃ d ∈ (t0−w, t0], c_uid > 0}|, w ∈ {7, 14}."""

    name = "B3_RecentPop"

    def _score(self):
        tr = self.train
        s = recent_popularity(tr, int(self.params.get("w", 14)))
        return np.broadcast_to(s, (tr.n_users, tr.n_items)).copy()

    @classmethod
    def param_space(cls):
        return grid(w=[7, 14])


class PersonalRepeat(Recommender):
    """B8 (task B only): s(u,i) = W^{L2}_ui (days with recency decay τ; τ = ∞ ⇒ days)."""

    name = "B8_PersonalRepeat"
    tasks = ("B",)

    def _score(self):
        tau = float(self.params.get("tau", 14.0))
        spec = SignalSpec("L1") if math.isinf(tau) else SignalSpec("L2", tau=tau)
        return signal_matrix(self.train, spec)

    @classmethod
    def param_space(cls):
        return grid(tau=list(TAU_SPACE))
