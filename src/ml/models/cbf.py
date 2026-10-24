"""B9: content-based filtering on the structural attributes available in OULAD (draft §4.2.9).

Item features φ_i (three groups, each multiplied by a group weight ∈ {0, 0.5, 1}):
  * activity_type one-hot (types present in the catalogue);
  * week of first use before t0: floor(min access day / 7) / 10;
  * assessment-proximity profile: ρ_i(b) = share of active learner-days in bin b
    ({0–3, 4–7, 8–14, >14} days to the next published assessment) that include i,
    normalised to sum 1 over the four bins (shape of the profile).
Learner profile π_u = Σ_i W_ui φ_i / Σ_i W_ui with W = number of days (L1);
score s(u,j) = cos(π_u, φ_j).

``vle.week_from/to`` are empty for most resources and are therefore not used (draft §3.1).
"""
from __future__ import annotations

import numpy as np

from ..data import next_assessment_gap, proximity_bin
from ..signals import SignalSpec, signal_matrix
from .base import Recommender, grid
from .baskets import day_keys


def proximity_profile(train) -> np.ndarray:
    """I×4 matrix ρ_i(b) computed from the training period only."""
    gaps = next_assessment_gap(np.arange(train.ev_d.min(), train.t0 + 1), train.assessments["date"])
    day0 = train.ev_d.min()
    bins_by_day = proximity_bin(gaps)
    bu, bd, inv = day_keys(train)
    basket_bin = bins_by_day[bd - day0]
    den = np.bincount(basket_bin, minlength=4).astype(float)
    ev_bin = basket_bin[inv]
    num = np.zeros((train.n_items, 4))
    np.add.at(num, (train.ev_i, ev_bin), 1.0)        # one event per (u, i, d) after aggregation
    rho = np.divide(num, den[None, :], out=np.zeros_like(num), where=den[None, :] > 0)
    s = rho.sum(axis=1, keepdims=True)
    return np.divide(rho, s, out=np.zeros_like(rho), where=s > 0)


def item_features(train, w_type: float, w_week: float, w_assess: float) -> np.ndarray:
    types = np.unique(train.item_type)
    onehot = (train.item_type[:, None] == types[None, :]).astype(float)
    first_day = np.full(train.n_items, np.inf)
    np.minimum.at(first_day, train.ev_i, train.ev_d.astype(float))
    week = np.floor(first_day / 7.0)[:, None] / 10.0
    parts = [w_type * onehot, w_week * week, w_assess * proximity_profile(train)]
    return np.hstack(parts)


class CBF(Recommender):
    name = "B9_CBF"

    def _fit(self, train):
        p = self.params
        self.phi = item_features(train, float(p.get("w_type", 1.0)), float(p.get("w_week", 1.0)),
                                 float(p.get("w_assess", 1.0)))

    def _score(self):
        W = signal_matrix(self.train, SignalSpec("L1"))
        tot = W.sum(axis=1, keepdims=True)
        prof = np.divide(W @ self.phi, tot, out=np.zeros((W.shape[0], self.phi.shape[1])), where=tot > 0)
        pn = np.linalg.norm(prof, axis=1, keepdims=True)
        fn = np.linalg.norm(self.phi, axis=1, keepdims=True).T
        den = pn * fn
        return np.divide(prof @ self.phi.T, den, out=np.zeros_like(den), where=den > 0)

    @classmethod
    def param_space(cls):
        g = grid(w_type=[0.0, 0.5, 1.0], w_week=[0.0, 0.5, 1.0], w_assess=[0.0, 0.5, 1.0])
        return [c for c in g if any(v > 0 for v in c.values())]
