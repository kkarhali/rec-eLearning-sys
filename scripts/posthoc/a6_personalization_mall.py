#!/usr/bin/env python3
"""POST-HOC (session 2, م-ع-4 item 2; question ع-2): the "personalisation gain" with SKNN(M = all).

The D-60 decomposition (table 5-13 on 2013, table 5-20-a on 2014) attributes "(c) HYB* − (7) alone" to
personalisation. HYB*'s personal component is B5 SKNN restricted to the most recent M = 1000 (registration, week)
baskets of the other learners. Here that component is replaced by SKNN with M = None (all peer baskets), every
other step of the frozen HYB* procedure unchanged:
  * SKNN(M = all) configuration per (presentation, origin) = the one selected by a4_2_sknn_all.py (M fixed to None,
    the other parameters tuned on validation, task A, with the same 20-setting budget rule), read from
    results/posthoc/a4_2_sknn_all_rows.csv; its scores are recomputed here (tune phase: fit on ≤ t−14; test
    phase: fit on ≤ t) and stored, like every component of the locked runs, as float32 in a separate cache
    (data/cache/posthoc_components_mall/<year>/; the other components are symlinks to the locked caches);
  * run_hybrid.eval_combo_fold unchanged: mid-rank fusion (D-32), simplex grid step 1/4 (D-29), weights tuned on
    each validation window, first maximum, D-51 floor on the last component (SKNN weight ≥ 1/4), 5 seeds for (7).
Pairs (cluster bootstrap-t B = 10,000 seed 0, exact sign-flip p uncorrected; presentation and course level):
  HYB_Mall − (7) alone [the analogue of row (c)], HYB_Mall − non-personal hybrid (1)+(6) [row (a)],
  HYB_Mall − B3 [the H1 pair], HYB_Mall nominal grid − B3 [row (d)], HYB_Mall − HYB*, and the a4_1 analogue
  (1) B3 + SKNN(M = all) with the floor − B3; the locked rows (a)–(d) are recomputed at course level for context.

Stop conditions (before any number is written): the recomputed SKNN(M = all) validation and test NDCG@10 per fold
reproduce a4_2_sknn_all_rows.csv (≤ 1e-6, float64 scores); through the symlinked cache HYB* reproduces hybrid.csv
per fold (NDCG@10, validation, weights) and the four decomposition rows reproduce h1_decomposition.csv (≤ 1e-6).

    python3 scripts/posthoc/a6_personalization_mall.py [--workers 4] [--years 2013 2014]
"""
from __future__ import annotations

import argparse
import multiprocessing as mp
import os
import time

from _s2 import (C, DEC_LABELS, FLOOR, FROZEN, NONPERSONAL, check_decomposition, check_hybrid_folds,
                 check_locked_files, decomposition, fold_frame, folds_for, log_read, np, pd, per_pres, require,
                 weight_counts)
from src.ml import components as CP, data
from src.ml.experiments import run_hybrid as RH
from src.ml.harness import _val_score, eval_rows
from src.ml.models import SKNN
from src.ml.splits import make_fold

MALL = "B5_SKNN_Mall"
HYB_MALL = ["C7_ClusterPop", MALL]
B3_MALL = ["B3_RecentPop", MALL]
A42_LABEL = "B5_SKNN_Mall (post-hoc, M = None)"
CACHE_ROOT = data.CACHE_DIR / "posthoc_components_mall"
_PRES: dict = {}
_CFG: dict = {}


def link_cache(year: str, names) -> None:
    """data/cache/posthoc_components_mall/<year>/<fold>/: symlinks to the locked cache files of the fold."""
    src_root = C.CACHE_DEV if year == "2013" else C.CACHE_CONF
    for n, c in folds_for(names):
        src, dst = src_root / f"{n}_{c}", CACHE_ROOT / year / f"{n}_{c}"
        dst.mkdir(parents=True, exist_ok=True)
        for f in src.iterdir():
            t = dst / f.name
            if not t.exists():
                os.symlink(f.resolve(), t)


def score_job(args):
    """SKNN(M = all) with the a4_2 configuration: float64 validation / test NDCG@10, then cached as float32."""
    name, cut = args
    t0 = time.time()
    p, cfg = _PRES[name], CP.parse_config(_CFG[(name, cut)])
    tr, tg = make_fold(p, cut, "tune", "E5")
    S = SKNN(seed=0, **cfg).fit(tr).score()
    val = _val_score(S, tg.task("A"), tr.tiebreak)
    CP.save_scores(name, cut, MALL, "tune", 0, S)
    tr2, tg2 = make_fold(p, cut, "test", "E5")
    S2 = SKNN(seed=0, **cfg).fit(tr2).score()
    row = [r for r in eval_rows(name, cut, MALL, "A", -1, _CFG[(name, cut)], val, S2, tg2.task("A"), tr2)
           if r["slice"] == "all"][0]
    CP.save_scores(name, cut, MALL, "test", 0, S2)
    S32 = CP.load_scores(name, cut, MALL, "test", 0)
    row32 = [r for r in eval_rows(name, cut, MALL, "A", -1, _CFG[(name, cut)], val, S32, tg2.task("A"), tr2)
             if r["slice"] == "all"][0]
    print(f"[a6] SKNN(M=all) scores {name} t={cut} ({time.time() - t0:.0f}s)", flush=True)
    return {"presentation": name, "cut": cut, "config": _CFG[(name, cut)], "val": val, "test": row["NDCG@10"],
            "test_float32_cache": row32["NDCG@10"]}


def run_year(year: str, workers: int, checks: list):
    names = data.DEV_PRESENTATIONS if year == "2013" else data.CONF_PRESENTATIONS
    src = C.DEV if year == "2013" else C.CONF
    if year == "2014":
        checks += check_locked_files(["baselines.csv", "hybrid.csv", "h1_decomposition.csv"])
    # ---------- SKNN(M = all) component scores ----------
    a42 = pd.read_csv(C.OUT / "a4_2_sknn_all_rows.csv")
    a42 = a42[(a42["year"] == int(year)) & (a42["model"] == A42_LABEL) & (a42["slice"] == "all")]
    a42 = a42.set_index(["presentation", "cut"]).sort_index()
    _CFG.clear()
    _CFG.update({k: v for k, v in a42["config"].items()})
    _PRES.clear()
    if year == "2013":
        _PRES.update(data.load_dev_presentations(names))
    else:
        log_read("a6_personalization_mall.py", "daily VLE events, vle, assessments, courses, registrations and "
                 "studentInfo without sensitive columns (data.load_presentation) for SKNN(M = all) refits; cached "
                 "component scores and fold targets of the E10 run (data/cache/components_conf2014/E5)", names)
        ev_ = data.load_daily_events("conf", allow_confirmatory=True)
        _PRES.update({n: data.load_presentation(n, events=ev_, allow_confirmatory=True) for n in names})
    link_cache(year, names)
    CP.COMP_DIR = CACHE_ROOT / year
    with mp.get_context("fork").Pool(workers) as pool:
        sc = pd.DataFrame(pool.map(score_job, folds_for(names), chunksize=1)).set_index(["presentation", "cut"]).sort_index()
    checks.append({"year": year, **C.check(f"{year} SKNN(M = all) validation NDCG@10 per fold vs a4_2_sknn_all_rows.csv",
                                           sc["val"], a42["val_NDCG@10"])})
    checks.append({"year": year, **C.check(f"{year} SKNN(M = all) test NDCG@10 per fold vs a4_2_sknn_all_rows.csv",
                                           sc["test"], a42["NDCG@10"])})
    rec = {"year": year, **C.check(f"{year} SKNN(M = all) test NDCG@10 per fold from the float32 cache vs "
                                   "a4_2_sknn_all_rows.csv", sc["test_float32_cache"], a42["NDCG@10"])}
    rec.update(note="informational (float32 component cache, as every component of HYB*); not a stop condition",
               stop_condition=False)
    checks.append(rec)
    # ---------- hybrids (run_hybrid code path, symlinked cache) ----------
    base = pd.read_csv(src / "baselines.csv")
    bnp = C.pres_means(base, "B3_RecentPop")
    with mp.get_context("fork").Pool(workers) as pool:
        ev = RH.Evaluator(pool, folds_for(names))
        final = ev.fold_results(FROZEN, min_last=FLOOR)
        nominal = ev.fold_results(FROZEN)
        c7 = ev.fold_results(["C7_ClusterPop"])
        nph = ev.fold_results(NONPERSONAL)
        mall_single = ev.fold_results([MALL])
        hm = ev.fold_results(HYB_MALL, min_last=FLOOR)
        hm_nom = ev.fold_results(HYB_MALL)
        b3m = ev.fold_results(B3_MALL, min_last=FLOOR)
    checks += check_hybrid_folds(year, final, src)
    dec = decomposition(final, nominal, c7, nph, bnp)
    checks += check_decomposition(year, dec, src)
    require(checks, year, "a6")
    # ---------- post-hoc numbers ----------
    folds = pd.concat([fold_frame(hm, "HYB_Mall = (7) + SKNN(M = all) (floor ≥ 1/4)", year),
                       fold_frame(hm_nom, "HYB_Mall nominal grid (no floor)", year),
                       fold_frame(b3m, "HYB_B3+SKNN(M = all) (floor ≥ 1/4)", year),
                       fold_frame(mall_single, "SKNN(M = all) alone (float32 cache)", year),
                       fold_frame(final, "HYB* (reproduced)", year)], ignore_index=True)
    folds["status"] = C.POSTHOC_NOTE
    per = pd.DataFrame({"HYB_Mall": per_pres(hm), "HYB_Mall_nominal": per_pres(hm_nom), "HYB_B3+SKNN_Mall": per_pres(b3m),
                        "SKNN_Mall_alone": per_pres(mall_single), "C7_alone": per_pres(c7),
                        "nonpersonal_hybrid": per_pres(nph), "B3_RecentPop_locked": bnp, "HYB*": per_pres(final)})
    per.index.name = "presentation"
    pairs = [("HYB_Mall − (7) alone [personalisation gain, analogue of row (c)]", per["HYB_Mall"] - per["C7_alone"]),
             ("HYB_Mall − non-personal hybrid (1)+(6) [analogue of row (a)]", per["HYB_Mall"] - per["nonpersonal_hybrid"]),
             ("HYB_Mall − B3_RecentPop [H1 pair]", per["HYB_Mall"] - per["B3_RecentPop_locked"]),
             ("HYB_Mall nominal grid − B3_RecentPop [analogue of row (d)]", per["HYB_Mall_nominal"] - per["B3_RecentPop_locked"]),
             ("HYB_Mall − HYB* (frozen, M = 1000)", per["HYB_Mall"] - per["HYB*"]),
             ("HYB_B3+SKNN(M = all) − B3_RecentPop [analogue of a4_1]", per["HYB_B3+SKNN_Mall"] - per["B3_RecentPop_locked"])]
    st = []
    for label, d in pairs:
        st += C.pair_stats(d, label, year, kind="post-hoc (SKNN M = all)")
    ref = [(DEC_LABELS[0], per["HYB*"] - per["nonpersonal_hybrid"]), (DEC_LABELS[1], per["C7_alone"] - per["B3_RecentPop_locked"]),
           (DEC_LABELS[2], per["HYB*"] - per["C7_alone"]), (DEC_LABELS[3], per_pres(nominal) - per["B3_RecentPop_locked"])]
    for label, d in ref:
        st += C.pair_stats(d, "locked " + label, year, kind="reference (locked rows recomputed; presentation level = h1_decomposition.csv)")
    per = per.reset_index()
    per.insert(0, "year", year)
    w = weight_counts(folds[folds["model"].str.startswith("HYB_Mall = ")])
    wb = weight_counts(folds[folds["model"].str.startswith("HYB_B3+")])
    print(f"[a6] {year}: HYB_Mall {per['HYB_Mall'].mean():.4f} | (7) {per['C7_alone'].mean():.4f} | B3 "
          f"{per['B3_RecentPop_locked'].mean():.4f} | HYB* {per['HYB*'].mean():.4f} | weights (C7, SKNN_Mall) {w} | "
          f"B3+SKNN_Mall weights {wb}", flush=True)
    wrows = [{"year": year, "model": "HYB_Mall = (7) + SKNN(M = all) (floor ≥ 1/4)", "weights": k, "n_folds": v} for k, v in w.items()]
    wrows += [{"year": year, "model": "HYB_B3+SKNN(M = all) (floor ≥ 1/4)", "weights": k, "n_folds": v} for k, v in wb.items()]
    return folds, per, st, wrows


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--years", nargs="*", default=["2013", "2014"])
    a = ap.parse_args(argv)
    t0 = time.time()
    C.check_lock_sha()
    checks, folds, per, st, wr = [], [], [], [], []
    for y in a.years:
        f, p, s, w = run_year(y, a.workers, checks)
        folds.append(f), per.append(p), st.extend(s), wr.extend(w)
    tag = "" if a.years == ["2013", "2014"] else "_" + "_".join(a.years)
    C.write_csv(pd.DataFrame(checks), f"a6_reproduction_checks{tag}.csv")
    C.write_csv(pd.concat(folds, ignore_index=True), f"a6_personalization_mall_folds{tag}.csv")
    C.write_csv(pd.concat(per, ignore_index=True), f"a6_personalization_mall_per_presentation{tag}.csv")
    C.write_csv(pd.DataFrame(st), f"a6_personalization_mall{tag}.csv")
    C.write_csv(pd.DataFrame(wr), f"a6_personalization_mall_weights{tag}.csv")
    commit, dirty = C.git_commit()
    print(f"[a6] done in {(time.time() - t0) / 60:.1f} min (commit {commit}{' dirty' if dirty else ''})", flush=True)


if __name__ == "__main__":
    main()
