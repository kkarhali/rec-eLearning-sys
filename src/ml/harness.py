"""Tune-then-test loop shared by the experiments (ADR-002 §3.6.1, §3.6.9).

For one (presentation, origin t):
  1. tune phase  — train ≤ t−14, score every configuration (≤ 20 per model) on (t−14, t];
                   pick the best configuration per task by validation NDCG@10;
  2. test phase  — refit on ≤ t with the selected configuration and evaluate on (t, t+14]
                   (all metrics, slices all / cold_q1 / top_q4 / lt5), 5 seeds for stochastic models.
Stochastic models are tuned with seed 0 only (D-34). WRMF iteration checkpoints are not counted
as settings (ADR-004 §2.4), so WRMF gets 20 base configurations × checkpoints {10, 15, 25}.
Slices (D-28): all; cold_q1 = bottom quartile of distinct catalogue items in training among the
evaluated learners of the (presentation, origin, phase, task); top_q4 = top quartile; lt5 = < 5 items
(descriptive). Every test row carries the validation NDCG@10 of the selected configuration so the
optimism gap (validation − test) can be reported (D-29).
"""
from __future__ import annotations

import resource
import time
from dataclasses import dataclass

import numpy as np

from . import metrics
from .data import PresentationData
from .models import BASELINES, sample_space
from .models.wrmf import WRMF
from .splits import make_fold

SEEDS = (0, 1, 2, 3, 4)
BUDGET = 20
COLD_THRESHOLD = 5          # < 5 distinct catalogue items in training ⇒ descriptive "lt5" slice
TUNE_METRIC = "NDCG@10"
WRMF_BASES = BUDGET         # checkpoints {10, 15, 25} are not settings (ADR-004 §2.4)


def model_configs(name: str) -> list[dict]:
    cls = BASELINES[name]
    space = cls.param_space()
    if cls is WRMF:
        return sample_space(space, WRMF_BASES, name)
    return sample_space(space, BUDGET, name)


def config_key(cfg: dict) -> str:
    def fmt(v):
        if hasattr(v, "key"):
            return v.key
        if isinstance(v, float):
            return f"{v:g}"
        return str(v)
    return ";".join(f"{k}={fmt(v)}" for k, v in sorted(cfg.items())) or "-"


def iter_settings(name: str, configs: list[dict], train, seed: int):
    """Yield (config, scores) for every tuning setting (WRMF iterations as checkpoints)."""
    cls = BASELINES[name]
    for cfg in configs:
        t = time.time()
        if cls is WRMF:
            m = cls(seed=seed, **cfg, iters=max(WRMF.ITER_CHECKPOINTS),
                    checkpoints=WRMF.ITER_CHECKPOINTS).fit(train)
            secs = time.time() - t
            for it in WRMF.ITER_CHECKPOINTS:
                yield {**cfg, "iters": it}, m.scores_at(it), secs
        else:
            S = cls(seed=seed, **cfg).fit(train).score()
            yield cfg, S, time.time() - t


def _task_views(targets, tasks):
    return {t: targets.task(t) for t in tasks}


def _val_score(scores, view, tiebreak):
    tgt, cand, unreach, ev = view
    res = metrics.evaluate(scores, cand, tgt, unreach, ev, tiebreak, ks=(10,))
    return metrics.summarize(res)[TUNE_METRIC] if res["n_eval"] else float("nan")


@dataclass
class JobResult:
    rows: list
    tuning: list
    timing: list
    folds: list


def run_job(p: PresentationData, cut: int, model_names, exclusion: str = "E5",
            seeds=SEEDS, tasks=("A", "B")) -> JobResult:
    rows, tuning, timing, folds = [], [], [], []
    # ---------------- tune phase ----------------
    tr, tg = make_fold(p, cut, "tune", exclusion)
    views = _task_views(tg, tasks)
    best: dict[tuple[str, str], tuple[float, dict]] = {}
    for name in model_names:
        cls = BASELINES[name]
        my_tasks = [t for t in tasks if t in cls.tasks]
        if not my_tasks:
            continue
        configs = model_configs(name)
        t_start = time.time()
        n_set = 0
        for cfg, S, secs in iter_settings(name, configs, tr, seed=seeds[0]):
            n_set += 1
            rec = {"presentation": p.name, "cut": cut, "model": name, "config": config_key(cfg),
                   "fit_score_seconds": secs}
            for t in my_tasks:
                v = _val_score(S, views[t], tr.tiebreak)
                rec[f"val_{TUNE_METRIC}_{t}"] = v
                if (name, t) not in best or (np.isfinite(v) and v > best[(name, t)][0]):
                    best[(name, t)] = (v, cfg)
            tuning.append(rec)
        timing.append({"presentation": p.name, "cut": cut, "phase": "tune", "model": name,
                       "n_settings": n_set, "seconds": time.time() - t_start,
                       "maxrss_mb": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024})
    # ---------------- test phase ----------------
    tr, tg = make_fold(p, cut, "test", exclusion)
    views = _task_views(tg, tasks)
    pop = tr.popularity()
    n_train_items = tr.seen.sum(axis=1)
    folds.append({"presentation": p.name, "cut": cut, "t0": tr.t0, "n_learners_train": tr.n_users,
                  "catalogue": tr.n_items, "density": float(tr.seen.mean()),
                  "n_window_learners": tg.n_window_learners,
                  "n_window_learners_no_train": tg.n_window_learners_no_train,
                  "n_window_pairs": tg.n_window_pairs,
                  "unreachable_share": tg.n_window_pairs_unreachable / max(tg.n_window_pairs, 1),
                  **{f"n_eval_{t}": int(views[t][3].sum()) for t in tasks}})
    for name in model_names:
        cls = BASELINES[name]
        my_tasks = [t for t in tasks if t in cls.tasks]
        if not my_tasks:
            continue
        t_start = time.time()
        model_seeds = seeds if cls.stochastic else (seeds[0],)
        cache: dict[tuple[str, int], np.ndarray] = {}
        fit_secs: dict[tuple[str, int], float] = {}
        for t in my_tasks:
            val, cfg = best.get((name, t), (np.nan, {}))
            tgt, cand, unreach, ev = views[t]
            for s in model_seeds:
                key = (config_key(cfg), s)
                if key not in cache:
                    t_fit = time.time()
                    cache[key] = cls(seed=s, **cfg).fit(tr).score()
                    fit_secs[key] = time.time() - t_fit
                res = metrics.evaluate(cache[key], cand, tgt, unreach, ev, tr.tiebreak, pop=pop)
                n_items_eval = n_train_items[res_idx(ev)]
                q1, q3 = (np.quantile(n_items_eval, [0.25, 0.75]) if len(n_items_eval) else (0, 0))
                slices = (("all", None), ("cold_q1", n_items_eval <= q1), ("top_q4", n_items_eval >= q3),
                          ("lt5", n_items_eval < COLD_THRESHOLD))
                for slice_name, mask in slices:
                    row = {"presentation": p.name, "cut": cut, "task": t, "model": name,
                           "seed": s if cls.stochastic else -1, "slice": slice_name,
                           "config": config_key(cfg), f"val_{TUNE_METRIC}": val,
                           "fit_score_seconds": fit_secs[key],
                           "n_eval": int(res["n_eval"] if mask is None else mask.sum()),
                           **metrics.summarize(res, mask)}
                    if slice_name == "all":
                        row.update({f"Coverage@{k}": v for k, v in res["coverage"].items()})
                        row.update({f"PopBias@{k}": v for k, v in res["popbias"].items()})
                    rows.append(row)
        timing.append({"presentation": p.name, "cut": cut, "phase": "test", "model": name,
                       "n_settings": len(cache), "seconds": time.time() - t_start,
                       "maxrss_mb": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024})
    return JobResult(rows, tuning, timing, folds)


def res_idx(evaluated: np.ndarray) -> np.ndarray:
    return np.flatnonzero(evaluated)
