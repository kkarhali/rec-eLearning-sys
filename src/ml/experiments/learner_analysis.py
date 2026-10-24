"""Learner analysis on the development presentations (D-13, D-27, D-39; draft §4.7, §2.6)
→ results/dev2013/learner_analysis.md, learner_auc.csv, learner_clusters.csv, learner_fairness.csv.

    python3 -m src.ml.experiments.learner_analysis [--no-overlap-exclusion]

H4-a development analogue: leave-one-presentation-out (LOPO) inside 2013. For every held-out presentation,
Logistic L2 is trained on the other eight (λ by inner LOPO over those eight), for M0 (total clicks), M1 (VLE
log features only) and M2 (M1 + academic/administrative). Δ_p = AUC_p(M1) − AUC_p(M0); bootstrap-t over the
nine presentations, δ_AUC = 0.02 (descriptive; the confirmatory test trains on 2013 and tests on 2014).
Training rows of students registered in 2014 are removed (D-27/D-47) unless --no-overlap-exclusion
(sensitivity "full training"). Youden threshold from pooled out-of-fold predictions (frozen).
CART (depth ≤ 4, min leaf ∈ {20, 50, 100}) for interpretation. Cut 56 primary, 28 and 112 secondary.
Clusters at day 56 (dashboard, D-39-c): k-means++ with the k rule; post-hoc at-risk rate per cluster.
"""
from __future__ import annotations

import os

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")

import argparse  # noqa: E402
import json  # noqa: E402
import time  # noqa: E402

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from .. import data, learners as L, stats  # noqa: E402

OUT = data.RESULTS_DIR / "dev2013"
LAMBDAS = (1e-3, 1e-2, 1e-1, 1.0, 10.0)
CART_GRID = [(d, m) for d in (2, 3, 4) for m in (20, 50, 100)]
CUTS_RISK = (56, 28, 112)


def build_table(pres: dict, t_c: int, sa: pd.DataFrame) -> pd.DataFrame:
    frames = []
    for name, p in pres.items():
        reg = p.registrations.set_index("id_student")
        info = p.students.set_index("id_student")
        unreg = reg["date_unregistration"]
        keep = info.index[~(unreg.reindex(info.index) < t_c).fillna(False).to_numpy()]
        keep = keep[info.loc[keep, "final_result"].isin(["Pass", "Distinction", "Fail", "Withdrawn"])]
        y = info.loc[keep, "final_result"].isin(["Fail", "Withdrawn"]).astype(int)
        m0 = L.total_clicks(p.events, keep.to_numpy(), t_c)
        m1 = L.vle_features(p.events, keep.to_numpy(), t_c)
        ac = L.academic_features(p, keep.to_numpy(), t_c, sa)
        df = pd.concat([m0, m1, ac], axis=1)
        df["y"] = y.to_numpy()
        df["presentation"] = name
        frames.append(df.reset_index())
    return pd.concat(frames, ignore_index=True)


def feature_sets(df: pd.DataFrame) -> dict[str, list[str]]:
    m1 = ["active_days", "gap_sd", "first_day"] + [c for c in df.columns if c.startswith("share_")]
    m2 = m1 + ["on_time_ratio", "mean_score", "no_score", "num_of_prev_attempts", "studied_credits", "date_registration"]
    return {"M0": ["total_clicks"], "M1": m1, "M2": m2}


def standardise(df: pd.DataFrame, cols) -> np.ndarray:
    """z-score within each presentation (pre-cut data only)."""
    X = np.zeros((len(df), len(cols)))
    for _, idx in df.groupby("presentation").indices.items():
        X[idx] = L.zscore(df.iloc[idx][cols].to_numpy(dtype=float))
    return X


def lopo_logistic(df, X, y, train_mask, lambdas=LAMBDAS):
    """Outer LOPO predictions; λ by inner LOPO on the training presentations."""
    pres = df["presentation"].to_numpy()
    names = list(dict.fromkeys(pres))
    oof = np.full(len(df), np.nan)
    chosen = {}
    for held in names:
        tr_names = [n for n in names if n != held]
        best = None
        for lam in lambdas:
            aucs = []
            for inner in tr_names:
                fit = np.isin(pres, [n for n in tr_names if n != inner]) & train_mask
                te = pres == inner
                w = L.logistic_fit(X[fit], y[fit], lam)
                aucs.append(L.roc_auc(y[te], L.logistic_predict(w, X[te])))
            if best is None or np.nanmean(aucs) > best[0]:
                best = (np.nanmean(aucs), lam)
        fit = np.isin(pres, tr_names) & train_mask
        w = L.logistic_fit(X[fit], y[fit], best[1])
        te = pres == held
        oof[te] = L.logistic_predict(w, X[te])
        chosen[held] = best[1]
    return oof, chosen


def lopo_cart(df, X, y, train_mask):
    pres = df["presentation"].to_numpy()
    names = list(dict.fromkeys(pres))
    oof = np.full(len(df), np.nan)
    chosen = {}
    for held in names:
        tr_names = [n for n in names if n != held]
        best = None
        for depth, leaf in CART_GRID:
            aucs = []
            for inner in tr_names[::2]:           # every second inner fold (cost; documented)
                fit = np.isin(pres, [n for n in tr_names if n != inner]) & train_mask
                te = pres == inner
                tree = L.cart_fit(X[fit], y[fit], depth, leaf)
                aucs.append(L.roc_auc(y[te], L.cart_predict(tree, X[te])))
            if best is None or np.nanmean(aucs) > best[0]:
                best = (np.nanmean(aucs), (depth, leaf))
        fit = np.isin(pres, tr_names) & train_mask
        tree = L.cart_fit(X[fit], y[fit], *best[1])
        te = pres == held
        oof[te] = L.cart_predict(tree, X[te])
        chosen[held] = best[1]
    return oof, chosen


def per_presentation(df, y, scores: dict, thr: dict) -> pd.DataFrame:
    rows = []
    for name, idx in df.groupby("presentation").indices.items():
        for model, s in scores.items():
            r = {"presentation": name, "model": model, "n": len(idx), "risk_rate": float(y[idx].mean()),
                 "ROC_AUC": L.roc_auc(y[idx], s[idx]), "PR_AUC": L.average_precision(y[idx], s[idx]),
                 "Brier": L.brier(y[idx], s[idx]) if model.startswith(("M", "majority")) else np.nan}
            if model in thr:
                r.update(L.threshold_metrics(y[idx], s[idx], thr[model]))
            rows.append(r)
    return pd.DataFrame(rows)


def run_cut(pres, sa, t_c, overlap_ids, exclude_overlap=True):
    df = build_table(pres, t_c, sa)
    y = df["y"].to_numpy()
    fs = feature_sets(df)
    in_overlap = df["id_student"].isin(overlap_ids).to_numpy() if overlap_ids is not None else np.zeros(len(df), bool)
    train_mask = ~in_overlap if exclude_overlap else np.ones(len(df), bool)
    scores, lam = {}, {}
    for m, cols in fs.items():
        X = standardise(df, cols)
        scores[m], lam[m] = lopo_logistic(df, X, y, train_mask)
    Xc = standardise(df, fs["M2"])
    scores["CART_M2"], cart_par = lopo_cart(df, Xc, y, train_mask)
    scores["majority"] = np.full(len(df), y[train_mask].mean())
    thr = {m: L.youden_threshold(y, scores[m]) for m in ("M0", "M1", "M2")}
    tab = per_presentation(df, y, scores, thr)
    return df, y, scores, tab, thr, lam, cart_par, in_overlap, fs


def clusters_day56(pres, df56, fs) -> pd.DataFrame:
    rows = []
    for name, idx in df56.groupby("presentation").indices.items():
        sub = df56.iloc[idx]
        cols = fs["M1"] + ["date_registration"]
        X = L.zscore(sub[cols].to_numpy(dtype=float))
        ch = L.choose_k(X)
        for c in range(ch.k):
            mm = ch.labels == c
            rows.append({"presentation": name, "k": ch.k, "stable": ch.stable, "cluster": c, "size": int(mm.sum()),
                         "share": float(mm.mean()), "active_days": float(sub["active_days"][mm].mean()),
                         "first_day": float(sub["first_day"][mm].mean()), "gap_sd": float(sub["gap_sd"][mm].mean()),
                         "total_clicks": float(sub["total_clicks"][mm].mean()),
                         "share_quiz": float(sub["share_quiz"][mm].mean()),
                         "share_forumng": float(sub["share_forumng"][mm].mean()),
                         "share_oucontent": float(sub["share_oucontent"][mm].mean()),
                         "share_navigation": float(sub[[f"share_{t}" for t in L.NAV_TYPES]].sum(axis=1)[mm].mean()),
                         "at_risk_rate_posthoc": float(sub["y"][mm].mean()),
                         "silhouette_k": float(ch.table.set_index("k").loc[ch.k, "silhouette"]),
                         "ari_k": float(ch.table.set_index("k").loc[ch.k, "ari_mean"])})
    return pd.DataFrame(rows)


def fairness(pres, df, y, s, thr) -> pd.DataFrame:
    info = pd.concat([data.load_student_info(include_sensitive=True).query("presentation == @n").assign(presentation=n)
                      for n in pres], ignore_index=True)
    m = df.merge(info[["presentation", "id_student", "gender", "disability", "imd_band", "age_band"]],
                 on=["presentation", "id_student"], how="left")
    rows = []
    for attr in ("gender", "disability", "imd_band", "age_band"):
        for g, idx in m.groupby(attr).indices.items():
            r = L.threshold_metrics(y[idx], s[idx], thr)
            rows.append({"attribute": attr, "group": g, "n": len(idx), "small_group": len(idx) < 50,
                         "risk_rate": float(y[idx].mean()), "ROC_AUC": L.roc_auc(y[idx], s[idx]),
                         "FNR": r["FNR"], "FPR": r["FPR"]})
    return pd.DataFrame(rows)


def _md(df):
    cols = list(df.columns)
    out = ["| " + " | ".join(map(str, cols)) + " |", "|" + "---|" * len(cols)]
    for _, r in df.iterrows():
        out.append("| " + " | ".join(f"{v:.3f}" if isinstance(v, float) else str(v) for v in r.values) + " |")
    return "\n".join(out)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-overlap-exclusion", action="store_true")
    a = ap.parse_args(argv)
    t0 = time.time()
    pres = data.load_dev_presentations()
    sa = data.load_student_assessment("dev")
    overlap = data.confirmatory_student_ids()            # D-47 (logged in results/access_log.jsonl)
    all_tabs, summary, deltas = [], [], {}
    md = ["# تحليل المتعلمين — عروض التطوير 2013 (مولَّد بـ`python3 -m src.ml.experiments.learner_analysis`)\n",
          "> وصفي على التطوير: «ترك عرض واحد خارج التدريب» داخل 2013 (9 وحدات). الاختبار التأكيدي (تدريب 2013 واختبار 2014) "
          "بعد التجميد. لا سمة حساسة في أي نموذج (D-21).\n"]
    for t_c in CUTS_RISK:
        for excl in ((True, False) if t_c == 56 else (True,)):
            df, y, scores, tab, thr, lam, cart_par, in_ov, fs = run_cut(pres, sa, t_c, overlap, excl)
            tab["cut"] = t_c
            tab["overlap_excluded"] = excl
            all_tabs.append(tab)
            piv = tab.pivot(index="presentation", columns="model", values="ROC_AUC")
            for a_, b_ in (("M1", "M0"), ("M2", "M1"), ("M2", "M0")):
                d = (piv[a_] - piv[b_]).to_numpy()
                c = stats.compare(d)
                v = stats.verdict(c["mean"], c["ci_lo"], c["ci_hi"], c["p"], delta=0.02)
                summary.append({"cut": t_c, "overlap_excluded": excl, "comparison": f"{a_} − {b_}",
                                "mean_AUC_a": float(piv[a_].mean()), "mean_AUC_b": float(piv[b_].mean()),
                                "delta": c["mean"], "ci_lo": c["ci_lo"], "ci_hi": c["ci_hi"], "p": c["p"],
                                "presentations_delta_pos": int((d > 0).sum()), "dev_rule_reading": v,
                                "sd_delta": float(np.std(d, ddof=1))})
                deltas[(t_c, excl, a_, b_)] = d
            if t_c == 56 and excl:
                df56, y56, s56, thr56, fs56, ov56 = df, y, scores, thr, fs, in_ov
                cart_tree = L.cart_fit(standardise(df, fs["M2"]), y, *max(set(cart_par.values()), key=list(cart_par.values()).count))
                lam56 = lam
    tabs = pd.concat(all_tabs, ignore_index=True)
    tabs.to_csv(OUT / "learner_auc.csv", index=False, float_format="%.6f")
    summ = pd.DataFrame(summary)
    summ.to_csv(OUT / "learner_h4a_summary.csv", index=False, float_format="%.6f")
    cl = clusters_day56(pres, df56, fs56)
    cl.to_csv(OUT / "learner_clusters.csv", index=False, float_format="%.6f")
    fair = fairness(pres, df56, y56, s56["M1"], thr56["M1"])
    fair.to_csv(OUT / "learner_fairness.csv", index=False, float_format="%.6f")
    sd_h4a = float(np.std(deltas[(56, True, "M1", "M0")], ddof=1))
    (OUT / "learner_meta.json").write_text(json.dumps({
        "seconds": round(time.time() - t0, 1), "overlap_ids": len(overlap),
        "overlap_rows_day56": int(ov56.sum()), "rows_day56": int(len(df56)), "youden_thresholds_day56": thr56,
        "lambda_by_heldout_day56": {k: v for k, v in lam56.items()}, "sigma_H4a": sd_h4a}, indent=2, default=str))
    m56 = summ[(summ["cut"] == 56)]
    md += [f"## H4-أ (اليوم 56): AUC بترك عرض خارج التدريب، {len(df56):,} تسجيلاً، معدل الخطر {y56.mean():.1%}؛ "
           f"حُذف من التدريب {int(ov56.sum()):,} صفاً لطلاب لهم تسجيل في 2014 (D-47)\n",
           _md(m56[["overlap_excluded", "comparison", "mean_AUC_a", "mean_AUC_b", "delta", "ci_lo", "ci_hi", "p",
                    "presentations_delta_pos", "dev_rule_reading"]]) + "\n",
           "`dev_rule_reading` تطبيق آلي للجدول الأحادي بـδ_AUC = 0.02 على 9 عروض تطوير بلا Holm، **للتوضيح فقط** "
           "(الحكم التأكيدي على 2014). الفاصل bootstrap-t العنقودي؛ p قلب إشارات دقيق ثنائي الطرف.\n",
           "## AUC لكل عرض (اليوم 56، مع حذف المتداخلين)\n"]
    t56 = tabs[(tabs["cut"] == 56) & tabs["overlap_excluded"]]
    md.append(_md(t56.pivot(index="presentation", columns="model", values="ROC_AUC").reset_index()) + "\n")
    agg = t56.groupby("model")[["ROC_AUC", "PR_AUC", "Brier", "balanced_accuracy", "F1", "FNR", "FPR"]].mean()
    md += ["## متوسط المقاييس المرافقة (عتبة Youden مجمَّدة من التنبؤات خارج الطيّة)\n",
           _md(agg.reset_index()) + "\n",
           f"عتبات Youden: " + "، ".join(f"{k} = {v:.3f}" for k, v in thr56.items()) + "\n",
           "## القطعان الثانويان 28 و112 (مع حذف المتداخلين)\n",
           _md(summ[summ["cut"] != 56][["cut", "comparison", "mean_AUC_a", "mean_AUC_b", "delta", "ci_lo", "ci_hi", "p"]]) + "\n",
           "## CART (عمق ≤ 4) على ملامح M2 — كل عروض 2013 (للتفسير)\n", "```",
           *L.cart_rules(cart_tree, fs56["M2"]), "```\n",
           "## عناقيد اليوم 56 (للوحة المدرّس، D-39-ج)\n",
           _md(cl[["presentation", "k", "stable", "cluster", "size", "active_days", "first_day", "total_clicks",
                   "share_navigation", "at_risk_rate_posthoc"]]) + "\n",
           "`at_risk_rate_posthoc` متغير تحليل لاحق (final_result) لا ملمح. `stable` = تحقق شرط ARI ≥ 0.8 مع أفضل اثنين في "
           "silhouette وDBI؛ وإلا فأفضل silhouette (الحالة الاحتياطية الرسمية، D-39-ب).\n",
           "## إنصاف وصفي للمصنِّف M1 (اليوم 56؛ FNR وFPR بعتبة Youden؛ المجموعات < 50 موسومة)\n",
           _md(fair) + "\n",
           f"الزمن: {(time.time() - t0) / 60:.1f} دقيقة. σ(Δ_p) لـH4-أ = {sd_h4a:.4f} (يدخل `mde80.md`، D-46).\n"]
    (OUT / "learner_analysis.md").write_text("\n".join(md), encoding="utf-8")
    print(f"[learners] done in {(time.time() - t0) / 60:.1f} min")


if __name__ == "__main__":
    main()
