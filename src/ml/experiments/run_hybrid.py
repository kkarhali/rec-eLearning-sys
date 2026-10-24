"""Hybrid acceptance and freeze on the development presentations (D-11, D-29, D-30, D-32; draft §4.4)
→ results/dev2013/hybrid_frozen.json, hybrid_acceptance.md, hybrid.csv, h4b.csv.

    python3 -m src.ml.experiments.run_hybrid [--workers 4]

Candidates (ADR-002 §3.3): (1) Recent-Pop B3; (2) WRMF B7; (3) Item-kNN B4; (4) the best sequential S* among
SKNN B5, Markov B6 and GRU-lite (if it passed the sanity gates) on the 2013 test windows; (5) CBF B9;
(6) assessment proximity C6; (7) cluster popularity C7. Component parameters = their standalone selection on
validation, task A (D-42); C7's window w is tuned here on validation (seed 0).
Step 1 caches component scores per (presentation, origin, phase, seed); step 2 runs the greedy forward
acceptance: weights on the budgeted simplex grid (D-29) tuned on validation for every (presentation, origin);
lift measured on the 2013 TEST windows (D-30), bootstrap-t over the nine presentations, lift > seed SD for
stochastic components; personalisation floor. Then: freeze, H1/H3 development descriptives, H4-b (exploratory).
"""
from __future__ import annotations

import os

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")

import argparse  # noqa: E402
import json  # noqa: E402
import multiprocessing as mp  # noqa: E402
import subprocess  # noqa: E402
import time  # noqa: E402
from collections import Counter  # noqa: E402

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from .. import components as CP, data, hybrid, metrics, stats  # noqa: E402
from ..harness import SEEDS, _val_score, config_key  # noqa: E402
from ..models import BASELINES, COMPONENTS  # noqa: E402
from ..models.gru_lite import GRULite  # noqa: E402
from ..splits import CUTS, make_fold  # noqa: E402

OUT = data.RESULTS_DIR / "dev2013"
LABEL = {"B3_RecentPop": "(1) Recent-Pop", "B7_WRMF": "(2) WRMF", "B4_ItemKNN": "(3) Item-kNN",
         "B5_SKNN": "(4) SKNN", "B6_Markov": "(4) Markov", "GRU_lite": "(4) GRU-lite", "B9_CBF": "(5) CBF",
         "C6_AssessProx": "(6) قرب التقييم", "C7_ClusterPop": "(7) شعبية العنقود"}
PERSONAL_BASE = {"B7_WRMF", "B4_ItemKNN", "B9_CBF"}
STOCHASTIC = {"B7_WRMF", "GRU_lite", "C7_ClusterPop"}
_PRES: dict = {}
_CFG: dict = {}


def fold_dir(pres, cut):
    return CP.COMP_DIR / f"{pres}_{cut}"


# ------------------------------------------------------------------------------------------------
# step 1: component scores
# ------------------------------------------------------------------------------------------------
def build_fold(args):
    name, cut, comps, seeds = args
    p = _PRES[name]
    t = time.time()
    tr, tg = make_fold(p, cut, "tune")
    tr2, tg2 = make_fold(p, cut, "test")
    for phase, (T, G) in (("tune", (tr, tg)), ("test", (tr2, tg2))):
        tgt, cand, un, ev = G.task("A")
        tB, cB, uB, eB = G.task("B")
        np.savez_compressed(fold_dir(name, cut) / f"fold_{phase}.npz" if fold_dir(name, cut).exists()
                            else _mk(fold_dir(name, cut)) / f"fold_{phase}.npz",
                            tgt=tgt, cand=cand, unreach=un, ev=ev, tgtB=tB, unreachB=uB, evB=eB,
                            tiebreak=T.tiebreak, n_items=T.seen.sum(axis=1), pop=T.popularity())
    vA = tg.task("A")
    for comp in comps:
        if comp == "GRU_lite":
            continue                                   # cached by run_gru
        if comp == "C7_ClusterPop":
            from ..models.context import cluster_choice
            cls = COMPONENTS[comp]
            m = cls(seed=seeds[0], w=3, precomputed=cluster_choice(tr)).fit(tr)
            best = None
            for w in (3, 7, 14, 21, 28):
                S = m.set_window(w).score()
                v = _val_score(S, vA, tr.tiebreak)
                if best is None or v > best[0]:
                    best = (v, {"w": w}, S.copy())
            cfg = best[1]
            CP.save_scores(name, cut, comp, "tune", seeds[0], best[2])
            ch2 = cluster_choice(tr2)
            for s in seeds:
                if not CP.has_scores(name, cut, comp, "test", s):
                    CP.save_scores(name, cut, comp, "test", s,
                                   cls(seed=s, **cfg, precomputed=ch2).fit(tr2).score())
            (fold_dir(name, cut) / f"{comp}_config.json").write_text(json.dumps({"config": config_key(cfg)}))
            continue
        elif comp == "C6_AssessProx":
            cfg, cls = {}, COMPONENTS[comp]
            CP.save_scores(name, cut, comp, "tune", seeds[0], cls().fit(tr).score())
        else:
            cfg, cls = _CFG[(comp, name, cut)], BASELINES[comp]
            if not CP.has_scores(name, cut, comp, "tune", seeds[0]):
                CP.save_scores(name, cut, comp, "tune", seeds[0], cls(seed=seeds[0], **cfg).fit(tr).score())
        for s in (seeds if cls.stochastic else seeds[:1]):
            if not CP.has_scores(name, cut, comp, "test", s):
                CP.save_scores(name, cut, comp, "test", s, cls(seed=s, **cfg).fit(tr2).score())
        (fold_dir(name, cut) / f"{comp}_config.json").write_text(json.dumps({"config": config_key(cfg)}))
    print(f"[hybrid] scores {name} t={cut} ({time.time() - t:.0f}s)", flush=True)
    return name, cut


def _mk(d):
    d.mkdir(parents=True, exist_ok=True)
    return d


# ------------------------------------------------------------------------------------------------
# step 2: evaluation of a combination on one fold
# ------------------------------------------------------------------------------------------------
def _rt(name, cut, comp, phase, seed, F, task="A"):
    s = seed if (comp in STOCHASTIC and phase == "test") else SEEDS[0]
    S = CP.load_scores(name, cut, comp, phase, s)
    cand = F["cand"] if task == "A" else np.ones_like(F["cand"])
    ev = F["ev"] if task == "A" else F["evB"]
    return hybrid.rank_normalize(S[ev], cand[ev])


def _ndcg(score, F, ev_rows, task="A", slice_mask=None, ks=(10,)):
    cand = F["cand"] if task == "A" else np.ones_like(F["cand"])
    tgt = F["tgt"] if task == "A" else F["tgtB"]
    un = F["unreach"] if task == "A" else F["unreachB"]
    res = metrics.evaluate(score, cand[ev_rows], tgt[ev_rows], un[ev_rows], np.ones(ev_rows.sum(), bool),
                           F["tiebreak"][ev_rows], ks=ks)
    return metrics.summarize(res, slice_mask)


def eval_combo_fold(args):
    """Weights tuned on validation; test NDCG@10 per seed (all / cold_q1 / top_q4). Returns a dict."""
    name, cut, combo, weights_override, forced = args[:5]
    min_last = args[5] if len(args) > 5 else None
    Ft = dict(np.load(fold_dir(name, cut) / "fold_tune.npz"))
    Fs = dict(np.load(fold_dir(name, cut) / "fold_test.npz"))
    evt, evs = Ft["ev"].astype(bool), Fs["ev"].astype(bool)
    r_tune = [_rt(name, cut, c, "tune", 0, Ft) for c in combo]
    if weights_override is not None:
        w = np.asarray(weights_override, dtype=float)
        val = _ndcg(hybrid.fuse(r_tune, w), Ft, evt)["NDCG@10"]
    elif forced is not None:
        # H4-b: forced insertion of the last component with w7 ∈ {0, .1, …, .5}; others = base weights × (1 − w7)
        base_w = np.asarray(forced, dtype=float)
        best = None
        for w7 in (0.0, 0.1, 0.2, 0.3, 0.4, 0.5):
            w_try = np.r_[base_w * (1 - w7), w7]
            v = _ndcg(hybrid.fuse(r_tune, w_try), Ft, evt)["NDCG@10"]
            if best is None or v > best[0]:
                best = (v, w_try)
        val, w = best
    else:
        grid = hybrid.simplex_grid(len(combo))
        if min_last is not None:                      # descriptive variant: floor component weight ≥ min_last
            grid = grid[grid[:, -1] >= min_last - 1e-12]
        vals = [_ndcg(hybrid.fuse(r_tune, g), Ft, evt)["NDCG@10"] for g in grid]
        b = int(np.argmax(vals))
        w, val = grid[b], vals[b]
    n_items = Fs["n_items"][evs]
    q1, q3 = np.quantile(n_items, [0.25, 0.75])
    slices = {"all": None, "cold_q1": n_items <= q1, "top_q4": n_items >= q3}
    seeds = SEEDS if any(c in STOCHASTIC for c in combo) else SEEDS[:1]
    test = {k: [] for k in slices}
    for s in seeds:
        r_test = [_rt(name, cut, c, "test", s, Fs) for c in combo]
        fused = hybrid.fuse(r_test, w)
        for k, m in slices.items():
            test[k].append(_ndcg(fused, Fs, evs, slice_mask=m)["NDCG@10"])
    return {"presentation": name, "cut": cut, "combo": list(combo), "weights": [float(x) for x in w], "val": float(val),
            **{f"test_{k}": float(np.mean(v)) for k, v in test.items()},
            "test_all_by_seed": [float(x) for x in test["all"]], "n_seeds": len(seeds)}


class Evaluator:
    def __init__(self, pool, folds):
        self.pool, self.folds, self.cache, self.log = pool, folds, {}, []

    def fold_results(self, combo, weights_by_fold=None, forced_by_fold=None, min_last=None):
        key = (tuple(combo), None if weights_by_fold is None else "w", None if forced_by_fold is None else "f", min_last)
        plain = weights_by_fold is None and forced_by_fold is None
        if key in self.cache and plain:
            return self.cache[key]
        args = [(n, c, tuple(combo), None if weights_by_fold is None else weights_by_fold[(n, c)],
                 None if forced_by_fold is None else forced_by_fold[(n, c)], min_last) for n, c in self.folds]
        res = self.pool.map(eval_combo_fold, args, chunksize=1)
        if plain:
            self.cache[key] = res
        return res

    def __call__(self, combo):
        res = self.fold_results(combo)
        df = pd.DataFrame(res)
        per_pres = df.groupby("presentation")["test_all"].mean().sort_index()
        seed_sd = None
        if any(c in STOCHASTIC for c in combo):
            by_seed = np.array([r["test_all_by_seed"] for r in res])          # folds × seeds
            pres = df["presentation"].to_numpy()
            seed_means = [pd.Series(by_seed[:, s]).groupby(pres).mean().mean() for s in range(by_seed.shape[1])]
            seed_sd = float(np.std(seed_means, ddof=1))
        self.log.append({"combo": " + ".join(combo), "test_mean": float(per_pres.mean()), "seed_sd": seed_sd})
        return per_pres.to_numpy(), seed_sd


def _b(x):
    """Bootstrap-t bound for display: degenerate resamples (many identical unit lifts) give |bound| ≫ 1."""
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return "—"
    return ("−∞" if x < 0 else "+∞") if abs(x) > 1 else f"{x:+.4f}"


def _md(df):
    cols = list(df.columns)
    out = ["| " + " | ".join(map(str, cols)) + " |", "|" + "---|" * len(cols)]
    for _, r in df.iterrows():
        out.append("| " + " | ".join(f"{v:.4f}" if isinstance(v, float) else str(v) for v in r.values) + " |")
    return "\n".join(out)


def presentation_means(df: pd.DataFrame, model: str, task="A", slice_="all", metric="NDCG@10") -> pd.Series:
    r = df[(df["model"] == model) & (df["task"] == task) & (df["slice"] == slice_)]
    return r.groupby(["presentation", "cut"])[metric].mean().groupby("presentation").mean().sort_index()


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--presentations", nargs="*", default=list(data.DEV_PRESENTATIONS))
    a = ap.parse_args(argv)
    data.assert_allowed(a.presentations)
    t0 = time.time()
    base = pd.read_csv(OUT / "baselines.csv")
    gru_ok = json.loads((OUT / "gru_sanity.json").read_text()).get("gates_passed", False) and (OUT / "gru.csv").exists()
    gru = pd.read_csv(OUT / "gru.csv") if gru_ok else None
    allres = pd.concat([base, gru], ignore_index=True) if gru_ok else base
    # S*: best sequential on the 2013 test windows (task A), and B_np* among B1–B3 (D-30)
    seq_cands = ["B5_SKNN", "B6_Markov"] + (["GRU_lite"] if gru_ok else [])
    seq_scores = {m: presentation_means(allres, m).mean() for m in seq_cands}
    s_star = max(seq_scores, key=seq_scores.get)
    s_star_nonneural = max(["B5_SKNN", "B6_Markov"], key=lambda m: seq_scores[m])
    np_scores = {m: presentation_means(base, m).mean() for m in ("B1_Random", "B2_Pop", "B3_RecentPop")}
    b_np = max(np_scores, key=np_scores.get)
    cands = ["B3_RecentPop", "B7_WRMF", "B4_ItemKNN", s_star, "B9_CBF", "C6_AssessProx", "C7_ClusterPop"]
    personal = PERSONAL_BASE | {s_star}
    _CFG.update(CP.selected_configs(OUT / "baselines.csv", "A"))
    _PRES.update(data.load_dev_presentations(tuple(a.presentations)))
    order = ["FFF_2013J", "FFF_2013B", "DDD_2013J", "BBB_2013J", "DDD_2013B", "BBB_2013B", "EEE_2013J",
             "GGG_2013J", "AAA_2013J"]
    folds = [(n, c) for c in sorted(CUTS, reverse=True) for n in order if n in a.presentations]
    ctx = mp.get_context("fork")
    with ctx.Pool(a.workers) as pool:
        pool.map(build_fold, [(n, c, cands, SEEDS) for n, c in folds], chunksize=1)
    t1 = time.time()
    with ctx.Pool(a.workers) as pool:
        ev = Evaluator(pool, folds)
        fr = hybrid.greedy_forward(cands, ev, stochastic=STOCHASTIC, personal=personal, n_boot=10_000, seed=0)
        accept_only = [c for c in fr.combination if c != fr.floor_component]
        final = ev.fold_results(fr.combination)
        floor_min = ev.fold_results(fr.combination, min_last=0.25) if fr.floor_component else None
        acc_res = ev.fold_results(accept_only) if accept_only != fr.combination else final
        # H4-b: forced insertion of (7)
        if "C7_ClusterPop" in fr.combination:
            m1_res = final
            idx = fr.combination.index("C7_ClusterPop")
            others = [c for c in fr.combination if c != "C7_ClusterPop"]
            wmap = {}
            for r in final:
                w = np.array(r["weights"])
                w = np.delete(w, idx)
                wmap[(r["presentation"], r["cut"])] = (w / w.sum()).tolist() if w.sum() > 0 else [1 / len(w)] * len(w)
            m0_res = ev.fold_results(others, weights_by_fold=wmap)
        else:
            m0_res = final
            forced = {(r["presentation"], r["cut"]): r["weights"] for r in final}
            m1_res = ev.fold_results(fr.combination + ["C7_ClusterPop"], forced_by_fold=forced)
    t2 = time.time()
    # ---------------- results tables ----------------
    def per_pres(res, col="test_all"):
        return pd.DataFrame(res).groupby("presentation")[col].mean().sort_index()

    hyb = per_pres(final)
    bnp = presentation_means(base, b_np)
    d_h1 = (hyb - bnp).dropna().to_numpy()
    c_h1 = stats.compare(d_h1)
    rows = []
    variants = [("HYB*", final), ("HYB_accept_only", acc_res)] + ([("HYB_floor_w>=0.25", floor_min)] if floor_min else [])
    for label, res in variants:
        for r in res:
            rows.append({"model": label, "presentation": r["presentation"], "cut": r["cut"],
                         "components": " + ".join(r["combo"]), "weights": json.dumps(r["weights"]),
                         "val_NDCG@10": r["val"], "NDCG@10": r["test_all"], "NDCG@10_cold_q1": r["test_cold_q1"],
                         "NDCG@10_top_q4": r["test_top_q4"], "n_seeds": r["n_seeds"]})
    hdf = pd.DataFrame(rows)
    hdf.to_csv(OUT / "hybrid.csv", index=False, float_format="%.6f")
    # H3 development descriptive (GRU vs best non-neural sequential)
    h3 = None
    if gru_ok:
        d3 = (presentation_means(gru, "GRU_lite") - presentation_means(base, s_star_nonneural)).dropna().to_numpy()
        c3 = stats.compare(d3)
        h3 = {"comparison": f"GRU_lite − {s_star_nonneural}", **c3, "sd": float(np.std(d3, ddof=1)),
              "dev_rule_reading": stats.verdict_bidirectional(c3["mean"], c3["ci_lo"], c3["ci_hi"], c3["p"])}
    # H4-b
    h4b = {}
    for sl in ("cold_q1", "top_q4"):
        d = (per_pres(m1_res, f"test_{sl}") - per_pres(m0_res, f"test_{sl}")).dropna().to_numpy()
        c = stats.compare(d)
        direction = "positive" if c["ci_lo"] > 0 else ("negative" if c["ci_hi"] < 0 else "unclear")
        h4b[sl] = {**c, "direction": direction}
    pd.DataFrame([{"slice": k, **v} for k, v in h4b.items()]).to_csv(OUT / "h4b.csv", index=False, float_format="%.6f")
    # ---------------- freeze ----------------
    weights = {f"{r['presentation']}_{r['cut']}": dict(zip(r["combo"], r["weights"])) for r in final}
    modal = Counter(tuple(r["weights"]) for r in final).most_common(1)[0][0]
    cfgs = {}
    gru_cfg = (pd.read_csv(OUT / "gru.csv").query("task == 'A' and slice == 'all'")
               .drop_duplicates(["presentation", "cut"]).set_index(["presentation", "cut"])["config"]) if gru_ok else None
    for n, c in folds:
        d = {}
        for comp in fr.combination:
            f = fold_dir(n, c) / f"{comp}_config.json"
            d[comp] = json.loads(f.read_text())["config"] if f.exists() else gru_cfg.loc[(n, c)]
        cfgs[f"{n}_{c}"] = d
    try:
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=data.REPO_ROOT).decode().strip()
    except Exception:
        commit = "unknown"
    frozen = {
        "status": "frozen on the 2013 development presentations (D-11, D-30); confirmatory run on 2014 re-tunes "
                  "only the weights on each presentation's validation window inside this frozen space",
        "components": fr.combination, "labels": [LABEL[c] for c in fr.combination],
        "floor_component": fr.floor_component, "accept_only_components": accept_only,
        "candidates": cands, "S_star": s_star, "S_star_nonneural": s_star_nonneural, "B_np_star": b_np,
        "weight_grid": f"simplex step {'1/4' if len(fr.combination) <= 3 else '1/3'} (D-29)",
        "initial_weights_modal": dict(zip(fr.combination, modal)),
        "weights_by_fold": weights, "component_configs_by_fold": cfgs,
        "component_parameter_spaces": "standalone spaces of results/dev2013/baselines.csv (B3, B4, B7, B9), "
                                      "gru.csv (GRU-lite), C7 w ∈ {3,7,14,21,28}",
        "task": "A (D-42)", "seeds_report": list(SEEDS), "git_commit_at_freeze_run": commit,
        "date": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    (OUT / "hybrid_frozen.json").write_text(json.dumps(frozen, indent=2, ensure_ascii=False))
    # ---------------- report ----------------
    single = pd.DataFrame([{"المكوّن": LABEL[c], "id": c, "NDCG@10 اختبار 2013 (منفرداً)": float(np.mean(ev((c,))[0]))}
                           for c in cands]).sort_values("NDCG@10 اختبار 2013 (منفرداً)", ascending=False)
    md = ["# قاعدة القبول والتركيبة المجمَّدة للهجين — عروض التطوير 2013 (مولَّد بـ`python3 -m src.ml.experiments.run_hybrid`)\n",
          f"**التركيبة المجمَّدة HYB\\*:** {' + '.join(LABEL[c] for c in fr.combination)}"
          + (f" — دخل {LABEL[fr.floor_component]} **بالأرضية لا بالقبول** (D-30)" if fr.floor_component else "") + "\n",
          f"- S\\* (أفضل تسلسلي على نوافذ اختبار 2013): **{s_star}**؛ القيم: "
          + "، ".join(f"{k} {v:.4f}" for k, v in seq_scores.items()) + ".",
          f"- B_np\\* (أقوى غير شخصي): **{b_np}** (" + "، ".join(f"{k} {v:.4f}" for k, v in np_scores.items()) + ").",
          f"- الأوزان: شبكة السمبلكس D-29 مضبوطة على التحقق لكل (عرض، أصل)؛ المنوال: "
          + "، ".join(f"{LABEL[c]} {w:.3f}" for c, w in zip(fr.combination, modal)) + ".",
          "- الرفع على نوافذ **اختبار** 2013 (t، t+14] (D-30)، وفاصل bootstrap-t العنقودي على العروض التسعة، "
          "وللمكوّن العشوائي شرط «الرفع > انحراف البذور الخمس» (انحراف متوسط التركيبة عبر البذور).\n",
          "## المكوّنات منفردة (نوافذ اختبار 2013، المهمة A)\n", _md(single) + "\n",
          "## جولات الإجراء الجشع\n"]
    base_combo = [fr.combination[0]]
    for rnd, decisions in enumerate(fr.history, start=1):
        md.append(f"### الجولة {rnd} — القاعدة: {' + '.join(LABEL[c] for c in base_combo)}\n")
        tab = pd.DataFrame([{"المرشح": LABEL[d.component], "متوسط الرفع": d.mean_lift, "الفاصل الأدنى": _b(d.ci[0]),
                             "الفاصل الأعلى": _b(d.ci[1]), "انحراف البذور": d.seed_sd if d.seed_sd is not None else "—",
                             "القرار": "يُقبل" if d.accepted else "يُرفض"} for d in decisions])
        md.append(_md(tab) + "\n")
        acc = [d for d in decisions if d.accepted]
        if acc:
            base_combo = base_combo + [max(acc, key=lambda d: d.mean_lift).component]
    why = []
    for c in cands:
        if c in accept_only:
            why.append(f"- {LABEL[c]}: **داخل** — " + ("أفضل مكوّن منفرد (القاعدة الابتدائية)." if c == fr.combination[0]
                                                      else "رفع موجب بفاصل لا يشمل الصفر وأكبر رفع في جولته."))
        elif c == fr.floor_component:
            why.append(f"- {LABEL[c]}: **داخل بالأرضية** — لم يُقبل أي مكوّن شخصي، فأُضيف صاحب أكبر رفع مقدَّر بينها.")
        else:
            why.append(f"- {LABEL[c]}: **خارج** — لم يحقق شرط القبول في أي جولة فُحص فيها "
                       "(الحد الأدنى لفاصل bootstrap-t ≤ 0، أو الرفع ≤ انحراف البذور للمكوّن العشوائي).")
    gap = hdf[hdf["model"] == "HYB*"]
    wpos = sum(1 for r in final if fr.floor_component and r["weights"][fr.combination.index(fr.floor_component)] > 0)
    md += ["**ملاحظة على الفاصل:** حين يختار الضبط وزناً صفرياً للمرشح في عدة عروض يصبح رفعها صفراً بالضبط، "
           "فتنتج إعادات bootstrap كلها من هذه العروض بانحراف صفري، وينفجر t* (المقام max(s_b, 10⁻¹²)، ADR-004 §2.2). "
           "يُعرض الحد حينئذ ±∞؛ والقرار لا يتغير لأن الفاصل يشمل الصفر.\n",
           "## لماذا دخل/خرج كل مكوّن\n", *why, "",
           *( [f"**وزن مكوّن الأرضية:** {LABEL[fr.floor_component]} أخذ وزناً موجباً في {wpos}/27 زوجاً فقط (الشبكة تتضمن الصفر)، "
               "فالأرضية مستوفاة تركيبياً لكنها قد تكون اسمية في بعض الأزواج. للمعلومة: البديل الذي يفرض وزن الأرضية ≥ 1/4 "
               f"يعطي NDCG@10 = {pd.DataFrame(floor_min).groupby('presentation')['test_all'].mean().mean():.4f} على نوافذ الاختبار "
               "(وصفي؛ يحتاج قرار المشرف، ولم يُستعمل في التجميد).\n"] if fr.floor_component else []),
           "## الهجين على نوافذ اختبار 2013 (المهمة A)\n",
           _md(pd.DataFrame([{"النموذج": "HYB*", "NDCG@10": float(hyb.mean()), "تحقق": float(gap["val_NDCG@10"].mean()),
                              "فجوة التفاؤل": float(gap["val_NDCG@10"].mean() - gap["NDCG@10"].mean())},
                             {"النموذج": "HYB (بالقبول وحده)", "NDCG@10": float(per_pres(acc_res).mean()),
                              "تحقق": float(pd.DataFrame(acc_res)["val"].mean()),
                              "فجوة التفاؤل": float(pd.DataFrame(acc_res)["val"].mean() - pd.DataFrame(acc_res)["test_all"].mean())},
                             {"النموذج": b_np, "NDCG@10": float(bnp.mean()), "تحقق": float("nan"), "فجوة التفاؤل": float("nan")}])) + "\n",
           f"**H1 (وصفي على التطوير):** Δ(HYB\\* − {b_np}) = {c_h1['mean']:+.4f}، فاصل bootstrap-t "
           f"[{_b(c_h1['ci_lo'])}، {_b(c_h1['ci_hi'])}]، p = {c_h1['p']:.4f}، عروض Δ>0: {int((d_h1 > 0).sum())}/9. "
           f"قراءة القاعدة الآلية (9 عروض، بلا Holm، توضيحية): {stats.verdict(c_h1['mean'], c_h1['ci_lo'], c_h1['ci_hi'], c_h1['p'])}.\n"]
    if h3:
        md.append(f"**H3 (وصفي على التطوير):** Δ({h3['comparison']}) = {h3['mean']:+.4f}، فاصل [{h3['ci_lo']:+.4f}، "
                  f"{h3['ci_hi']:+.4f}]، p = {h3['p']:.4f}؛ قراءة الجدول السداسي (توضيحية): {h3['dev_rule_reading']}.\n")
    md += ["## H4-ب (استكشافية، D-28): إدخال (7) قسراً\n",
           _md(pd.DataFrame([{"الشريحة": k, "Δ": v["mean"], "الفاصل الأدنى": _b(v["ci_lo"]), "الفاصل الأعلى": _b(v["ci_hi"]),
                              "p (غير مصححة)": v["p"], "الاتجاه": v["direction"]} for k, v in h4b.items()])) + "\n",
           "M1 = HYB\\* مع (7) بوزن w₇ ∈ {0، 0.1، …، 0.5} مضبوط على التحقق وبقية الأوزان × (1 − w₇)؛ M0 = HYB\\* "
           "(أو HYB\\* بلا (7) مع إعادة التطبيع إن كان (7) داخلها). الربع الأدنى = n ≤ Q1 (D-45).\n",
           f"الزمن: بناء الدرجات {(t1 - t0) / 60:.1f} دقيقة، والبحث والتقييم {(t2 - t1) / 60:.1f} دقيقة.\n",
           "### سجل كل التركيبات التي قُيِّمت\n", _md(pd.DataFrame(ev.log)) + "\n"]
    (OUT / "hybrid_acceptance.md").write_text("\n".join(md), encoding="utf-8")
    summary = {"components": fr.combination, "floor": fr.floor_component, "floor_weight_positive_folds": wpos,
               "floor_min_quarter_ndcg": (float(pd.DataFrame(floor_min).groupby("presentation")["test_all"].mean().mean())
                                          if floor_min else None),
               "H1": c_h1, "sd_H1": float(np.std(d_h1, ddof=1)),
               "H3": h3, "H4b": h4b, "seconds": round(time.time() - t0, 1)}
    (OUT / "hybrid_meta.json").write_text(json.dumps(summary, indent=2, default=float, ensure_ascii=False))
    print(f"[hybrid] HYB* = {fr.combination} (floor={fr.floor_component}); H1 Δ={c_h1['mean']:+.4f} "
          f"in {(time.time() - t0) / 60:.1f} min", flush=True)


if __name__ == "__main__":
    main()
