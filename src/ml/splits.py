"""Global temporal cuts, tune/test phases and tasks A/B (ADR-002 §3.6, D-14).

For every presentation and origin t ∈ {70, 126, 182}:

    phase "tune": train d ≤ t−14, validation window (t−14, t]
    phase "test": train d ≤ t,    test window       (t, t+14]

Catalogue C(t0): non-excluded items with ≥ 1 access in the training period (d ≤ t0).
Task A (primary): targets = window items not visited before t0, candidates = C \\ I_u.
Task B (secondary): targets = all window items (incl. repeats), candidates = C.
Window items outside the catalogue are counted as misses ("unreachable").

Evaluated learner (task-specific): ≥ 1 catalogue interaction in training and ≥ 1 target.

Leakage design: :func:`make_fold` returns a :class:`TrainData` (the only object passed to
models) built exclusively from rows with d ≤ t0, and a separate :class:`Targets` object
used only by the evaluator.
"""
from __future__ import annotations

import zlib
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from .data import EXCLUSION_SETS, PresentationData

CUTS = (70, 126, 182)
HORIZON = 14
PHASES = ("tune", "test")
TASKS = ("A", "B")


def phase_t0(cut: int, phase: str) -> int:
    if phase == "tune":
        return cut - HORIZON
    if phase == "test":
        return cut
    raise ValueError(phase)


# --- deterministic tie-breaking (draft §5.3) ------------------------------------------------
_M64 = np.uint64(0xFFFFFFFFFFFFFFFF)


def _splitmix64(x: np.ndarray) -> np.ndarray:
    with np.errstate(over="ignore"):
        x = (x + np.uint64(0x9E3779B97F4A7C15)) & _M64
        x = ((x ^ (x >> np.uint64(30))) * np.uint64(0xBF58476D1CE4E5B9)) & _M64
        x = ((x ^ (x >> np.uint64(27))) * np.uint64(0x94D049BB133111EB)) & _M64
        return x ^ (x >> np.uint64(31))


def tiebreak_keys(pres: str, cut: int, students: np.ndarray, items: np.ndarray) -> np.ndarray:
    """U×I uniform keys in [0,1) derived only from (presentation, origin, learner, item).

    Identical for every model, so no model gains from id order or popularity on ties.
    """
    base = np.uint64(zlib.crc32(f"{pres}|{cut}".encode()))
    s = np.asarray(students, dtype=np.uint64)[:, None]
    i = np.asarray(items, dtype=np.uint64)[None, :]
    with np.errstate(over="ignore"):
        x = (base << np.uint64(40)) ^ (s * np.uint64(1_000_003)) ^ (i * np.uint64(0x9E3779B1))
    h = _splitmix64(_splitmix64(x))
    return (h >> np.uint64(11)).astype(np.float64) / float(1 << 53)


# --- containers ---------------------------------------------------------------------------------
@dataclass
class TrainData:
    """Training view handed to models. Built from rows with d ≤ t0 only."""

    pres: str
    cut: int
    phase: str
    t0: int
    exclusion: str
    users: np.ndarray            # id_student of learners with ≥ 1 catalogue interaction ≤ t0 (U)
    items: np.ndarray            # catalogue id_site (I), sorted
    item_type: np.ndarray        # activity_type per catalogue item
    ev_u: np.ndarray             # daily catalogue events (u, i, d, c), d ≤ t0
    ev_i: np.ndarray
    ev_d: np.ndarray
    ev_c: np.ndarray
    seen: np.ndarray             # bool U×I, visited before t0
    all_events: pd.DataFrame     # all activity types d ≤ t0 (context / learner features)
    assessments: pd.DataFrame    # published schedule (allowed, ADR-002 §3.6.10)
    tiebreak: np.ndarray         # U×I keys
    type_medians: dict = field(default_factory=dict)
    type_medians_per_event: np.ndarray | None = None
    registrations: pd.DataFrame | None = None   # id_student, date_registration only (known at registration)

    @property
    def n_users(self) -> int:
        return len(self.users)

    @property
    def n_items(self) -> int:
        return len(self.items)

    def user_index(self, student) -> int:
        k = int(np.searchsorted(self.users, student))
        if k >= len(self.users) or self.users[k] != student:
            raise KeyError(student)
        return k

    def popularity(self) -> np.ndarray:
        """Distinct learners per catalogue item over the whole training period."""
        return self.seen.sum(axis=0).astype(np.float64)


@dataclass
class Targets:
    """Evaluation-only view of the target window (t0, t0+14]."""

    window: tuple[int, int]
    target: np.ndarray           # bool U×I: in-catalogue window items (task B)
    unreach: np.ndarray          # int U: window items outside the catalogue
    seen: np.ndarray             # bool U×I (copy of TrainData.seen, for task A)
    n_window_learners: int       # registrations with ≥ 1 non-excluded window event
    n_window_learners_no_train: int  # … of which have no catalogue interaction ≤ t0
    n_window_pairs: int          # distinct (learner, item) window pairs, non-excluded
    n_window_pairs_unreachable: int

    def task(self, name: str):
        """Return (targets U×I, candidates U×I, unreachable U, evaluated U)."""
        if name == "A":
            tgt = self.target & ~self.seen
            cand = ~self.seen
        elif name == "B":
            tgt = self.target
            cand = np.ones_like(self.seen)
        else:
            raise ValueError(name)
        unreach = self.unreach        # out-of-catalogue items are new for everybody
        evaluated = (tgt.sum(axis=1) + unreach) > 0
        return tgt, cand, unreach, evaluated


def build_train(p: PresentationData, t0: int, cut: int, phase: str, exclusion: str = "E5") -> TrainData:
    """Training view from rows with d ≤ t0 only (also used by the replay service for any day, D-49)."""
    ev = p.events
    excluded = EXCLUSION_SETS[exclusion]
    is_target_type = ~ev["activity_type"].astype(str).isin(excluded).to_numpy()
    train_mask = ev["date"].to_numpy() <= t0
    tr_all = ev.loc[train_mask].reset_index(drop=True)
    tr = ev.loc[train_mask & is_target_type]
    items = np.unique(tr["id_site"].to_numpy())
    users = np.unique(tr["id_student"].to_numpy())
    U, I = len(users), len(items)

    ev_u = np.searchsorted(users, tr["id_student"].to_numpy()).astype(np.int32)
    ev_i = np.searchsorted(items, tr["id_site"].to_numpy()).astype(np.int32)
    seen = np.zeros((U, I), dtype=bool)
    seen[ev_u, ev_i] = True

    type_map = (p.items.set_index("id_site")["activity_type"].astype(str))
    item_type = type_map.reindex(items).to_numpy()
    ev_type = tr["activity_type"].astype(str).to_numpy()
    from .signals import type_medians as _tm
    meds = _tm(ev_type, tr["clicks"].to_numpy())
    med_per_event = np.array([meds[t] for t in ev_type], dtype=np.float64) if len(ev_type) else np.zeros(0)
    return TrainData(
        pres=p.name, cut=cut, phase=phase, t0=t0, exclusion=exclusion,
        users=users, items=items, item_type=item_type,
        ev_u=ev_u, ev_i=ev_i, ev_d=tr["date"].to_numpy().astype(np.int32),
        ev_c=tr["clicks"].to_numpy().astype(np.int32), seen=seen,
        all_events=tr_all, assessments=p.assessments.copy(),
        tiebreak=tiebreak_keys(p.name, cut, users, items),
        type_medians=meds, type_medians_per_event=med_per_event,
        registrations=p.registrations[["id_student", "date_registration"]].copy()
        if "date_registration" in p.registrations else None,
    )


def make_fold(p: PresentationData, cut: int, phase: str, exclusion: str = "E5",
              horizon: int = HORIZON) -> tuple[TrainData, Targets]:
    t0 = phase_t0(cut, phase)
    if t0 + horizon > p.length:
        raise ValueError(f"{p.name}: window ({t0}, {t0 + horizon}] exceeds presentation length {p.length}")
    train = build_train(p, t0, cut, phase, exclusion)
    users, items, seen = train.users, train.items, train.seen
    U, I = len(users), len(items)
    ev = p.events
    is_target_type = ~ev["activity_type"].astype(str).isin(EXCLUSION_SETS[exclusion]).to_numpy()
    d = ev["date"].to_numpy()
    win_mask = (d > t0) & (d <= t0 + horizon)

    win = ev.loc[win_mask & is_target_type, ["id_student", "id_site"]].drop_duplicates()
    in_users = np.isin(win["id_student"].to_numpy(), users)
    in_items = np.isin(win["id_site"].to_numpy(), items)
    target = np.zeros((U, I), dtype=bool)
    w_ok = win.loc[in_users & in_items]
    target[np.searchsorted(users, w_ok["id_student"].to_numpy()),
           np.searchsorted(items, w_ok["id_site"].to_numpy())] = True
    unreach = np.zeros(U, dtype=np.int64)
    w_un = win.loc[in_users & ~in_items]
    np.add.at(unreach, np.searchsorted(users, w_un["id_student"].to_numpy()), 1)
    win_learners = np.unique(win["id_student"].to_numpy())
    targets = Targets(
        window=(t0, t0 + horizon), target=target, unreach=unreach, seen=seen.copy(),
        n_window_learners=len(win_learners),
        n_window_learners_no_train=int((~np.isin(win_learners, users)).sum()),
        n_window_pairs=len(win), n_window_pairs_unreachable=int((~in_items).sum()),
    )
    return train, targets


def check_no_overlap(train: TrainData, targets: Targets) -> None:
    """Assert the training period and the target window are disjoint (raises on violation)."""
    lo, hi = targets.window
    if len(train.ev_d) and train.ev_d.max() > train.t0:
        raise AssertionError("training events after t0")
    if not (lo == train.t0 and hi > lo):
        raise AssertionError("window does not start at t0")
    if len(train.all_events) and train.all_events["date"].max() > train.t0:
        raise AssertionError("context events after t0")
