#!/usr/bin/env python3
"""POST-HOC A-5: equivalence of the hand-written learner models (src/ml/learners.py) with scikit-learn.

Committee condition A-5 (docs/defense/r3-alomar-verdict.md §5). Descriptive; no hypothesis, no verdict.
scikit-learn is NOT installed in the thesis environment (PyPI blocked by the network policy), so this script is
meant for a machine with scikit-learn; without it, it exits with status 2 and a clear message before any work.

Data: the nine 2013 development presentations only (no 2014 row is read, not even the D-47 ids), learner table
of ``learner_analysis.build_table`` at the H4-a cut (day 56 by default), feature sets M0/M1/M2 of
``learner_analysis.feature_sets``, z-scored within each presentation (``learner_analysis.standardise``).
y = Fail/Withdrawn. No sensitive attribute is read (studentInfo is loaded without them, D-21). The D-47 overlap
exclusion is not applied (it would need the 2014 ids): the comparison is between two implementations on the same
rows, which is what A-5 asks.

Comparisons (each row of results/posthoc/sklearn_equivalence.csv):
  1. L2 logistic regression — ours: min mean(logloss) + (λ/2)‖w‖², unpenalised intercept, Newton
     (learners.logistic_fit); sklearn: LogisticRegression(C, solver="newton-cg") minimises C·Σ logloss + ½‖w‖²
     with an unpenalised intercept, hence C = 1 / (λ·n). For M0/M1/M2 × λ ∈ {1e-3, 1e-2, 1e-1, 1, 10}: max |Δ coef|
     (intercept included) on all rows, and max |Δ ROC-AUC| per held-out presentation in leave-one-presentation-out
     (LOPO) predictions, plus max |Δ| of the per-presentation H4-a difference AUC(M1) − AUC(M0).
  2. k-means++ — per presentation (day-56 cluster features of learner_analysis.clusters_day56), our choose_k k:
     ARI between our labels (seed 0, n_init 10) and KMeans(k, init="k-means++", n_init=10, random_state=0,
     algorithm="lloyd"), relative inertia difference, and k chosen by the same rule with sklearn KMeans.
     The two k-means++ initialisations use different random streams (and sklearn's greedy k-means++), so
     identical labels are not expected; ARI close to 1 and equal inertia/k are the evidence.
  3. CART (Gini) — for every (depth, min leaf) of learner_analysis.CART_GRID on M2: share of rows with identical
     predicted leaf probability, class agreement at 0.5, and |Δ ROC-AUC| (in-sample and LOPO);
     DecisionTreeClassifier(criterion="gini", max_depth=d, min_samples_leaf=m, min_samples_split=2m, random_state=0).
  4. Metric functions on identical inputs: roc_auc vs roc_auc_score, brier vs brier_score_loss,
     adjusted_rand_index vs adjusted_rand_score, silhouette_fast vs silhouette_score (same subsample),
     davies_bouldin vs davies_bouldin_score, average_precision vs average_precision_score (ties handled
     differently: informational).

    python3 scripts/posthoc/sklearn_equivalence.py [--cut 56]
    python3 scripts/posthoc/sklearn_equivalence.py --prepare-only     # data preparation only (no sklearn needed)
"""
from __future__ import annotations

import argparse
import importlib.util
import sys
import time

import _common as C  # noqa: E402  (sets sys.path)
import numpy as np
import pandas as pd

MISSING_MSG = ("scikit-learn is not installed: this equivalence check (committee condition A-5) cannot run here. "
               "Install it on a machine with network access (pip install scikit-learn) and rerun "
               "`python3 scripts/posthoc/sklearn_equivalence.py`. Nothing was computed or written.")
TOL = {"coef": 1e-4, "auc": 1e-4, "exact": 1e-9, "ari": 0.95, "agree": 0.99}


def require_sklearn(find_spec=importlib.util.find_spec) -> None:
    """Exit (status 2) with a clear message when scikit-learn is missing; checked before any data is read."""
    if find_spec("sklearn") is None:
        print(f"[A-5] {MISSING_MSG}", file=sys.stderr)
        raise SystemExit(2)


def lambda_to_C(lam: float, n: int) -> float:
    """mean(logloss) + (λ/2)‖w‖², divided by λ, is (1/(λn))·Σ logloss + ½‖w‖²: sklearn's objective with C = 1/(λn)."""
    if lam <= 0 or n <= 0:
        raise ValueError("λ and n must be positive")
    return 1.0 / (lam * n)


def prepare(cut: int = 56):
    """Learner table of the nine 2013 presentations at ``cut`` and the z-scored feature matrices (no sklearn)."""
    from src.ml import data
    from src.ml.experiments import learner_analysis as LA
    pres = data.load_dev_presentations()
    sa = data.load_student_assessment("dev")
    df = LA.build_table(pres, cut, sa)
    leaked = set(df.columns) & set(data.SENSITIVE_COLUMNS)
    if leaked:
        raise RuntimeError(f"sensitive columns in the learner table: {sorted(leaked)}")
    if not df["presentation"].isin(data.DEV_PRESENTATIONS).all():
        raise RuntimeError("non-2013 rows in the learner table")
    fs = LA.feature_sets(df)
    X = {m: LA.standardise(df, cols) for m, cols in fs.items()}
    return pres, df, df["y"].to_numpy(), fs, X


def _row(component, setting, metric, value, tol=None, kind="max", note=""):
    ok = None if tol is None else (bool(value <= tol) if kind == "max" else bool(value >= tol))
    return {"component": component, "setting": setting, "metric": metric, "value": float(value),
            "tolerance": tol, "criterion": None if tol is None else ("≤" if kind == "max" else "≥"), "pass": ok,
            "note": note}


def compare_logistic(df, y, X, rows):
    from sklearn.linear_model import LogisticRegression

    from src.ml import learners as L
    from src.ml.experiments.learner_analysis import LAMBDAS
    pres = df["presentation"].to_numpy()
    names = list(dict.fromkeys(pres))

    def sk_fit(Xf, yf, lam):
        m = LogisticRegression(C=lambda_to_C(lam, len(yf)), solver="newton-cg", tol=1e-12, max_iter=10_000)
        m.fit(Xf, yf)
        return np.r_[m.intercept_, m.coef_.ravel()], m

    per_auc = {}
    for mset in ("M0", "M1", "M2"):
        for lam in LAMBDAS:
            w_ours = L.logistic_fit(X[mset], y, lam)
            w_sk, _ = sk_fit(X[mset], y, lam)
            rows.append(_row("logistic L2 (Newton)", f"{mset}, λ={lam:g}, all 2013 rows", "max |Δ coefficient|",
                             np.abs(w_ours - w_sk).max(), TOL["coef"]))
            d_auc = []
            for held in names:
                tr, te = pres != held, pres == held
                a = L.roc_auc(y[te], L.logistic_predict(L.logistic_fit(X[mset][tr], y[tr], lam), X[mset][te]))
                _, m = sk_fit(X[mset][tr], y[tr], lam)
                b = L.roc_auc(y[te], m.predict_proba(X[mset][te])[:, 1])
                per_auc[(mset, lam, held)] = (a, b)
                d_auc.append(abs(a - b))
            rows.append(_row("logistic L2 (Newton)", f"{mset}, λ={lam:g}, LOPO", "max |Δ ROC-AUC| per held-out presentation",
                             max(d_auc), TOL["auc"]))
    for lam in LAMBDAS:
        d = [abs((per_auc[("M1", lam, h)][0] - per_auc[("M0", lam, h)][0])
                 - (per_auc[("M1", lam, h)][1] - per_auc[("M0", lam, h)][1])) for h in names]
        rows.append(_row("logistic L2 (Newton)", f"H4-a pair AUC(M1) − AUC(M0), λ={lam:g}, LOPO",
                         "max |Δ| of the per-presentation difference", max(d), TOL["auc"]))


def compare_kmeans(df, rows):
    from sklearn.cluster import KMeans
    from sklearn.metrics import adjusted_rand_score, davies_bouldin_score, silhouette_score

    from src.ml import learners as L
    from src.ml.experiments.learner_analysis import feature_sets
    fs = feature_sets(df)
    cols = fs["M1"] + ["date_registration"]
    for name, idx in df.groupby("presentation").indices.items():
        X = L.zscore(df.iloc[idx][cols].to_numpy(dtype=float))
        ch = L.choose_k(X)
        km = KMeans(n_clusters=ch.k, init="k-means++", n_init=10, random_state=0, algorithm="lloyd").fit(X)
        _, _, sse_ours = L.kmeans(X, ch.k, seed=0, n_init=10)
        rows.append(_row("k-means++", f"{name}, k={ch.k} (our rule), seed 0", "ARI(ours, sklearn)",
                         adjusted_rand_score(ch.labels, km.labels_), TOL["ari"], kind="min"))
        rows.append(_row("k-means++", f"{name}, k={ch.k}", "relative inertia difference (ours − sklearn)/sklearn",
                         (sse_ours - km.inertia_) / km.inertia_, note="negative = ours lower SSE"))
        # the k rule of learners.choose_k with sklearn KMeans
        tab = []
        for k in range(2, 9):
            runs = [KMeans(n_clusters=k, init="k-means++", n_init=10, random_state=s, algorithm="lloyd").fit(X).labels_
                    for s in range(5)]
            aris = [adjusted_rand_score(runs[i], runs[j]) for i in range(5) for j in range(i + 1, 5)]
            tab.append({"k": k, "silhouette": L.silhouette_fast(X, runs[0]), "dbi": L.davies_bouldin(X, runs[0]),
                        "ari_mean": float(np.mean(aris))})
        tab = pd.DataFrame(tab)
        top_sil = set(tab.nlargest(2, "silhouette")["k"])
        top_dbi = set(tab.nsmallest(2, "dbi")["k"])
        ok = tab[tab["k"].isin(top_sil & top_dbi) & (tab["ari_mean"] >= 0.8)]
        k_sk = int(ok["k"].min()) if len(ok) else int(tab.loc[tab["silhouette"].idxmax(), "k"])
        rows.append(_row("k-means++", f"{name}", "k chosen: ours − sklearn (0 = same k)", abs(ch.k - k_sk), 0,
                         note=f"ours k={ch.k} ({'stable' if ch.stable else 'unstable'}), sklearn k={k_sk}"))
        # metric functions on identical labels
        n = len(X)
        sub = np.arange(n) if n <= 3000 else np.random.default_rng(0).choice(n, 3000, replace=False)
        rows.append(_row("metric functions", f"{name}, our labels", "|silhouette_fast − silhouette_score| (same subsample)",
                         abs(L.silhouette_fast(X, ch.labels) - silhouette_score(X[sub], ch.labels[sub])), TOL["exact"]))
        rows.append(_row("metric functions", f"{name}, our labels", "|davies_bouldin − davies_bouldin_score|",
                         abs(L.davies_bouldin(X, ch.labels) - davies_bouldin_score(X, ch.labels)), TOL["exact"]))
        rows.append(_row("metric functions", f"{name}, our labels vs sklearn labels",
                         "|adjusted_rand_index − adjusted_rand_score|",
                         abs(L.adjusted_rand_index(ch.labels, km.labels_) - adjusted_rand_score(ch.labels, km.labels_)),
                         TOL["exact"]))


def compare_cart(df, y, X, rows):
    from sklearn.tree import DecisionTreeClassifier

    from src.ml import learners as L
    from src.ml.experiments.learner_analysis import CART_GRID
    Xm = X["M2"]
    pres = df["presentation"].to_numpy()
    names = list(dict.fromkeys(pres))

    def sk(Xf, yf, d, m):
        return DecisionTreeClassifier(criterion="gini", max_depth=d, min_samples_leaf=m, min_samples_split=2 * m,
                                      random_state=0).fit(Xf, yf)

    for d, m in CART_GRID:
        p_o = L.cart_predict(L.cart_fit(Xm, y, d, m), Xm)
        p_s = sk(Xm, y, d, m).predict_proba(Xm)[:, 1]
        rows.append(_row("CART (Gini)", f"M2, depth={d}, min_leaf={m}, all 2013 rows", "share of identical leaf probabilities",
                         float(np.mean(np.abs(p_o - p_s) < 1e-12)), TOL["agree"], kind="min"))
        rows.append(_row("CART (Gini)", f"M2, depth={d}, min_leaf={m}, all 2013 rows", "class agreement at 0.5",
                         float(np.mean((p_o >= 0.5) == (p_s >= 0.5))), TOL["agree"], kind="min"))
        rows.append(_row("CART (Gini)", f"M2, depth={d}, min_leaf={m}, all 2013 rows", "|Δ ROC-AUC| in sample",
                         abs(L.roc_auc(y, p_o) - L.roc_auc(y, p_s)), TOL["auc"]))
        dd = []
        for held in names:
            tr, te = pres != held, pres == held
            a = L.roc_auc(y[te], L.cart_predict(L.cart_fit(Xm[tr], y[tr], d, m), Xm[te]))
            b = L.roc_auc(y[te], sk(Xm[tr], y[tr], d, m).predict_proba(Xm[te])[:, 1])
            dd.append(abs(a - b))
        rows.append(_row("CART (Gini)", f"M2, depth={d}, min_leaf={m}, LOPO", "max |Δ ROC-AUC| per held-out presentation",
                         max(dd), TOL["auc"]))


def compare_metric_functions(df, y, X, rows):
    from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score

    from src.ml import learners as L
    s = L.logistic_predict(L.logistic_fit(X["M1"], y, 1e-2), X["M1"])
    rows.append(_row("metric functions", "M1 logistic scores, all 2013 rows", "|roc_auc − roc_auc_score|",
                     abs(L.roc_auc(y, s) - roc_auc_score(y, s)), TOL["exact"]))
    rows.append(_row("metric functions", "M1 logistic scores, all 2013 rows", "|brier − brier_score_loss|",
                     abs(L.brier(y, s) - brier_score_loss(y, s)), TOL["exact"]))
    rows.append(_row("metric functions", "M1 logistic scores, all 2013 rows",
                     "|average_precision − average_precision_score|",
                     abs(L.average_precision(y, s) - average_precision_score(y, s)),
                     note="informational: tied scores are handled differently"))
    c = X["M0"][:, 0]                                    # many ties (total clicks)
    rows.append(_row("metric functions", "M0 total clicks (ties), all 2013 rows", "|roc_auc − roc_auc_score|",
                     abs(L.roc_auc(y, c) - roc_auc_score(y, c)), TOL["exact"]))


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--cut", type=int, default=56)
    ap.add_argument("--prepare-only", action="store_true", help="run the data preparation only (no sklearn needed)")
    a = ap.parse_args(argv)
    if not a.prepare_only:
        require_sklearn()
    t0 = time.time()
    pres, df, y, fs, X = prepare(a.cut)
    print(f"[A-5] day {a.cut}: {len(df):,} registrations in {df['presentation'].nunique()} presentations, "
          f"risk rate {y.mean():.3f}; features " + ", ".join(f"{m}={len(c)}" for m, c in fs.items()), flush=True)
    if a.prepare_only:
        return
    import sklearn
    rows = []
    compare_logistic(df, y, X, rows)
    compare_kmeans(df, rows)
    compare_cart(df, y, X, rows)
    compare_metric_functions(df, y, X, rows)
    out = pd.DataFrame(rows)
    out.insert(0, "sklearn_version", sklearn.__version__)
    out["numpy_version"] = np.__version__
    commit, dirty = C.git_commit()
    out["commit"] = commit + (" (dirty)" if dirty else "")
    out["status"] = "post-hoc (A-5), descriptive equivalence check on the 2013 development data"
    p = C.write_csv(out, "sklearn_equivalence.csv")
    n_fail = int((out["pass"] == False).sum())  # noqa: E712
    print(f"[A-5] {len(out)} comparisons, {n_fail} outside tolerance → {p} ({time.time() - t0:.0f}s)")


if __name__ == "__main__":
    main()
