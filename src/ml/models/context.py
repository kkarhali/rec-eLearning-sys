"""Context components of the hybrid (draft §4.3): (6) assessment proximity and (7) cluster popularity."""
from __future__ import annotations

import numpy as np

from ..data import next_assessment_gap, proximity_bin
from ..learners import choose_k, vle_features, zscore
from .base import Recommender, grid
from .cbf import proximity_profile
from .simple import recent_popularity


class AssessmentProximity(Recommender):
    """(6) s6(i; t0) = ρ_i(bin(a(t0))): training access rate of i in learner-days of the same
    days-to-next-assessment bin as the end of training (published schedule only)."""

    name = "C6_AssessProx"

    def _fit(self, train):
        self.rho = proximity_profile(train, normalise=False)
        gap = next_assessment_gap([train.t0], train.assessments["date"])
        self.bin = int(proximity_bin(gap)[0])

    def _score(self):
        return np.broadcast_to(self.rho[:, self.bin], (self.train.n_users, self.train.n_items)).copy()


def cluster_features(train) -> np.ndarray:
    """Engagement, regularity and timing features up to t0 (draft §4.7.1, D-39-c), z-scored."""
    F = vle_features(train.all_events, train.users, train.t0)
    if train.registrations is not None:
        reg = train.registrations.set_index("id_student")["date_registration"]
        F["date_registration"] = reg.reindex(F.index).fillna(reg.median()).to_numpy()
    return zscore(F.to_numpy(dtype=float))


def cluster_choice(train, n_init: int = 10):
    """k-means++ with the k rule on the features up to t0; labels for seeds 0–4 (D-34, D-39-c)."""
    return choose_k(cluster_features(train), n_init=n_init)


class ClusterPop(Recommender):
    """(7) s7(i; u) = |{v : g(v) = g(u), ∃ d ∈ (t0−w, t0], c_vid > 0}| with k-means++ clusters recomputed at
    every (presentation, origin, phase) from features up to t0 (k by the draft §4.7.2 rule; seed = model seed)."""

    name = "C7_ClusterPop"
    stochastic = True

    def _fit(self, train):
        pre = self.params.get("precomputed")              # ClusterChoice from cluster_choice(train): reuse across w/seeds
        ch = pre if pre is not None else cluster_choice(train, n_init=int(self.params.get("n_init", 10)))
        self.k, self.stable = ch.k, ch.stable
        self.labels = ch.labels_by_seed.get(self.seed, ch.labels) if ch.labels_by_seed else ch.labels
        self.set_window(int(self.params.get("w", 7)))

    def set_window(self, w: int):
        train = self.train
        m = train.ev_d > train.t0 - w
        pairs = np.unique(train.ev_u[m].astype(np.int64) * train.n_items + train.ev_i[m])
        u, i = pairs // train.n_items, pairs % train.n_items
        C = np.zeros((self.k, train.n_items))
        np.add.at(C, (self.labels[u], i), 1.0)
        self.counts = C
        self._scores = None
        return self

    def _score(self):
        return self.counts[self.labels].copy()

    @classmethod
    def param_space(cls):
        return grid(w=[3, 7, 14, 21, 28])


__all__ = ["AssessmentProximity", "ClusterPop", "recent_popularity"]
