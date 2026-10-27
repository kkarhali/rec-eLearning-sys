#!/usr/bin/env python3
"""POST-HOC A-4 (2): H3 sensitivity — SKNN without the "most recent M baskets" restriction (M = None = all).

Committee condition A-4 (docs/defense/r3-alomar-verdict.md §5). Outside the Holm family; descriptive.

B5 SKNN's registered space is grid(L ∈ {1,3,7}, k ∈ {50,100,200,500}, M ∈ {1000, 5000, None},
variant ∈ {sknn, vsknn}) = 72 points, of which the budget rule (harness.model_configs → models.sample_space,
≤ 20 settings, fixed seed per model name) samples 20; every locked selection had M = 1000. Here M is fixed to None
(all (registration, week) baskets of the other learners) and the remaining space, grid(L, k, variant) = 24 points,
is sampled by the same rule (sample_space(space, 20, "B5_SKNN")). For every (presentation, origin): tune on
(≤ t−14 | (t−14, t]) by validation NDCG@10 on task A (first maximum wins, as harness.run_job), refit on ≤ t and
evaluate on (t, t+14] (harness.eval_rows; float64 scores, full catalogue). GRU-lite is not retrained: its locked
rows are read from results/conf2014/gru.csv and results/dev2013/gru.csv.

Reproduction (stop condition): the same loop run on the registered 20-setting space must select the locked
configuration with the locked validation NDCG@10 and reproduce B5's locked test NDCG@10 per fold (≤ 1e-6), and
GRU-lite − B5 must reproduce the H3 column of results/conf2014/per_presentation.csv.

    python3 scripts/posthoc/a4_2_sknn_all.py [--workers 4] [--years 2013 2014]
"""
from __future__ import annotations

import argparse
import multiprocessing as mp
import time

import _common as C  # noqa: E402  (sets sys.path)
import numpy as np
import pandas as pd

from src.ml import components as CP, data, stats
from src.ml.harness import BUDGET, _val_score, config_key, eval_rows, model_configs
from src.ml.models import SKNN, sample_space
from src.ml.splits import CUTS, make_fold

REG = model_configs("B5_SKNN")                                                    # registered 20 settings
MALL = sample_space([c for c in SKNN.param_space() if c["M"] is None], BUDGET, "B5_SKNN")   # M = None, 20 of 24
LABEL_REG, LABEL_ALL = "B5_SKNN (registered space, reproduction)", "B5_SKNN_Mall (post-hoc, M = None)"
_PRES: dict = {}


def job(args):
    name, cut = args
    t0 = time.time()
    p = _PRES[name]
    tr, tg = make_fold(p, cut, "tune", "E5")
    vA = tg.task("A")
    tuning, val = [], {}
    for cfg in REG + [c for c in MALL if c not in REG]:
        S = SKNN(seed=0, **cfg).fit(tr).score()
        v = _val_score(S, vA, tr.tiebreak)
        val[config_key(cfg)] = v
        tuning.append({"presentation": name, "cut": cut, "config": config_key(cfg), "val_NDCG@10_A": v,
                       "in_registered_space": cfg in REG, "in_Mall_space": cfg in MALL})

    def pick(space):
        best = None
        for cfg in space:                                   # strict '>' keeps the first maximum (harness.run_job)
            v = val[config_key(cfg)]
            if best is None or (np.isfinite(v) and v > best[0]):
                best = (v, cfg)
        return best

    tr2, tg2 = make_fold(p, cut, "test", "E5")
    view = tg2.task("A")
    rows = []
    for label, space in ((LABEL_REG, REG), (LABEL_ALL, MALL)):
        v, cfg = pick(space)
        t = time.time()
        S = SKNN(seed=0, **cfg).fit(tr2).score()
        rows += eval_rows(name, cut, label, "A", -1, config_key(cfg), v, S, view, tr2, secs=time.time() - t)
    print(f"[A-4 (2)] {name} t={cut} ({time.time() - t0:.0f}s)", flush=True)
    return rows, tuning


def run_year(year: str, workers: int, checks: list):
    names = data.DEV_PRESENTATIONS if year == "2013" else data.CONF_PRESENTATIONS
    src = C.DEV if year == "2013" else C.CONF
    _PRES.clear()
    if year == "2013":
        _PRES.update(data.load_dev_presentations(names))
    else:
        C.log_posthoc_read("a4_2_sknn_all.py", "daily VLE events, vle, assessments, courses, registrations and "
                           "studentInfo without sensitive columns (data.load_presentation) for SKNN refits", names)
        ev = data.load_daily_events("conf", allow_confirmatory=True)
        _PRES.update({n: data.load_presentation(n, events=ev, allow_confirmatory=True) for n in names})
    folds = [(n, c) for c in sorted(CUTS, reverse=True) for n in names]
    with mp.get_context("fork").Pool(workers) as pool:
        res = pool.map(job, folds, chunksize=1)
    rows = pd.DataFrame([r for rr, _ in res for r in rr])
    tuning = pd.DataFrame([t for _, tt in res for t in tt])
    rows.insert(0, "year", year)
    tuning.insert(0, "year", year)
    # ---------- reproduction checks (stop on failure) ----------
    base = pd.read_csv(src / "baselines.csv")
    b5 = base[(base["model"] == "B5_SKNN") & (base["task"] == "A") & (base["slice"] == "all")].set_index(["presentation", "cut"]).sort_index()
    mine = rows[(rows["model"] == LABEL_REG) & (rows["slice"] == "all")].set_index(["presentation", "cut"]).sort_index()
    same_cfg = bool((mine["config"] == b5["config"]).all())
    checks.append({"year": year, "check": f"{year} B5 selected configuration per fold = {src.name}/baselines.csv",
                   "n": len(mine), "max_abs_diff": 0.0 if same_cfg else float("nan"), "tolerance": 0.0, "pass": same_cfg})
    print(f"[reproduction] {year} B5 selected configs identical: {same_cfg}", flush=True)
    checks.append({"year": year, **C.check(f"{year} B5 validation NDCG@10 per fold vs {src.name}/baselines.csv",
                                           mine["val_NDCG@10"], b5["val_NDCG@10"])})
    for m in ("NDCG@10", "HR@10", "MRR@10"):
        checks.append({"year": year, **C.check(f"{year} B5 test {m} per fold vs {src.name}/baselines.csv", mine[m], b5[m])})
    gru = pd.read_csv(src / "gru.csv")
    g = C.pres_means(gru, "GRU_lite")
    s_reg = C.pres_means(rows.assign(model=rows["model"].replace({LABEL_REG: "reg"})), "reg")
    if year == "2014":
        ref = pd.read_csv(C.CONF / "per_presentation.csv", index_col="presentation")["H3"].sort_index()
        checks.append({"year": year, **C.check("2014 GRU_lite − B5 per presentation vs conf2014/per_presentation.csv (H3)",
                                               g - s_reg, ref)})
    else:
        checks.append({"year": year, **C.check("2013 GRU_lite − B5 per presentation vs dev2013 gru.csv − baselines.csv",
                                               g - s_reg, g - C.pres_means(base, "B5_SKNN"))})
    if not all(c["pass"] for c in checks if c["year"] == year):
        raise SystemExit(f"[A-4 (2)] reproduction failed for {year}; no new number written")
    # ---------- post-hoc pair ----------
    s_all = C.pres_means(rows.assign(model=rows["model"].replace({LABEL_ALL: "all"})), "all")
    per = pd.DataFrame({"GRU_lite": g, "B5_SKNN_locked": C.pres_means(base, "B5_SKNN"), "B5_SKNN_Mall": s_all})
    per["H3_locked_delta"] = per["GRU_lite"] - per["B5_SKNN_locked"]
    per["H3_Mall_delta"] = per["GRU_lite"] - per["B5_SKNN_Mall"]
    per.index.name = "presentation"
    per = per.reset_index()
    per.insert(0, "year", year)
    d = per.set_index("presentation")["H3_Mall_delta"]
    st = C.pair_stats(d, "GRU_lite − B5_SKNN_Mall (H3 inference, M = None)", year)
    c0 = st[0]
    st[0]["six_level_reading_illustrative_uncorrected_p"] = stats.verdict_bidirectional(
        c0["mean"], c0["ci_lo"], c0["ci_hi"], c0["p_signflip_uncorrected"])
    st += C.pair_stats(per.set_index("presentation")["B5_SKNN_Mall"] - per.set_index("presentation")["B5_SKNN_locked"],
                       "B5_SKNN_Mall − B5_SKNN (locked, M = 1000)", year)
    gc = gru[(gru["model"] == "GRU_lite") & (gru["task"] == "A") & (gru["slice"] == "all")].groupby(["presentation", "cut"])["NDCG@10"].mean()
    sc = rows[(rows["model"] == LABEL_ALL) & (rows["slice"] == "all")].groupby(["presentation", "cut"])["NDCG@10"].mean()
    for cut, dd in (gc - sc).dropna().groupby(level="cut"):
        st.append({"comparison": "GRU_lite − B5_SKNN_Mall", "year": year, "unit": f"origin t = {cut} alone (descriptive)",
                   "n_units": len(dd), "mean": float(dd.mean()), "n_pos": int((dd > 0).sum()), "status": C.POSTHOC_NOTE})
    sel = rows[(rows["model"] == LABEL_ALL) & (rows["slice"] == "all")]["config"].value_counts()
    print(f"[A-4 (2)] {year}: SKNN(M=all) {s_all.mean():.4f} | SKNN locked {per['B5_SKNN_locked'].mean():.4f} | "
          f"GRU {g.mean():.4f} | Δ(GRU − SKNN_Mall) {d.mean():+.4f} | configs {sel.to_dict()}", flush=True)
    return rows, tuning, per, st


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--years", nargs="*", default=["2013", "2014"])
    a = ap.parse_args(argv)
    t0 = time.time()
    C.check_lock_sha()
    checks, rows, tun, per, st = [], [], [], [], []
    for y in a.years:
        r, t, p, s = run_year(y, a.workers, checks)
        rows.append(r), tun.append(t), per.append(p), st.extend(s)
    tag = "" if a.years == ["2013", "2014"] else "_" + "_".join(a.years)
    C.write_csv(pd.DataFrame(checks), f"a4_2_reproduction_checks{tag}.csv")
    C.write_csv(pd.concat(rows, ignore_index=True), f"a4_2_sknn_all_rows{tag}.csv")
    C.write_csv(pd.concat(tun, ignore_index=True), f"a4_2_sknn_all_tuning{tag}.csv")
    C.write_csv(pd.concat(per, ignore_index=True), f"a4_2_sknn_all_per_presentation{tag}.csv")
    C.write_csv(pd.DataFrame(st), f"a4_2_sknn_all{tag}.csv")
    commit, dirty = C.git_commit()
    print(f"[A-4 (2)] done in {(time.time() - t0) / 60:.1f} min (commit {commit}{' dirty' if dirty else ''})", flush=True)


if __name__ == "__main__":
    main()
