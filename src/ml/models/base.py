"""Common recommender interface.

    model = SomeModel(seed=0, **params).fit(train)     # train: splits.TrainData (d ≤ t0 only)
    S = model.score()                                  # dense U×I scores over the catalogue
    model.recommend(student_id, k=10, exclude_seen=True)   # list of id_site

``exclude_seen=True`` is task A (candidates = C \\ I_u), ``False`` is task B (all of C).
Ties are broken with the protocol keys ``train.tiebreak`` (draft §5.3).

New model families (GRU-lite, cluster popularity, assessment proximity …) only need to
subclass :class:`Recommender`, implement ``_fit`` and ``_score`` and declare
``param_space``; the harness and the hybrid consume them unchanged.
"""
from __future__ import annotations

import itertools
import zlib

import numpy as np

from ..metrics import rank_order


class Recommender:
    name = "base"
    stochastic = False          # True ⇒ evaluated with 5 seeds
    tasks = ("A", "B")          # tasks the model is meaningful for

    def __init__(self, seed: int = 0, **params):
        self.seed = seed
        self.params = params
        self.train = None
        self._scores = None

    # -- interface ---------------------------------------------------------------
    def fit(self, train):
        self.train = train
        self._scores = None
        self._fit(train)
        return self

    def score(self) -> np.ndarray:
        if self._scores is None:
            self._scores = np.asarray(self._score(), dtype=np.float64)
        return self._scores

    def recommend(self, student, k: int = 10, exclude_seen: bool = True) -> list[int]:
        tr = self.train
        u = tr.user_index(student)
        cand = ~tr.seen[u] if exclude_seen else np.ones(tr.n_items, dtype=bool)
        order = rank_order(self.score()[u:u + 1], cand[None, :], tr.tiebreak[u:u + 1])[0]
        order = order[cand[order]][:k]
        return tr.items[order].tolist()

    # -- to implement ----------------------------------------------------------------
    def _fit(self, train):
        pass

    def _score(self) -> np.ndarray:
        raise NotImplementedError

    @classmethod
    def param_space(cls) -> list[dict]:
        return [{}]

    def describe(self) -> str:
        if not self.params:
            return self.name
        return self.name + "(" + ",".join(f"{k}={_fmt(v)}" for k, v in sorted(self.params.items())) + ")"


def _fmt(v):
    if hasattr(v, "key"):
        return v.key
    if isinstance(v, float):
        return f"{v:g}"
    return str(v)


def grid(**axes) -> list[dict]:
    keys = list(axes)
    return [dict(zip(keys, vals)) for vals in itertools.product(*(axes[k] for k in keys))]


def sample_space(space: list[dict], budget: int, name: str) -> list[dict]:
    """≤ budget configurations; random subset (fixed seed per model name) when the space is larger."""
    if len(space) <= budget:
        return list(space)
    rng = np.random.default_rng(zlib.crc32(name.encode()) + 20261024)
    idx = np.sort(rng.choice(len(space), size=budget, replace=False))
    return [space[i] for i in idx]
