"""B10: EASE (Steck 2019) — reference baseline only (D-37, ADR-004 §2.4).

Closed form on the binary learner × item matrix X:
    P = (XᵀX + λI)⁻¹,   B_ij = −P_ij / P_jj (i ≠ j),   B_jj = 0,   s(u,·) = x_u B
λ ∈ {1, 10, 50, 100, 500}. Not a hybrid component and not part of any hypothesis.
"""
from __future__ import annotations

import numpy as np

from .base import Recommender, grid


def ease_weights(X: np.ndarray, lam: float) -> np.ndarray:
    G = X.T @ X + lam * np.eye(X.shape[1])
    P = np.linalg.inv(G)
    B = -P / np.diag(P)[None, :]
    np.fill_diagonal(B, 0.0)
    return B


class EASE(Recommender):
    name = "B10_EASE"

    def _fit(self, train):
        self.X = train.seen.astype(np.float64)
        self.B = ease_weights(self.X, float(self.params.get("lam", 100.0)))

    def _score(self):
        return self.X @ self.B

    @classmethod
    def param_space(cls):
        return grid(lam=[1.0, 10.0, 50.0, 100.0, 500.0])
