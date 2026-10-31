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

Exact zeros (session 3, round 1, د. الكنج, problem 1): B3 is read from the locked baselines.csv (6 decimals) and
the hybrids are computed in the session. Where the nominal grid gives SKNN weight 0 in every fold of a presentation,
the hybrid IS B3 and the difference is a rounding residue (< 5e-7), which the first version counted as positive and
used to break the sign-flip ties. Every difference is now passed through ``_common.snap_zero`` (|d| ≤ 1e-6 → 0,
the a5 convention), and the summary rows carry n_zero and n_neg.

``--from-csv`` recomputes only the summary rows (a4_1_recentpop_sknn.csv) from the committed per-presentation file,
without refitting and without reading any 2014 cache (so no access-log line, as a12): it first checks that every
per-presentation column is reproduced within 1e-6 from the committed fold file and the locked baselines.csv and
hybrid.csv, and that the summary rows not touched by exact zeros match the committed summary within 1e-6;
otherwise it stops. Its checks go to a4_1_from_csv_checks.csv.

    python3 scripts/posthoc/a4_1_recentpop_sknn.py [--workers 4]
    python3 scripts/posthoc/a4_1_recentpop_sknn.py --from-csv
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


LABELS = {"floor": "HYB_B3+SKNN − B3_RecentPop (H1 inference)",
          "nominal": "HYB_B3+SKNN nominal grid − B3_RecentPop",
          "frozen": "HYB_B3+SKNN − HYB* (frozen)"}


def summary_rows(per: pd.DataFrame, year: str) -> list[dict]:
    """The three paired comparisons of table هـ-1 from the per-presentation means (index = presentation).
    Each difference goes through snap_zero: B3 comes from a 6-decimal locked file (see module docstring)."""
    hp, hn, b3, hs = (per[k] for k in ("HYB_B3+SKNN", "HYB_B3+SKNN_nominal", "B3_RecentPop", "HYB*_locked"))
    return (C.pair_stats(C.snap_zero(hp - b3), LABELS["floor"], year)
            + C.pair_stats(C.snap_zero(hn - b3), LABELS["nominal"], year)
            + C.pair_stats(C.snap_zero(hp - hs), LABELS["frozen"], year))


def from_csv(years) -> None:
    """Recompute the summary rows from the committed per-presentation file (no refit, no 2014 cache read)."""
    per_all = pd.read_csv(C.OUT / "a4_1_recentpop_sknn_per_presentation.csv")
    folds_all = pd.read_csv(C.OUT / "a4_1_recentpop_sknn_folds.csv")
    old = pd.read_csv(C.OUT / "a4_1_recentpop_sknn.csv")
    checks, rows = [], []
    for year in years:
        src = C.DEV if year == "2013" else C.CONF
        base = pd.read_csv(src / "baselines.csv")
        hl = pd.read_csv(src / "hybrid.csv")
        hl = hl[(hl["model"] == "HYB*") & (hl["task"] == "A")]
        per = per_all[per_all["year"] == int(year)].set_index("presentation").sort_index()
        f = folds_all[folds_all["year"] == int(year)]
        refs = [("HYB_B3+SKNN", C.fold_means(f[f["model"].str.contains("floor ≥")], "NDCG@10"), "fold file (floor)"),
                ("HYB_B3+SKNN_nominal", C.fold_means(f[f["model"].str.contains("nominal")], "NDCG@10"), "fold file (nominal)"),
                ("B3_RecentPop", C.pres_means(base, "B3_RecentPop"), f"{src.name}/baselines.csv"),
                ("B5_SKNN", C.pres_means(base, "B5_SKNN"), f"{src.name}/baselines.csv"),
                ("HYB*_locked", C.fold_means(hl, "NDCG@10"), f"{src.name}/hybrid.csv"),
                ("delta_vs_B3", per["HYB_B3+SKNN"] - per["B3_RecentPop"], "HYB_B3+SKNN − B3_RecentPop of the same file")]
        for col, ref, what in refs:
            # delta_vs_B3 is the difference of two 6-decimal columns, stored with 6 decimals: three roundings of
            # ≤ 5e-7 each, hence the wider tolerance for this derived column only
            tol = 3 * C.TOL / 2 if col == "delta_vs_B3" else C.TOL
            checks.append({"year": year, **C.check(f"{year} per-presentation {col} vs {what}", per[col], ref, tol)})
        rows += summary_rows(per, year)
    new = pd.DataFrame(rows)
    # the rows without exact zeros must be the committed ones (the CSV rounding of the inputs moves them < 1e-6)
    for _, r in new.iterrows():
        o = old[(old["comparison"] == r["comparison"]) & (old["year"] == int(r["year"])) & (old["unit"] == r["unit"])].iloc[0]
        if r["n_zero"] == 0:
            d = max(abs(r[k] - o[k]) for k in ("mean", "ci_lo", "ci_hi", "p_signflip_uncorrected"))
            same_pos = int(r["n_pos"]) == int(o["n_pos"])
            checks.append({"year": r["year"], "check": f"{r['year']} {r['comparison']} [{r['unit'][:6]}]: mean, CI, p, "
                           "n_pos = committed summary (no exact zero)", "n": 1, "max_abs_diff": d,
                           "tolerance": C.TOL, "pass": bool(d <= C.TOL and same_pos)})
        print(f"[a4_1 --from-csv] {r['year']} {r['comparison'][:44]:44s} {r['unit'][:12]:12s} mean {r['mean']:+.6f} "
              f"p {o['p_signflip_uncorrected']:.6f} -> {r['p_signflip_uncorrected']:.6f} | n_pos {int(o['n_pos'])} -> "
              f"{int(r['n_pos'])}, zero {int(r['n_zero'])}, neg {int(r['n_neg'])}", flush=True)
    ck = pd.DataFrame(checks)
    C.write_csv(ck, "a4_1_from_csv_checks.csv")
    if not ck["pass"].all():
        print(ck[~ck["pass"]].to_string())
        raise SystemExit("[a4_1 --from-csv] reproduction failed; no new number written")
    C.write_csv(new, "a4_1_recentpop_sknn.csv")


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
    per["delta_vs_B3"] = C.snap_zero(per["HYB_B3+SKNN"] - per["B3_RecentPop"])
    per.index.name = "presentation"
    stats_rows = summary_rows(per, year)
    per = per.reset_index()
    per.insert(0, "year", year)
    w = folds[folds["model"].str.contains("floor ≥")]["weights"].value_counts()
    print(f"[A-4 (1)] {year}: HYB_B3+SKNN {hp.mean():.4f} | B3 {b3.mean():.4f} | Δ {per['delta_vs_B3'].mean():+.4f} "
          f"| weights {w.to_dict()}", flush=True)
    return folds, per, stats_rows


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--years", nargs="*", default=["2013", "2014"])
    ap.add_argument("--from-csv", action="store_true",
                    help="recompute the summary rows from the committed per-presentation file (no refit)")
    a = ap.parse_args(argv)
    t0 = time.time()
    C.check_lock_sha()
    if a.from_csv:
        from_csv(a.years)
        commit, dirty = C.git_commit()
        print(f"[A-4 (1)] --from-csv done in {time.time() - t0:.1f}s (commit {commit}{' dirty' if dirty else ''})", flush=True)
        return
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
