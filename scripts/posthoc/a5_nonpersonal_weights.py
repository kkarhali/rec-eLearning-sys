#!/usr/bin/env python3
"""POST-HOC (session 2, م-ع-3 item 3): weights of the non-personal hybrid (1) Recent-Pop + (6) assessment proximity.

The D-60 decomposition of H1 (table 5-13 on the 2013 test windows; table 5-20-a on 2014) has a row
"(a) HYB* − non-personal hybrid (1)+(6)". run_hybrid.frozen_analyses tunes that control's weights on each
(presentation, origin) validation window but never writes them. This tool re-runs the same code path
(run_hybrid.Evaluator.fold_results(["B3_RecentPop", "C6_AssessProx"]) on the cached component scores of the locked
runs: simplex grid step 1/4, mid-rank fusion, first maximum wins, no floor) and saves the chosen weights.

Stop condition: before anything is written, the four decomposition rows (mean, bootstrap-t CI, percentile CI,
sign-flip p, n_pos) must reproduce results/dev2013/h1_decomposition.csv (2013) and results/conf2014/
h1_decomposition.csv (2014) to ≤ 1e-6, and HYB* must reproduce hybrid.csv per fold (NDCG@10, validation, weights).

Outside the Holm family; descriptive. Outputs: results/posthoc/a5_nonpersonal_weights*.csv.

    python3 scripts/posthoc/a5_nonpersonal_weights.py [--workers 4] [--years 2013 2014]
"""
from __future__ import annotations

import argparse
import multiprocessing as mp
import time

from _s2 import (C, FLOOR, FROZEN, NONPERSONAL, check_decomposition, check_hybrid_folds, check_locked_files,
                 decomposition, fold_frame, folds_for, log_read, np, pd, per_pres, require, weight_counts)
from src.ml import data
from src.ml.experiments import run_hybrid as RH


def run_year(year: str, workers: int, checks: list):
    names = data.DEV_PRESENTATIONS if year == "2013" else data.CONF_PRESENTATIONS
    src = C.DEV if year == "2013" else C.CONF
    C.use_cache(year)
    if year == "2014":
        checks += check_locked_files(["baselines.csv", "hybrid.csv", "h1_decomposition.csv"])
        log_read("a5_nonpersonal_weights.py", "cached component scores and fold targets of the E10 run "
                 "(data/cache/components_conf2014/E5)", names)
    base = pd.read_csv(src / "baselines.csv")
    bnp = C.pres_means(base, "B3_RecentPop")
    with mp.get_context("fork").Pool(workers) as pool:
        ev = RH.Evaluator(pool, folds_for(names))
        final = ev.fold_results(FROZEN, min_last=FLOOR)
        nominal = ev.fold_results(FROZEN)
        c7 = ev.fold_results(["C7_ClusterPop"])
        nph = ev.fold_results(NONPERSONAL)
    checks += check_hybrid_folds(year, final, src)
    checks += check_decomposition(year, decomposition(final, nominal, c7, nph, bnp), src)
    require(checks, year, "a5")
    # ---------- the non-personal hybrid's weights per (presentation, origin) ----------
    f = fold_frame(nph, "non-personal hybrid (1)+(6) [D-60 control]", year)
    b3f = base[(base["model"] == "B3_RecentPop") & (base["task"] == "A") & (base["slice"] == "all")]
    b3f = b3f.groupby(["presentation", "cut"])["NDCG@10"].mean().rename("B3_RecentPop_NDCG@10_locked")
    f = f.merge(b3f.reset_index(), on=["presentation", "cut"], how="left")
    f["delta_vs_B3"] = f["NDCG@10"] - f["B3_RecentPop_NDCG@10_locked"]
    f["max_abs_delta_le_1e-6"] = f["delta_vs_B3"].abs() <= C.TOL     # (1, 0) folds: control = B3 up to cache noise
    f["status"] = C.POSTHOC_NOTE
    per = pd.DataFrame({"nonpersonal_hybrid": per_pres(nph), "B3_RecentPop_locked": bnp, "HYB*": per_pres(final),
                        "share_folds_w_C6_zero": f.groupby("presentation")["w_C6_AssessProx"].apply(lambda s: float((s == 0).mean()))})
    per["delta_nonpersonal_vs_B3"] = per["nonpersonal_hybrid"] - per["B3_RecentPop_locked"]
    per.index.name = "presentation"
    per = per.reset_index()
    per.insert(0, "year", year)
    # Where every fold of a presentation chose (1, 0) the control IS B3: the difference is float32-cache noise
    # (≤ 1e-6, the reproduction tolerance), so it is set to 0 and no interval is computed (it would be degenerate);
    # a descriptive row per year instead.
    per.loc[per["delta_nonpersonal_vs_B3"].abs() <= C.TOL, "delta_nonpersonal_vs_B3"] = 0.0
    d = per["delta_nonpersonal_vs_B3"]
    st = [{"year": year, "n_presentations": len(per), "n_folds": len(f),
           "n_folds_weight_C6_positive": int((f["w_C6_AssessProx"] > 0).sum()),
           "presentations_with_C6_weight": ";".join(sorted(f.loc[f["w_C6_AssessProx"] > 0, "presentation"].unique())),
           "mean_nonpersonal": float(per["nonpersonal_hybrid"].mean()), "mean_B3_locked": float(bnp.mean()),
           "mean_delta_vs_B3": float(d.mean()), "n_presentations_delta_nonzero": int((d != 0).sum()),
           "min_delta_vs_B3": float(d.min()), "max_delta_vs_B3": float(d.max()), "status": C.POSTHOC_NOTE}]
    wc = weight_counts(f)
    print(f"[a5] {year}: weights (B3, C6) {wc} | non-personal {per['nonpersonal_hybrid'].mean():.4f} vs B3 "
          f"{per['B3_RecentPop_locked'].mean():.4f}", flush=True)
    summ = [{"year": year, "weights_B3_C6": k, "n_folds": v, "n_folds_total": len(f)} for k, v in wc.items()]
    return f, per, st, summ


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--years", nargs="*", default=["2013", "2014"])
    a = ap.parse_args(argv)
    t0 = time.time()
    C.check_lock_sha()
    checks, folds, per, st, summ = [], [], [], [], []
    for y in a.years:
        f, p, s, w = run_year(y, a.workers, checks)
        folds.append(f), per.append(p), st.extend(s), summ.extend(w)
    tag = "" if a.years == ["2013", "2014"] else "_" + "_".join(a.years)
    C.write_csv(pd.DataFrame(checks), f"a5_reproduction_checks{tag}.csv")
    C.write_csv(pd.concat(folds, ignore_index=True), f"a5_nonpersonal_weights{tag}.csv")
    C.write_csv(pd.concat(per, ignore_index=True), f"a5_nonpersonal_weights_per_presentation{tag}.csv")
    C.write_csv(pd.DataFrame(st), f"a5_nonpersonal_weights_summary{tag}.csv")
    C.write_csv(pd.DataFrame(summ), f"a5_nonpersonal_weights_counts{tag}.csv")
    commit, dirty = C.git_commit()
    print(f"[a5] done in {time.time() - t0:.1f}s (commit {commit}{' dirty' if dirty else ''})", flush=True)


if __name__ == "__main__":
    main()
