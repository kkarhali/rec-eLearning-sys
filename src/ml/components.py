"""Component score cache shared by the round-2 experiments (hybrid, H4-b, serving).

Scores of each component for each (presentation, origin, phase, seed) are stored as float32 U×I arrays in
``data/cache/components/<presentation>_<cut>/<component>_<phase>_s<seed>.npy`` (git-ignored), so the
hybrid acceptance search can re-rank without refitting. Configurations are those selected by the
standalone tuning of each component on validation, task A (D-42), read back from the result CSVs.
"""
from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pandas as pd

from .data import CACHE_DIR, RESULTS_DIR
from .signals import SignalSpec

COMP_DIR = CACHE_DIR / "components"


def comp_path(pres: str, cut: int, comp: str, phase: str, seed: int) -> Path:
    return COMP_DIR / f"{pres}_{cut}" / f"{comp}_{phase}_s{seed}.npy"


def save_scores(pres, cut, comp, phase, seed, S: np.ndarray) -> None:
    p = comp_path(pres, cut, comp, phase, seed)
    p.parent.mkdir(parents=True, exist_ok=True)
    np.save(p, S.astype(np.float32))


def load_scores(pres, cut, comp, phase, seed) -> np.ndarray:
    return np.load(comp_path(pres, cut, comp, phase, seed)).astype(np.float64)


def has_scores(pres, cut, comp, phase, seed) -> bool:
    return comp_path(pres, cut, comp, phase, seed).exists()


# --- config keys ↔ dicts ----------------------------------------------------------------------------
def parse_signal(s: str) -> SignalSpec:
    if s in ("L0", "L1"):
        return SignalSpec(s)
    lvl, rest = s.split("(", 1)
    kv = dict(x.split("=") for x in rest.rstrip(")").split(","))
    tau = math.inf if kv["tau"] in ("inf", "Infinity") else float(kv["tau"])
    return SignalSpec(lvl, tau=tau, beta=float(kv.get("beta", 0.0)))


_INT = {"w", "k", "L", "M", "f", "iters", "epochs", "dh", "de"}
_STR = {"variant", "target"}


def parse_config(key: str) -> dict:
    """Inverse of harness.config_key (e.g. 'alpha=20;f=16;iters=25;reg=1;signal=L3(tau=14,beta=2)')."""
    if key in ("-", "", None) or (isinstance(key, float) and math.isnan(key)):
        return {}
    out = {}
    for part in _split(key):
        k, v = part.split("=", 1)
        if k == "signal":
            out[k] = parse_signal(v)
        elif v == "None":
            out[k] = None
        elif k in _INT:
            out[k] = int(float(v))
        elif k in _STR:
            out[k] = v
        else:
            out[k] = float(v)
    return out


def _split(key: str) -> list[str]:
    parts, depth, cur = [], 0, ""
    for ch in key:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        if ch == ";" and depth == 0:
            parts.append(cur)
            cur = ""
        else:
            cur += ch
    if cur:
        parts.append(cur)
    return parts


def selected_configs(csv: Path | None = None, task: str = "A") -> dict[tuple[str, str, int], dict]:
    """{(model, presentation, cut): config} selected on validation for ``task`` (D-42)."""
    df = pd.read_csv(csv or RESULTS_DIR / "dev2013" / "baselines.csv")
    df = df[(df["task"] == task) & (df["slice"] == "all") & (df["seed"] <= 0)]
    return {(r.model, r.presentation, int(r.cut)): parse_config(r.config) for r in df.itertuples()}
