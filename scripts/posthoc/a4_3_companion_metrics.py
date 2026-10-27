#!/usr/bin/env python3
"""POST-HOC A-4 (3): companion metrics of the frozen HYB* on task A (HR@10, MRR@10, Coverage@10, PopBias@10).

Committee condition A-4 (docs/defense/r3-alomar-verdict.md §5). Outside the Holm family; descriptive.

HYB* is NOT re-tuned: the weights are those chosen in the locked runs, read from results/conf2014/hybrid_2014.json
(2014) and results/dev2013/hybrid_frozen.json (2013 test windows, for comparison); component scores are the cached
scores of the same runs (5 seeds for the stochastic (7) cluster popularity). Metrics are computed with
``src.ml.metrics.evaluate`` exactly as the baselines' companion metrics in ``harness.run_job``: full catalogue,
task-A candidates (unseen items), the fixed tie-break keys, popularity percentile of the test-phase training
popularity (PopBias), coverage = distinct recommended items / catalogue size. Aggregation as the unit of analysis:
seeds → origins → presentation → mean over presentations.

Like-for-like check (stop condition): the same pipeline applied to B3 Recent-Pop's cached scores must reproduce
B3's locked NDCG@10, HR@10, MRR@10, Coverage@10 and PopBias@10 in baselines.csv (per fold, ≤ 1e-6), and HYB*'s
NDCG@10 must reproduce hybrid.csv (per fold, ≤ 1e-6).

    python3 scripts/posthoc/a4_3_companion_metrics.py
"""
from __future__ import annotations

import argparse
import json
import time

import _common as C  # noqa: E402  (sets sys.path)
import numpy as np
import pandas as pd

from src.ml import components as CP, data, hybrid, metrics
from src.ml.experiments import run_hybrid as RH
from src.ml.harness import SEEDS
from src.ml.splits import CUTS

METRICS = ["NDCG@10", "HR@10", "MRR@10", "P@10", "R@10", "Coverage@10", "PopBias@10"]
REF_MODELS = ["B3_RecentPop", "B5_SKNN", "B2_Pop", "B7_WRMF"]


def companion(S, F) -> dict:
    ev = F["ev"].astype(bool)
    res = metrics.evaluate(S, F["cand"], F["tgt"], F["unreach"], ev, F["tiebreak"], ks=(10,), pop=F["pop"])
    row = metrics.summarize(res)
    row["Coverage@10"] = res["coverage"][10]
    row["PopBias@10"] = res["popbias"][10]
    row["n_eval"] = res["n_eval"]
    return row


def hyb_scores(name, cut, combo, w, seed, F):
    """Fused HYB* scores on the full U×I grid (rows outside the evaluated learners stay 0 and are not evaluated)."""
    ev = F["ev"].astype(bool)
    rt = [RH._rt(name, cut, c, "test", seed, F) for c in combo]
    S = np.zeros(F["cand"].shape)
    S[ev] = hybrid.fuse(rt, np.asarray(w, dtype=float))
    return S


def run_year(year: str, checks: list):
    names = data.DEV_PRESENTATIONS if year == "2013" else data.CONF_PRESENTATIONS
    src = C.DEV if year == "2013" else C.CONF
    C.use_cache(year)
    if year == "2014":
        C.log_posthoc_read("a4_3_companion_metrics.py", "cached component scores and fold targets of the E10 run "
                           "(data/cache/components_conf2014/E5)", names)
        wj = json.loads((C.CONF / "hybrid_2014.json").read_text())
    else:
        wj = json.loads((C.DEV / "hybrid_frozen.json").read_text())
    combo, wbf = wj["components"], wj["weights_by_fold"]
    base = pd.read_csv(src / "baselines.csv")
    hl = pd.read_csv(src / "hybrid.csv")
    hl = hl[(hl["model"] == "HYB*") & (hl["task"] == "A")].set_index(["presentation", "cut"])
    rows = []
    for name in names:
        for cut in sorted(CUTS):
            F = dict(np.load(RH.fold_dir(name, cut) / "fold_test.npz"))
            w = [wbf[f"{name}_{cut}"][c] for c in combo]
            if json.loads(hl.loc[(name, cut), "weights"]) != w:
                raise SystemExit(f"weights of {name} t={cut} differ between the weight file and hybrid.csv")
            seeds = SEEDS if any(c in RH.STOCHASTIC for c in combo) else SEEDS[:1]
            for s in seeds:
                rows.append({"year": year, "model": "HYB*", "presentation": name, "cut": cut, "seed": s,
                             "weights": json.dumps(w), **companion(hyb_scores(name, cut, combo, w, s, F), F)})
            rows.append({"year": year, "model": "B3_RecentPop (pipeline check)", "presentation": name, "cut": cut,
                         "seed": -1, **companion(CP.load_scores(name, cut, "B3_RecentPop", "test", 0), F)})
    df = pd.DataFrame(rows)
    fold = df.groupby(["model", "presentation", "cut"])[METRICS + ["n_eval"]].mean()
    # ---------- reproduction checks (stop on failure) ----------
    b3 = base[(base["model"] == "B3_RecentPop") & (base["task"] == "A") & (base["slice"] == "all")]
    b3 = b3.set_index(["presentation", "cut"]).sort_index()
    mine = fold.loc["B3_RecentPop (pipeline check)"].sort_index()
    for m in ["NDCG@10", "HR@10", "MRR@10", "Coverage@10", "PopBias@10"]:
        checks.append({"year": year, **C.check(f"{year} B3_RecentPop {m} per fold vs {src.name}/baselines.csv",
                                               mine[m], b3[m])})
    checks.append({"year": year, **C.check(f"{year} B3_RecentPop n_eval per fold vs {src.name}/baselines.csv",
                                           mine["n_eval"].astype(float), b3["n_eval"].astype(float), tol=0)})
    checks.append({"year": year, **C.check(f"{year} HYB* NDCG@10 per fold vs {src.name}/hybrid.csv",
                                           fold.loc["HYB*"]["NDCG@10"].sort_index(), hl["NDCG@10"].sort_index())})
    if not all(c["pass"] for c in checks if c["year"] == year):
        raise SystemExit(f"[A-4 (3)] reproduction failed for {year}; no new number written")
    # ---------- per presentation ----------
    per = []
    for model in fold.index.get_level_values(0).unique():
        g = fold.loc[model].reset_index()
        pm = {m: C.fold_means(g, m) for m in METRICS}
        for p in pm["NDCG@10"].index:
            per.append({"year": year, "model": model, "presentation": p, "source": "post-hoc pipeline",
                        **{m: float(pm[m][p]) for m in METRICS}})
    for model in REF_MODELS:                    # locked values, read as they are (context only)
        pm = {m: C.pres_means(base, model, metric=m) for m in METRICS}
        for p in pm["NDCG@10"].index:
            per.append({"year": year, "model": model, "presentation": p, "source": f"locked {src.name}/baselines.csv",
                        **{m: float(pm[m][p]) for m in METRICS}})
    gru = pd.read_csv(src / "gru.csv")
    pm = {m: C.pres_means(gru, "GRU_lite", metric=m) for m in METRICS if m in gru.columns}
    for p in pm["NDCG@10"].index:
        per.append({"year": year, "model": "GRU_lite", "presentation": p, "source": f"locked {src.name}/gru.csv",
                    **{m: float(pm[m][p]) for m in pm}})
    df.insert(1, "source", "post-hoc pipeline")
    return df, pd.DataFrame(per)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--years", nargs="*", default=["2014", "2013"])
    a = ap.parse_args(argv)
    t0 = time.time()
    C.check_lock_sha()
    checks, folds, per = [], [], []
    for y in a.years:
        f, p = run_year(y, checks)
        folds.append(f), per.append(p)
    per = pd.concat(per, ignore_index=True)
    summ = (per.groupby(["year", "model", "source"])[METRICS].agg(["mean", "std"]))
    summ.columns = [f"{m}_{s}".replace("_mean", "") for m, s in summ.columns]
    summ = summ.reset_index()
    summ["n_presentations"] = per.groupby(["year", "model", "source"]).size().to_numpy()
    summ["status"] = C.POSTHOC_NOTE
    summ = summ.sort_values(["year", "NDCG@10"], ascending=[False, False])
    C.write_csv(pd.DataFrame(checks), "a4_3_reproduction_checks.csv")
    C.write_csv(pd.concat(folds, ignore_index=True), "a4_3_companion_metrics_folds.csv")
    C.write_csv(per, "a4_3_companion_metrics_per_presentation.csv")
    C.write_csv(summ, "a4_3_companion_metrics.csv")
    print(summ[["year", "model", "NDCG@10", "HR@10", "MRR@10", "Coverage@10", "PopBias@10"]].to_string(index=False))
    commit, dirty = C.git_commit()
    print(f"[A-4 (3)] done in {time.time() - t0:.1f}s (commit {commit}{' dirty' if dirty else ''})", flush=True)


if __name__ == "__main__":
    main()
