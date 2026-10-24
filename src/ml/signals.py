"""Nested implicit-signal family (ADR-001 item 6, ADR-002 §3.2, draft §3.4–3.5).

For registration u, item i and end of training t0, with D_ui the access days d ≤ t0 and
c_uid the (aggregated) clicks of day d:

    W_ui(t0) = Σ_{d ∈ D_ui} exp(−(t0 − d)/τ) · (1 + β · log1p(c_uid / m_type(i)))

m_type(i) is the median daily click count of the activity type of i, computed from the
training period only. Levels (each a special case of the next):

    L0  binary                1[|D_ui| > 0]
    L1  number of days        τ = ∞, β = 0
    L2  days + recency        β = 0
    L3  days + recency + type-normalised intensity

WRMF (Hu, Koren & Volinsky 2008): preference p_ui = 1[W_ui > 0], confidence c_ui = 1 + α·W_ui.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

LEVELS = ("L0", "L1", "L2", "L3")
TAU_SPACE = (7.0, 14.0, 28.0, 56.0, math.inf)
BETA_SPACE = (0.5, 1.0, 2.0)          # β = 0 is level L2
ALPHA_SPACE = (1.0, 2.0, 5.0, 10.0, 20.0, 40.0)


@dataclass(frozen=True)
class SignalSpec:
    level: str = "L1"
    tau: float = math.inf
    beta: float = 0.0

    def __post_init__(self):
        if self.level not in LEVELS:
            raise ValueError(self.level)

    @property
    def key(self) -> str:
        if self.level in ("L0", "L1"):
            return self.level
        if self.level == "L2":
            return f"L2(tau={self.tau:g})"
        return f"L3(tau={self.tau:g},beta={self.beta:g})"


def recency_factor(t0: float, days, tau: float) -> np.ndarray:
    days = np.asarray(days, dtype=float)
    if math.isinf(tau):
        return np.ones_like(days)
    return np.exp(-(t0 - days) / tau)


def intensity_factor(clicks, median, beta: float) -> np.ndarray:
    clicks = np.asarray(clicks, dtype=float)
    return 1.0 + beta * np.log1p(clicks / np.asarray(median, dtype=float))


def type_medians(item_type_of_event: np.ndarray, clicks: np.ndarray) -> dict[str, float]:
    """Median daily clicks per activity type (training events only)."""
    out: dict[str, float] = {}
    types = np.asarray(item_type_of_event)
    clicks = np.asarray(clicks, dtype=float)
    for t in np.unique(types):
        out[str(t)] = float(np.median(clicks[types == t]))
    return out


def event_weights(spec: SignalSpec, t0: float, days, clicks, medians_per_event) -> np.ndarray:
    """Per-(u,i,d) contribution to W under the chosen level."""
    days = np.asarray(days, dtype=float)
    if spec.level in ("L0", "L1"):
        return np.ones_like(days)
    w = recency_factor(t0, days, spec.tau)
    if spec.level == "L3":
        w = w * intensity_factor(clicks, medians_per_event, spec.beta)
    return w


def signal_matrix(train, spec: SignalSpec) -> np.ndarray:
    """Dense U×I matrix W for a :class:`splits.TrainData` (float64)."""
    U, I = len(train.users), len(train.items)
    W = np.zeros((U, I), dtype=np.float64)
    if spec.level == "L0":
        W[train.seen] = 1.0
        return W
    med = train.type_medians_per_event if spec.level == "L3" else None
    w = event_weights(spec, train.t0, train.ev_d, train.ev_c, med)
    np.add.at(W, (train.ev_u, train.ev_i), w)
    return W


def wrmf_preference_confidence(W: np.ndarray, alpha: float, binary_confidence: bool = False):
    """p = 1[W>0]; c = 1 + α·W  (or 1 + α·1[W>0] for the binary comparator of H2-a)."""
    P = (W > 0).astype(np.float64)
    C = 1.0 + alpha * (P if binary_confidence else W)
    return P, C


def all_signal_specs() -> list[SignalSpec]:
    specs = [SignalSpec("L0"), SignalSpec("L1")]
    specs += [SignalSpec("L2", tau=t) for t in TAU_SPACE if not math.isinf(t)]
    specs += [SignalSpec("L3", tau=t, beta=b) for t in TAU_SPACE for b in BETA_SPACE]
    return specs
