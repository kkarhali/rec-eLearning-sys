#!/usr/bin/env python3
"""POST-HOC (session 2, م-ك-2 item 1): leave-one-presentation-out estimate of the hybrid SELECTION PROCEDURE, 2013.

The frozen HYB* was selected and its development difference (+0.0196 vs B3) estimated on the same nine 2013 test
windows (selection-optimistic, ch5 5-7-3). Here the whole selection procedure of run_hybrid.main is repeated nine
times on eight development presentations, and the combination it selects is evaluated on the ninth:
  * S* (best sequential among B5 SKNN, B6 Markov, GRU-lite) and B_np* (best of B1, B2, B3) are re-chosen on the eight
    from the locked dev2013 rows (as run_hybrid.main does on nine);
  * hybrid.greedy_forward unchanged (imported): best single component as the base, acceptance = cluster bootstrap-t
    95 % lower bound of the per-presentation lift on the 2013 test windows > 0 (B = 10,000, seed 0), plus lift >
    seed SD for the stochastic components, ≤ 4 components, personalisation floor (personal = B7, B4, B9, S*);
    per-presentation values come from run_hybrid.Evaluator.fold_results (weights tuned on each validation window,
    simplex grid D-29), restricted to the eight training presentations;
  * the selected combination is then evaluated on the held-out presentation with the D-51 floor (floor component
    weight ≥ run_hybrid.floor_step) exactly as frozen_analyses builds HYB*; the nominal grid is reported too.
Weights are tuned per (presentation, origin) on validation, so a fold's result does not depend on which other
presentations are in the training set: the held-out value is a function of the selected combination only.
No 2014 row is read.

Stop condition: run on all nine presentations, the same code must select the frozen combination and floor
component of results/dev2013/hybrid_frozen.json, reproduce the round-1 decision table of hybrid_acceptance.md
(mean lift, interval bounds, seed SD, decision; at its 4 printed decimals), and reproduce HYB* per fold in
dev2013/hybrid.csv (≤ 1e-6). Runtime guard: after the reproduction and the first held-out fold, the total is
estimated and the tool stops if it exceeds --max-minutes (default 90).

    python3 scripts/posthoc/a10_selection_loo.py [--workers 4] [--max-minutes 90]
"""
from __future__ import annotations

import argparse
import json
import multiprocessing as mp
import re
import time

from _s2 import C, check_hybrid_folds, fold_frame, folds_for, np, pd
from src.ml import data, hybrid
from src.ml.experiments import run_hybrid as RH

SEQ = ["B5_SKNN", "B6_Markov", "GRU_lite"]
NONPERS = ["B1_Random", "B2_Pop", "B3_RecentPop"]


class SubsetEvaluator:
    """run_hybrid.Evaluator.__call__ restricted to a subset of presentations (same per-presentation means and
    seed SD formula); fold results are computed once over all folds and cached by the wrapped Evaluator."""

    def __init__(self, ev: RH.Evaluator, keep):
        self.ev, self.keep = ev, set(keep)

    def __call__(self, combo):
        res = [r for r in self.ev.fold_results(combo) if r["presentation"] in self.keep]
        df = pd.DataFrame(res)
        per_pres = df.groupby("presentation")["test_all"].mean().sort_index()
        seed_sd = None
        if any(c in RH.STOCHASTIC for c in combo):
            by_seed = np.array([r["test_all_by_seed"] for r in res])
            pres = df["presentation"].to_numpy()
            seed_means = [pd.Series(by_seed[:, s]).groupby(pres).mean().mean() for s in range(by_seed.shape[1])]
            seed_sd = float(np.std(seed_means, ddof=1))
        return per_pres.to_numpy(), seed_sd


def choose(allres: pd.DataFrame, models, keep):
    sc = {m: C.pres_means(allres, m).loc[sorted(keep)].mean() for m in models}
    return max(sc, key=sc.get), sc


def select(ev, allres, keep):
    s_star, seq = choose(allres, SEQ, keep)
    b_np, _ = choose(allres, NONPERS, keep)
    cands = ["B3_RecentPop", "B7_WRMF", "B4_ItemKNN", s_star, "B9_CBF", "C6_AssessProx", "C7_ClusterPop"]
    if s_star == "B6_Markov":
        raise SystemExit("S* = B6_Markov on this subset: its component scores are not cached (stop; not evaluated)")
    fr = hybrid.greedy_forward(cands, SubsetEvaluator(ev, keep), stochastic=RH.STOCHASTIC,
                               personal=RH.PERSONAL_BASE | {s_star}, n_boot=10_000, seed=0)
    return fr, s_star, b_np, seq


def final_results(ev, fr):
    combo = fr.combination
    if fr.floor_component:
        return ev.fold_results(combo, min_last=RH.floor_step(len(combo))), ev.fold_results(combo)
    res = ev.fold_results(combo)
    return res, res


def md_round1() -> list[tuple]:
    """Round-1 rows of results/dev2013/hybrid_acceptance.md: (label, mean, lo, hi, seed_sd, decision)."""
    txt = (C.DEV / "hybrid_acceptance.md").read_text(encoding="utf-8")
    sec = txt.split("### الجولة 1")[1].split("**الفاصل المنحلّ")[0]
    rows = []
    for line in sec.splitlines():
        if line.startswith("| (") and "|" in line[1:]:
            c = [x.strip() for x in line.strip("|").split("|")]
            rows.append((c[0], c[1], c[2], c[3], c[5], c[6]))
    return rows


def fmt_round1(decisions) -> list[tuple]:
    out = []
    for d in decisions:
        out.append((RH.LABEL[d.component], f"{d.mean_lift:.4f}", RH._b(d.ci[0]), RH._b(d.ci[1]),
                    f"{d.seed_sd:.4f}" if d.seed_sd is not None else "—", "يُقبل" if d.accepted else "يُرفض"))
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--max-minutes", type=float, default=90.0)
    a = ap.parse_args(argv)
    t0 = time.time()
    names = list(data.DEV_PRESENTATIONS)
    C.use_cache("2013")
    base = pd.read_csv(C.DEV / "baselines.csv")
    gru = pd.read_csv(C.DEV / "gru.csv")
    allres = pd.concat([base, gru], ignore_index=True)
    frozen = json.loads((C.DEV / "hybrid_frozen.json").read_text())
    checks, rows, sel_rows, folds_out = [], [], [], []
    with mp.get_context("fork").Pool(a.workers) as pool:
        ev = RH.Evaluator(pool, folds_for(names))
        # ---------- reproduction on all nine (stop on failure) ----------
        fr9, s9, b9, _ = select(ev, allres, names)
        ok = fr9.combination == frozen["components"] and fr9.floor_component == frozen["floor_component"] \
            and s9 == frozen["S_star"] and b9 == frozen["B_np_star"]
        print(f"[reproduction] selection on nine = hybrid_frozen.json: {ok} ({fr9.combination}, floor "
              f"{fr9.floor_component}, S* {s9}, B_np* {b9})", flush=True)
        checks.append({"year": "2013", "check": "selection on all nine (combination, floor, S*, B_np*) = "
                       "dev2013/hybrid_frozen.json", "n": 1, "max_abs_diff": 0.0 if ok else float("nan"),
                       "tolerance": 0.0, "pass": ok})
        mine, ref = fmt_round1(fr9.history[0]), md_round1()
        same = sorted(mine) == sorted(ref)
        print(f"[reproduction] round-1 decision table = hybrid_acceptance.md (4 printed decimals): {same}", flush=True)
        if not same:
            print("mine", mine, "\nref", ref, flush=True)
        checks.append({"year": "2013", "check": "round-1 decision table (lift, interval, seed SD, decision) = "
                       "dev2013/hybrid_acceptance.md at its 4 printed decimals", "n": len(ref),
                       "max_abs_diff": 0.0 if same else float("nan"), "tolerance": 5e-5, "pass": same})
        f9, _ = final_results(ev, fr9)
        checks += check_hybrid_folds("2013", f9, C.DEV)
        if not all(c["pass"] for c in checks):
            raise SystemExit("[a10] reproduction failed; no new number written")
        t_rep = time.time() - t0
        # ---------- leave one presentation out ----------
        for i, h in enumerate(names):
            t1 = time.time()
            keep = [n for n in names if n != h]
            fr, s_star, b_np, seq = select(ev, allres, keep)
            fin, nom = final_results(ev, fr)
            v_fin = float(np.mean([r["test_all"] for r in fin if r["presentation"] == h]))
            v_nom = float(np.mean([r["test_all"] for r in nom if r["presentation"] == h]))
            v_b = float(C.pres_means(base, b_np)[h])
            v_b3 = float(C.pres_means(base, "B3_RecentPop")[h])
            v_hs = float(np.mean([r["test_all"] for r in f9 if r["presentation"] == h]))
            hist = [" ; ".join(f"{d.component}:{'acc' if d.accepted else 'rej'}({d.mean_lift:+.4f},[{RH._b(d.ci[0])},{RH._b(d.ci[1])}])"
                               for d in rnd) for rnd in fr.history]
            rows.append({"held_out": h, "selected_combination": " + ".join(fr.combination),
                         "floor_component": fr.floor_component or "", "S_star_on_8": s_star, "B_np_star_on_8": b_np,
                         "n_rounds": len(fr.history), "rounds": " || ".join(hist),
                         "same_as_frozen": fr.combination == frozen["components"] and fr.floor_component == frozen["floor_component"],
                         "HYB_selected_heldout": v_fin, "HYB_selected_nominal_heldout": v_nom, "B_np_heldout": v_b,
                         "B3_heldout_locked": v_b3, "HYB*_frozen_heldout": v_hs, "delta_vs_B3": v_fin - v_b3,
                         "delta_nominal_vs_B3": v_nom - v_b3, "delta_vs_HYB*": v_fin - v_hs, "status": C.POSTHOC_NOTE})
            folds_out.append(fold_frame([r for r in fin if r["presentation"] == h], "LOO-selected hybrid (held-out)", "2013")
                             .assign(held_out=h))
            print(f"[a10] held out {h}: {' + '.join(fr.combination)} (floor {fr.floor_component}) → {v_fin:.4f} vs "
                  f"B3 {v_b3:.4f} ({time.time() - t1:.0f}s)", flush=True)
            if i == 0:
                # upper bound: each held-out selection evaluates at most the combinations of a full selection, and the
                # reproduction (a full selection from an empty fold cache) took t_rep
                est = (t_rep + max(9 * (time.time() - t1), 9 * t_rep)) / 60
                print(f"[a10] runtime estimate (reproduction + 9 × max(first held-out fold, reproduction); upper "
                      f"bound, fold results are cached across selections): {est:.1f} min", flush=True)
                if est > a.max_minutes:
                    raise SystemExit(f"[a10] estimated {est:.1f} min > {a.max_minutes} min: stopped")
    per = pd.DataFrame(rows)
    d = per.set_index("held_out")["delta_vs_B3"]
    st = C.pair_stats(d, "LOO-selected hybrid − B3_RecentPop (held-out presentation)", "2013")
    st += C.pair_stats(per.set_index("held_out")["delta_nominal_vs_B3"], "LOO-selected hybrid, nominal grid − B3_RecentPop", "2013")
    st += C.pair_stats(per.set_index("held_out")["HYB*_frozen_heldout"] - per.set_index("held_out")["B3_heldout_locked"],
                       "in-sample reference: HYB* (frozen, selected on all nine) − B3_RecentPop", "2013")
    C.write_csv(pd.DataFrame(checks), "a10_reproduction_checks.csv")
    C.write_csv(per, "a10_selection_loo.csv")
    C.write_csv(pd.concat(folds_out, ignore_index=True), "a10_selection_loo_folds.csv")
    C.write_csv(pd.DataFrame(st), "a10_selection_loo_stats.csv")
    print(per[["held_out", "selected_combination", "floor_component", "HYB_selected_heldout", "B3_heldout_locked",
               "delta_vs_B3"]].to_string(index=False))
    print(pd.DataFrame(st)[["comparison", "unit", "n_units", "mean", "ci_lo", "ci_hi", "p_signflip_uncorrected", "n_pos"]].to_string(index=False))
    commit, dirty = C.git_commit()
    print(f"[a10] done in {(time.time() - t0) / 60:.1f} min (commit {commit}{' dirty' if dirty else ''})", flush=True)


if __name__ == "__main__":
    main()
