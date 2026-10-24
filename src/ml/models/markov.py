"""B6: first-order Markov chain between consecutive active-day baskets (draft §4.2.6).

    P(j | a) = (N_aj + γ) / (Σ_j' N_aj' + γ |I|),   s(j) = (1/|S|) Σ_{a ∈ S} P(j | a)

S = last active-day basket of the learner (L = 1) or the union of the last L baskets.
"""
from __future__ import annotations

import numpy as np

from .base import Recommender, grid
from .baskets import consecutive_day_transitions, last_days_query


def transition_probabilities(N: np.ndarray, gamma: float) -> np.ndarray:
    I = N.shape[0]
    return (N + gamma) / (N.sum(axis=1, keepdims=True) + gamma * I)


class Markov(Recommender):
    name = "B6_Markov"

    def _fit(self, train):
        self.N = consecutive_day_transitions(train)
        self.P = transition_probabilities(self.N, float(self.params.get("gamma", 0.5)))

    def _score(self):
        Q = last_days_query(self.train, int(self.params.get("L", 1)), "binary")
        size = Q.sum(axis=1, keepdims=True)
        return np.divide(Q @ self.P, size, out=np.zeros((Q.shape[0], self.P.shape[1])), where=size > 0)

    @classmethod
    def param_space(cls):
        return grid(gamma=[0.01, 0.1, 0.5, 1.0], L=[1, 3])
