"""B7: WRMF with alternating least squares (Hu, Koren & Volinsky 2008), numpy only.

    min Σ_{u,i} c_ui (p_ui − x_uᵀ y_i)² + λ (Σ‖x_u‖² + Σ‖y_i‖²)
    x_u = (Yᵀ C^u Y + λI)⁻¹ Yᵀ C^u p_u   (closed form per learner; symmetric per item)

p = 1[W > 0], c = 1 + α·W (draft §3.5). Deterministic given the initialisation
X, Y ~ N(0, 0.01²) drawn from the seed. The per-learner normal matrices
Yᵀ diag(c_u) Y are formed for all learners at once with one GEMM
C · (y_i ⊗ y_i) (catalogues have ≤ 530 items), then solved in float64.
"""
from __future__ import annotations

import numpy as np

from ..signals import ALPHA_SPACE, SignalSpec, all_signal_specs, signal_matrix, wrmf_preference_confidence
from .base import Recommender, grid


def _normal_matrices(C: np.ndarray, F: np.ndarray, reg: float, chunk: int = 512) -> np.ndarray:
    """A_r = Fᵀ diag(C[r]) F + λI for every row r of C (C: R×N, F: N×f)."""
    N, f = F.shape
    FF = (F[:, :, None] * F[:, None, :]).reshape(N, f * f).astype(np.float32)
    R = C.shape[0]
    A = np.empty((R, f, f), dtype=np.float64)
    C32 = C.astype(np.float32)
    for s in range(0, R, chunk):
        e = min(R, s + chunk)
        A[s:e] = (C32[s:e] @ FF).reshape(e - s, f, f)
    A += reg * np.eye(f)[None]
    return A


def als_half_step(C: np.ndarray, P: np.ndarray, F: np.ndarray, reg: float) -> np.ndarray:
    """Solve for the factors of the rows of C/P given the fixed factors F of the columns."""
    A = _normal_matrices(C, F, reg)
    b = (C * P) @ F
    return np.linalg.solve(A, b[..., None])[..., 0]


def wrmf_loss(C, P, X, Y, reg) -> float:
    E = P - X @ Y.T
    return float((C * E * E).sum() + reg * ((X ** 2).sum() + (Y ** 2).sum()))


def als(C: np.ndarray, P: np.ndarray, f: int, reg: float, iters: int, seed: int,
        checkpoints=None, track_loss: bool = False):
    """Run ALS; returns (X, Y, losses, {iteration: (X, Y)} snapshots)."""
    rng = np.random.default_rng(seed)
    U, I = C.shape
    X = rng.normal(0.0, 0.01, (U, f))
    Y = rng.normal(0.0, 0.01, (I, f))
    CT, PT = np.ascontiguousarray(C.T), np.ascontiguousarray(P.T)
    losses, snaps = [], {}
    for it in range(1, iters + 1):
        X = als_half_step(C, P, Y, reg)
        Y = als_half_step(CT, PT, X, reg)
        if track_loss:
            losses.append(wrmf_loss(C, P, X, Y, reg))
        if checkpoints and it in checkpoints:
            snaps[it] = (X.copy(), Y.copy())
    return X, Y, losses, snaps


class WRMF(Recommender):
    name = "B7_WRMF"
    stochastic = True

    def _fit(self, train):
        p = self.params
        spec = p.get("signal", SignalSpec("L1"))
        W = signal_matrix(train, spec)
        P, C = wrmf_preference_confidence(W, float(p.get("alpha", 2.0)),
                                          binary_confidence=(spec.level == "L0"))
        iters = int(p.get("iters", 15))
        cps = set(p.get("checkpoints", ())) | {iters}
        X, Y, _, snaps = als(C, P, int(p.get("f", 32)), float(p.get("reg", 0.1)), max(cps), self.seed,
                             checkpoints=cps)
        self.snapshots = snaps
        self.X, self.Y = snaps[iters]

    def _score(self):
        return self.X @ self.Y.T

    def scores_at(self, iteration: int) -> np.ndarray:
        X, Y = self.snapshots[iteration]
        return X @ Y.T

    @classmethod
    def param_space(cls):
        # 'iters' is evaluated as checkpoints of one run (10, 15, 25), see README §decisions
        return grid(f=[16, 32, 64, 128], reg=[0.01, 0.1, 1.0, 10.0], alpha=list(ALPHA_SPACE),
                    signal=all_signal_specs())

    ITER_CHECKPOINTS = (10, 15, 25)
