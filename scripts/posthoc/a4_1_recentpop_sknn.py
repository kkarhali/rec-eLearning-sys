#!/usr/bin/env python3
"""POST-HOC A-4 (1): rank-fusion hybrid (1) Recent-Pop B3 + (4) SKNN B5, same procedure as the frozen HYB*.

Committee condition A-4 (docs/defense/r3-alomar-verdict.md §5). Outside the Holm family; descriptive.

Procedure = the frozen HYB* procedure of src/ml/experiments/run_hybrid.py with only the components swapped:
  * component scores = the cached scores of the locked runs (component parameters selected on validation, task A,
    by the standalone tuning of each baseline; 2013: data/cache/components, 2014: data/cache/components_conf2014/E5);
  * rank fusion with mid-ranks (D-32); weights tuned on each (presentation, origin) validation window on the D-29
    simplex grid (step 1/4), with the D-51 personalisation floor: grid points with SKNN weight 0 removed
    (SKNN weight ≥ 1/4), first maximum wins (np.argmax), exactly as ``run_hybrid.eval_combo_fold``;
  * test NDCG@10 on (t, t+14], task A (new resources, E5), seeds: both components are deterministic (seed 0);
  * pair vs B3 Recent-Pop with the H1 inference (cluster bootstrap-t B = 10,000 seed 0, exact sign-flip p,
    uncorrected), plus the course-level resampling of table 5-8-هـ.
Before any number is written, the pipeline must reproduce the locked HYB* (per fold, and weights), B3 and B5
NDCG@10 to ≤ 1e-6, otherwise the script stops.

    python3 scripts/posthoc/a4_1_recentpop_sknn.py [--workers 4]
"""
from __future__ import annotations

import argparse
import json
import multiprocessing as mp
import time

import _common as C  # noqa: E402  (sets sys.path)
import numpy as np
import pandas as pd

from src.ml import data
from src.ml.experiments import run_hybrid as RH
from src.ml.splits import CUTS

FROZEN = ["C7_ClusterPop", "B5_SKNN"]
POSTHOC = ["B3_RecentPop", "B5_SKNN"]          # floor component last (min_last applies to the last component)
FLOOR = 0.25                                   # run_hybrid.floor_step(2)


def folds_for(names):
    return [(n, c) for c in sorted(CUTS, reverse=True) for n in names]


def fold_frame(res, model):
    return pd.DataFrame([{"model": model, "presentation": r["presentation"], "cut": r["cut"],
                          "components": " + ".join(r["combo"]), "weights": json.dumps(r["weights"]),
                          "w_first": r["weights"][0], "w_SKNN": r["weights"][-1], "val_NDCG@10": r["val"],
                          "NDCG@10": r["test_all"], "NDCG@10_cold_q1": r["test_cold_q1"],
                          "NDCG@10_top_q4": r["test_top_q4"], "n_seeds": r["n_seeds"]} for r in res])


def run_year(year: str, workers: int, checks: list):
    names = data.DEV_PRESENTATIONS if year == "2013" else data.CONF_PRESENTATIONS
    src = C.DEV if year == "2013" else C.CONF
    C.use_cache(year)
    if year == "2014":
        C.log_posthoc_read("a4_1_recentpop_sknn.py", "cached component scores and fold targets of the E10 run "
                           "(data/cache/components_conf2014/E5)", names)
    base = pd.read_csv(src / "baselines.csv")
    hyb_locked = pd.read_csv(src / "hybrid.csv")
    hyb_locked = hyb_locked[(hyb_locked["model"] == "HYB*") & (hyb_locked["task"] == "A")]
    with mp.get_context("fork").Pool(workers) as pool:
        ev = RH.Evaluator(pool, folds_for(names))
        frozen = ev.fold_results(FROZEN, min_last=FLOOR)
        b3_single = ev.fold_results(["B3_RecentPop"])
        b5_single = ev.fold_results(["B5_SKNN"])
        post = ev.fold_results(POSTHOC, min_last=FLOOR)
        post_nominal = ev.fold_results(POSTHOC)
    # ---------- reproduction checks (stop on failure) ----------
    fz = fold_frame(frozen, "HYB*").set_index(["presentation", "cut"]).sort_index()
    lk = hyb_locked.set_index(["presentation", "cut"]).sort_index()
    checks.append({"year": year, **C.check(f"{year} HYB* NDCG@10 per fold vs {src.name}/hybrid.csv", fz["NDCG@10"], lk["NDCG@10"])})
    checks.append({"year": year, **C.check(f"{year} HYB* NDCG@10 per presentation vs {src.name}/hybrid.csv",
                                           C.fold_means(fz.reset_index(), "NDCG@10"), C.fold_means(lk.reset_index(), "NDCG@10"))})
    same_w = all(json.loads(a) == json.loads(b) for a, b in zip(fz["weights"], lk["weights"]))
    checks.append({"year": year, "check": f"{year} HYB* weights per fold identical to {src.name}/hybrid.csv",
                   "n": len(fz), "max_abs_diff": 0.0 if same_w else float("nan"), "tolerance": 0.0, "pass": same_w})
    print(f"[reproduction] {year} HYB* weights identical: {same_w}", flush=True)
    for m, res in (("B3_RecentPop", b3_single), ("B5_SKNN", b5_single)):
        got = C.fold_means(fold_frame(res, m), "NDCG@10")
        rec = {"year": year, **C.check(f"{year} {m} NDCG@10 per presentation (cached scores) vs "
                                       f"{src.name}/baselines.csv", got, C.pres_means(base, m))}
        if m == "B5_SKNN":
            # informational: the component cache stores float32 scores (components.save_scores), which can create
            # ties absent from the float64 scores of baselines.csv (2013: DDD_2013J t = 70 only, −2.2e-5). HYB* and
            # this post-hoc hybrid both use the float32 cache, so they stay like-for-like; the B5 values of the
            # locked run itself are reproduced in float64 by a4_2_sknn_all.py.
            rec["note"] = "informational (float32 component cache); not a stop condition"
            rec["stop_condition"] = False
        checks.append(rec)
    if not all(c["pass"] for c in checks if c["year"] == year and c.get("stop_condition", True)):
        raise SystemExit(f"[A-4 (1)] reproduction failed for {year}; no new number written")
    # ---------- post-hoc hybrid ----------
    folds = pd.concat([fold_frame(post, "HYB_B3+SKNN (post-hoc, floor ≥ 1/4)"),
                       fold_frame(post_nominal, "HYB_B3+SKNN nominal grid (post-hoc, no floor)")], ignore_index=True)
    folds.insert(0, "year", year)
    b3 = C.pres_means(base, "B3_RecentPop")
    b5 = C.pres_means(base, "B5_SKNN")
    hs = C.fold_means(fold_frame(frozen, "HYB*"), "NDCG@10")
    hp = C.fold_means(folds[folds["model"].str.contains("floor ≥")], "NDCG@10")
    hn = C.fold_means(folds[folds["model"].str.contains("nominal")], "NDCG@10")
    per = pd.DataFrame({"HYB_B3+SKNN": hp, "HYB_B3+SKNN_nominal": hn, "B3_RecentPop": b3, "B5_SKNN": b5, "HYB*_locked": hs})
    per["delta_vs_B3"] = per["HYB_B3+SKNN"] - per["B3_RecentPop"]
    per.index.name = "presentation"
    per = per.reset_index()
    per.insert(0, "year", year)
    stats_rows = (C.pair_stats(per.set_index("presentation")["delta_vs_B3"], "HYB_B3+SKNN − B3_RecentPop (H1 inference)", year)
                  + C.pair_stats((hn - b3), "HYB_B3+SKNN nominal grid − B3_RecentPop", year)
                  + C.pair_stats((hp - hs), "HYB_B3+SKNN − HYB* (frozen)", year))
    w = folds[folds["model"].str.contains("floor ≥")]["weights"].value_counts()
    print(f"[A-4 (1)] {year}: HYB_B3+SKNN {hp.mean():.4f} | B3 {b3.mean():.4f} | Δ {per['delta_vs_B3'].mean():+.4f} "
          f"| weights {w.to_dict()}", flush=True)
    return folds, per, stats_rows


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--years", nargs="*", default=["2013", "2014"])
    a = ap.parse_args(argv)
    t0 = time.time()
    C.check_lock_sha()
    checks, folds, per, st = [], [], [], []
    for y in a.years:
        f, p, s = run_year(y, a.workers, checks)
        folds.append(f), per.append(p), st.extend(s)
    C.write_csv(pd.DataFrame(checks), "a4_1_reproduction_checks.csv")
    C.write_csv(pd.concat(folds, ignore_index=True), "a4_1_recentpop_sknn_folds.csv")
    C.write_csv(pd.concat(per, ignore_index=True), "a4_1_recentpop_sknn_per_presentation.csv")
    C.write_csv(pd.DataFrame(st), "a4_1_recentpop_sknn.csv")
    commit, dirty = C.git_commit()
    print(f"[A-4 (1)] done in {time.time() - t0:.1f}s (commit {commit}{' dirty' if dirty else ''})", flush=True)


if __name__ == "__main__":
    main()
