"""Signal-family ablation (H2-a; draft §2.4, §5.11) → results/dev2013/ablation_signals.csv.

    python3 -m src.ml.experiments.run_ablation [--workers 4]

For WRMF (primary) and Item-kNN (secondary), each signal variant gets its own ≤ 20-setting budget, tuned
with seed 0 on validation NDCG@10 (task A), reported on the test windows with 5 seeds (WRMF) / 1 (Item-kNN):
    L0  binary (WRMF confidence 1 + α·1[W>0])      L1  days
    L2  days + recency τ                           L3  days + recency τ + type-normalised intensity β
    W*  the whole weighted family L1 ∪ L2 ∪ L3 (the H2-a treatment: "best member, τ/β/α tuned on validation")
H2-a (development analogue): Δ_p = WRMF(W*) − WRMF(L0) per presentation, bootstrap-t over the nine
presentations (descriptive; the confirmatory test is on 2014 after the freeze).
"""
from __future__ import annotations

import os

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")

import argparse  # noqa: E402
import json  # noqa: E402
import math  # noqa: E402
import multiprocessing as mp  # noqa: E402
import time  # noqa: E402

import pandas as pd  # noqa: E402

from .. import data  # noqa: E402
from ..harness import SEEDS, BUDGET, config_key, eval_rows, iter_settings, _val_score  # noqa: E402
from ..models import sample_space  # noqa: E402
from ..models.base import grid  # noqa: E402
from ..signals import ALPHA_SPACE, BETA_SPACE, TAU_SPACE, SignalSpec  # noqa: E402
from ..splits import CUTS, make_fold  # noqa: E402

OUT = data.RESULTS_DIR / "dev2013"
VARIANTS = ("L0", "L1", "L2", "L3", "Wstar")
_PRES: dict = {}


def signals_for(variant: str) -> list[SignalSpec]:
    L2 = [SignalSpec("L2", tau=t) for t in TAU_SPACE if not math.isinf(t)]
    L3 = [SignalSpec("L3", tau=t, beta=b) for t in TAU_SPACE for b in BETA_SPACE]
    return {"L0": [SignalSpec("L0")], "L1": [SignalSpec("L1")], "L2": L2, "L3": L3,
            "Wstar": [SignalSpec("L1")] + L2 + L3}[variant]


def space(model: str, variant: str) -> list[dict]:
    sig = signals_for(variant)
    if model == "B7_WRMF":
        sp = grid(f=[16, 32, 64], reg=[0.01, 0.1, 1.0, 10.0], alpha=list(ALPHA_SPACE), signal=sig)
    else:
        sp = grid(k=[20, 50, 100, None], shrink=[0.0, 10.0, 50.0, 100.0], signal=sig)
    return sample_space(sp, BUDGET, f"ablation|{model}|{variant}")


def run_job(args):
    name, cut, seeds = args
    p = _PRES[name]
    t_job = time.time()
    rows, tuning = [], []
    tr, tg = make_fold(p, cut, "tune")
    vA = tg.task("A")
    tr2, tg2 = make_fold(p, cut, "test")
    vA2 = tg2.task("A")
    for model in ("B7_WRMF", "B4_ItemKNN"):
        for variant in VARIANTS:
            best = None
            for cfg, S, secs in iter_settings(model, space(model, variant), tr, seed=seeds[0]):
                v = _val_score(S, vA, tr.tiebreak)
                tuning.append({"presentation": name, "cut": cut, "model": model, "variant": variant,
                               "config": config_key(cfg), "val_NDCG@10": v, "seconds": secs})
                if best is None or v > best[0]:
                    best = (v, cfg)
            from ..models import BASELINES
            cls = BASELINES[model]
            for s in (seeds if cls.stochastic else seeds[:1]):
                t = time.time()
                S = cls(seed=s, **best[1]).fit(tr2).score()
                rows += [dict(r, variant=variant) for r in
                         eval_rows(name, cut, model, "A", s if cls.stochastic else -1, config_key(best[1]), best[0],
                                   S, vA2, tr2, time.time() - t)]
    print(f"[ablation] {name} t={cut} ({time.time() - t_job:.0f}s)", flush=True)
    return rows, tuning


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--presentations", nargs="*", default=list(data.DEV_PRESENTATIONS))
    ap.add_argument("--cuts", nargs="*", type=int, default=list(CUTS))
    ap.add_argument("--workers", type=int, default=4)
    a = ap.parse_args(argv)
    data.assert_allowed(a.presentations)
    t0 = time.time()
    _PRES.update(data.load_dev_presentations(tuple(a.presentations)))
    order = ["FFF_2013J", "FFF_2013B", "DDD_2013J", "BBB_2013J", "DDD_2013B", "BBB_2013B", "EEE_2013J",
             "GGG_2013J", "AAA_2013J"]
    jobs = [(n, c, SEEDS) for c in sorted(a.cuts, reverse=True) for n in order if n in a.presentations]
    with mp.get_context("fork").Pool(a.workers) as pool:
        res = pool.map(run_job, jobs, chunksize=1)
    rows = pd.DataFrame([r for rr, _ in res for r in rr])
    tun = pd.DataFrame([r for _, tt in res for r in tt])
    rows.sort_values(["model", "variant", "presentation", "cut", "seed", "slice"]).to_csv(
        OUT / "ablation_signals.csv", index=False, float_format="%.6f")
    tun.to_csv(OUT / "ablation_tuning.csv", index=False, float_format="%.6f")
    meta = {"wall_seconds": round(time.time() - t0, 1), "cpu_seconds": float(tun["seconds"].sum()
                                                                             + rows.drop_duplicates(["model", "variant", "presentation", "cut", "seed"])["fit_score_seconds"].sum()),
            "workers": a.workers, "date": time.strftime("%Y-%m-%d %H:%M:%S")}
    (OUT / "ablation_meta.json").write_text(json.dumps(meta, indent=2))
    print(f"[ablation] finished in {meta['wall_seconds'] / 60:.1f} min", flush=True)


if __name__ == "__main__":
    main()
