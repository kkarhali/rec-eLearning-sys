"""B7: WRMF with alternating least squares (Hu, Koren & Volinsky 2008), numpy only.

    min Σ_{u,i} c_ui (p_ui − x_uᵀ y_i)² + λ (Σ‖x_u‖² + Σ‖y_i‖²)
    x_u = (Yᵀ C^u Y + λI)⁻¹ Yᵀ C^u p_u   (closed form per learner; symmetric per item)

p = 1[W > 0], c = 1 + α·W (draft §3.5). Deterministic given the initialisation
X, Y ~ N(0, 0.01²) drawn from the seed. The per-learner normal matrices
Yᵀ diag(c_u) Y are formed in chunks with one GEMM C · vec(y_i y_iᵀ)
(catalogues have ≤ 530 items), then solved in float64.
"""
from __future__ import annotations

import numpy as np

from ..signals import ALPHA_SPACE, SignalSpec, all_signal_specs, signal_matrix, wrmf_preference_confidence
from .base import Recommender, grid


def _vec_outer(F32: np.ndarray) -> np.ndarray:
    """Row-wise vec(f_n f_nᵀ) as an N×f² float32 matrix."""
    N, f = F32.shape
    return (F32[:, :, None] * F32[:, None, :]).reshape(N, f * f)


def normal_matrices(C: np.ndarray, F: np.ndarray, reg: float) -> np.ndarray:
    """A_r = Fᵀ diag(C[r]) F + λI for every row r of C (C: R×N, F: N×f). Reference/test helper."""
    f = F.shape[1]
    A = (C.astype(np.float64) @ _vec_outer(F.astype(np.float64))).reshape(C.shape[0], f, f)
    return A + reg * np.eye(f)[None]


def als_half_step(C: np.ndarray, P: np.ndarray, F: np.ndarray, reg: float, chunk: int = 128) -> np.ndarray:
    """Closed-form solve for the factors of every row of C/P given the fixed column factors F.

    A_r = Fᵀ diag(c_r) F + λI is formed as c_r · vec(f_n f_nᵀ) (one float32 GEMM per chunk of
    rows) and solved in float64. Small row chunks keep temporaries in cache and avoid
    page-faulting large buffers (≈ 10× faster than one big batched solve at f = 128).
    """
    R, N = C.shape
    f = F.shape[1]
    out = np.empty((R, f))
    B = (C * P) @ F
    C32 = C.astype(np.float32)
    eye = reg * np.eye(f)
    if N <= 1024:
        FF = _vec_outer(F.astype(np.float32))
        for s in range(0, R, chunk):
            e = min(R, s + chunk)
            A = (C32[s:e] @ FF).reshape(e - s, f, f).astype(np.float64) + eye
            out[s:e] = np.linalg.solve(A, B[s:e, :, None])[..., 0]
    else:
        acc = np.zeros((R, f * f), dtype=np.float32)
        CT = np.ascontiguousarray(C32.T)
        F32 = F.astype(np.float32)
        for s in range(0, N, 256):
            e = min(N, s + 256)
            acc += CT[s:e].T @ _vec_outer(F32[s:e])
        for s in range(0, R, chunk):
            e = min(R, s + chunk)
            A = acc[s:e].reshape(e - s, f, f).astype(np.float64) + eye
            out[s:e] = np.linalg.solve(A, B[s:e, :, None])[..., 0]
    return out


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
