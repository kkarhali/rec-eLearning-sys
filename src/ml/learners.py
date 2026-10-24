"""Learner analysis in numpy (D-13, D-27, D-28, D-39; draft §4.7).

* behavioural features of a registration up to a cut day (VLE log only for M1; M0 = total clicks;
  M2 = M1 + academic/administrative features);
* k-means++ (10 restarts) with the k rule of draft §4.7.2 (silhouette, Davies–Bouldin, ARI stability
  over 5 seeds; fallback = best silhouette flagged unstable, D-39-b);
* L2-regularised logistic regression (Newton/IRLS, unpenalised intercept);
* CART (Gini, depth ≤ 4, min leaf size);
* ROC-AUC (Mann–Whitney with mid-ranks), PR-AUC (average precision), Brier, Youden threshold,
  balanced accuracy, F1, FNR/FPR.
No sensitive attribute is ever used as a feature (D-21).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .data import EXCLUSION_SETS

ALL_TYPES = ("dataplus", "dualpane", "externalquiz", "folder", "forumng", "glossary", "homepage",
             "oucollaborate", "oucontent", "ouelluminate", "ouwiki", "page", "questionnaire", "quiz",
             "repeatactivity", "resource", "sharedsubpage", "subpage", "url")


# =============================================================================================
# features
# =============================================================================================
def vle_features(events: pd.DataFrame, students: np.ndarray, t_c: int) -> pd.DataFrame:
    """M1 features from the VLE log with date ≤ t_c (all activity types, navigation included).

    active_days, gap_sd (SD of gaps between consecutive active days; 0 if < 2 days), first_day
    (t_c + 1 when no activity, documented), share_<type> click shares (0 when no clicks).
    """
    ev = events[events["date"] <= t_c]
    out = pd.DataFrame(index=pd.Index(students, name="id_student"))
    days = ev[["id_student", "date"]].drop_duplicates().sort_values(["id_student", "date"])
    out["active_days"] = days.groupby("id_student").size().reindex(out.index).fillna(0).to_numpy()
    gaps = days.groupby("id_student")["date"].diff()
    gsd = gaps.groupby(days["id_student"]).std(ddof=0)
    out["gap_sd"] = gsd.reindex(out.index).fillna(0.0).to_numpy()
    out["first_day"] = days.groupby("id_student")["date"].min().reindex(out.index).fillna(t_c + 1).to_numpy()
    tot = ev.groupby("id_student")["clicks"].sum().reindex(out.index).fillna(0).to_numpy()
    by_type = ev.groupby(["id_student", ev["activity_type"].astype(str)])["clicks"].sum().unstack(fill_value=0)
    by_type = by_type.reindex(index=out.index, columns=list(ALL_TYPES), fill_value=0).to_numpy(dtype=float)
    shares = np.divide(by_type, tot[:, None], out=np.zeros_like(by_type), where=tot[:, None] > 0)
    for j, t in enumerate(ALL_TYPES):
        out[f"share_{t}"] = shares[:, j]
    return out


def total_clicks(events: pd.DataFrame, students: np.ndarray, t_c: int) -> pd.DataFrame:
    ev = events[events["date"] <= t_c]
    tot = ev.groupby("id_student")["clicks"].sum()
    return pd.DataFrame({"total_clicks": tot.reindex(students).fillna(0).to_numpy()},
                        index=pd.Index(students, name="id_student"))


def academic_features(p, students: np.ndarray, t_c: int, student_assessment: pd.DataFrame) -> pd.DataFrame:
    """M2 additions: on-time ratio and mean score of assessments known before t_c; prior attempts;
    studied credits; registration day. Missing → on_time = 0 if something was due, else 1; score → 0
    with an indicator ``no_score`` (documented)."""
    out = pd.DataFrame(index=pd.Index(students, name="id_student"))
    asm = p.assessments.dropna(subset=["date"])
    due = asm[asm["date"] <= t_c]
    sa = student_assessment[student_assessment["id_assessment"].isin(p.assessments["id_assessment"])]
    sa = sa[sa["id_student"].isin(students)]
    sub = sa[sa["date_submitted"] <= t_c]
    if len(due):
        m = sub.merge(due[["id_assessment", "date"]], on="id_assessment")
        on_time = (m["date_submitted"] <= m["date"]).groupby(m["id_student"]).sum()
        out["on_time_ratio"] = (on_time.reindex(out.index).fillna(0) / len(due)).to_numpy()
    else:
        out["on_time_ratio"] = 1.0
    sc = sub.groupby("id_student")["score"].mean()
    out["mean_score"] = sc.reindex(out.index).fillna(0.0).to_numpy()
    out["no_score"] = (~out.index.isin(sc.index)).astype(float)
    info = p.students.set_index("id_student")
    out["num_of_prev_attempts"] = info["num_of_prev_attempts"].reindex(out.index).fillna(0).to_numpy()
    out["studied_credits"] = info["studied_credits"].reindex(out.index).fillna(0).to_numpy()
    reg = p.registrations.set_index("id_student")["date_registration"]
    out["date_registration"] = reg.reindex(out.index).fillna(reg.median()).to_numpy()
    return out


def zscore(X: np.ndarray) -> np.ndarray:
    mu = X.mean(axis=0)
    sd = X.std(axis=0)
    return (X - mu) / np.where(sd > 0, sd, 1.0)


# =============================================================================================
# k-means++
# =============================================================================================
def kmeans_pp_init(X: np.ndarray, k: int, rng) -> np.ndarray:
    n = len(X)
    C = [X[rng.integers(n)]]
    d2 = ((X - C[0]) ** 2).sum(axis=1)
    for _ in range(1, k):
        probs = d2 / d2.sum() if d2.sum() > 0 else np.full(n, 1.0 / n)
        C.append(X[rng.choice(n, p=probs)])
        d2 = np.minimum(d2, ((X - C[-1]) ** 2).sum(axis=1))
    return np.array(C)


def lloyd(X, C, max_iter: int = 100):
    for _ in range(max_iter):
        d = ((X[:, None, :] - C[None, :, :]) ** 2).sum(axis=2)
        lab = d.argmin(axis=1)
        newC = np.array([X[lab == j].mean(axis=0) if (lab == j).any() else C[j] for j in range(len(C))])
        if np.allclose(newC, C):
            C = newC
            break
        C = newC
    d = ((X[:, None, :] - C[None, :, :]) ** 2).sum(axis=2)
    lab = d.argmin(axis=1)
    return lab, C, float(d[np.arange(len(X)), lab].sum())


def kmeans(X: np.ndarray, k: int, seed: int = 0, n_init: int = 10):
    """Best of n_init k-means++ runs (lowest within-cluster SS). Returns (labels, centres, inertia)."""
    rng = np.random.default_rng(seed)
    best = None
    for _ in range(n_init):
        lab, C, sse = lloyd(X, kmeans_pp_init(X, k, rng))
        if best is None or sse < best[2]:
            best = (lab, C, sse)
    return best


def silhouette(X: np.ndarray, lab: np.ndarray, max_n: int = 3000, seed: int = 0) -> float:
    n = len(X)
    idx = np.arange(n) if n <= max_n else np.random.default_rng(seed).choice(n, max_n, replace=False)
    Xs, ls = X[idx], lab[idx]
    D = np.sqrt(np.maximum(((Xs[:, None, :] - Xs[None, :, :]) ** 2).sum(axis=2), 0.0))
    ks = np.unique(ls)
    if len(ks) < 2:
        return float("nan")
    s = np.zeros(len(Xs))
    for i in range(len(Xs)):
        same = ls == ls[i]
        a = D[i, same].sum() / max(same.sum() - 1, 1)
        b = min(D[i, ls == k].mean() for k in ks if k != ls[i])
        s[i] = 0.0 if same.sum() == 1 else (b - a) / max(a, b)
    return float(s.mean())


def silhouette_fast(X: np.ndarray, lab: np.ndarray, max_n: int = 3000, seed: int = 0) -> float:
    """Vectorised silhouette (identical definition to :func:`silhouette`)."""
    n = len(X)
    idx = np.arange(n) if n <= max_n else np.random.default_rng(seed).choice(n, max_n, replace=False)
    Xs, ls = X[idx], lab[idx]
    sq = (Xs ** 2).sum(axis=1)
    D = np.sqrt(np.maximum(sq[:, None] + sq[None, :] - 2 * Xs @ Xs.T, 0.0))
    ks = np.unique(ls)
    if len(ks) < 2:
        return float("nan")
    onehot = (ls[:, None] == ks[None, :]).astype(float)
    sums = D @ onehot                                   # n × k
    cnt = onehot.sum(axis=0)
    own = np.searchsorted(ks, ls)
    a = sums[np.arange(len(ls)), own] / np.maximum(cnt[own] - 1, 1)
    mean_other = sums / cnt[None, :]
    mean_other[np.arange(len(ls)), own] = np.inf
    b = mean_other.min(axis=1)
    s = np.where(cnt[own] > 1, (b - a) / np.maximum(np.maximum(a, b), 1e-12), 0.0)
    return float(s.mean())


def davies_bouldin(X: np.ndarray, lab: np.ndarray) -> float:
    ks = np.unique(lab)
    C = np.array([X[lab == k].mean(axis=0) for k in ks])
    S = np.array([np.sqrt(((X[lab == k] - C[j]) ** 2).sum(axis=1)).mean() for j, k in enumerate(ks)])
    D = np.sqrt(((C[:, None, :] - C[None, :, :]) ** 2).sum(axis=2))
    R = (S[:, None] + S[None, :]) / np.where(D > 0, D, np.inf)
    np.fill_diagonal(R, -np.inf)
    return float(R.max(axis=1).mean())


def adjusted_rand_index(a: np.ndarray, b: np.ndarray) -> float:
    _, ai = np.unique(a, return_inverse=True)
    _, bi = np.unique(b, return_inverse=True)
    M = np.zeros((ai.max() + 1, bi.max() + 1))
    np.add.at(M, (ai, bi), 1)
    comb = lambda x: x * (x - 1) / 2.0  # noqa: E731
    sum_ij = comb(M).sum()
    sa, sb = comb(M.sum(axis=1)).sum(), comb(M.sum(axis=0)).sum()
    n = len(a)
    exp = sa * sb / comb(n)
    mx = 0.5 * (sa + sb)
    return float((sum_ij - exp) / (mx - exp)) if mx != exp else 1.0


@dataclass
class ClusterChoice:
    k: int
    labels: np.ndarray
    centres: np.ndarray
    stable: bool
    table: pd.DataFrame


def choose_k(X: np.ndarray, ks=range(2, 9), seeds=(0, 1, 2, 3, 4), n_init: int = 10,
             label_seed: int = 0, ari_min: float = 0.8) -> ClusterChoice:
    """Draft §4.7.2 rule: smallest k in the top-2 of both silhouette and DBI with mean ARI ≥ 0.8;
    otherwise the best silhouette, flagged unstable (D-39-b). Labels/centres from ``label_seed``."""
    rows, fits = [], {}
    for k in ks:
        runs = [kmeans(X, k, seed=s, n_init=n_init) for s in seeds]
        fits[k] = runs
        ref = runs[seeds.index(label_seed) if label_seed in seeds else 0]
        aris = [adjusted_rand_index(runs[i][0], runs[j][0]) for i in range(len(runs)) for j in range(i + 1, len(runs))]
        rows.append({"k": k, "silhouette": silhouette_fast(X, ref[0]), "dbi": davies_bouldin(X, ref[0]),
                     "ari_mean": float(np.mean(aris)) if aris else 1.0})
    tab = pd.DataFrame(rows)
    top_sil = set(tab.nlargest(2, "silhouette")["k"])
    top_dbi = set(tab.nsmallest(2, "dbi")["k"])
    ok = tab[tab["k"].isin(top_sil & top_dbi) & (tab["ari_mean"] >= ari_min)]
    if len(ok):
        k, stable = int(ok["k"].min()), True
    else:
        k, stable = int(tab.loc[tab["silhouette"].idxmax(), "k"]), False
    runs = fits[k]
    lab, C, _ = runs[seeds.index(label_seed) if label_seed in seeds else 0]
    return ClusterChoice(k, lab, C, stable, tab)


# =============================================================================================
# logistic regression (L2) and CART
# =============================================================================================
def logistic_fit(X: np.ndarray, y: np.ndarray, lam: float, max_iter: int = 50, tol: float = 1e-8):
    """min −mean loglik + (λ/2)‖w‖², intercept unpenalised; Newton steps with backtracking."""
    n, d = X.shape
    Xb = np.hstack([np.ones((n, 1)), X])
    w = np.zeros(d + 1)
    R = lam * np.eye(d + 1)
    R[0, 0] = 0.0

    def obj(w):
        z = Xb @ w
        return float(np.mean(np.logaddexp(0, z) - y * z) + 0.5 * w @ R @ w)

    f = obj(w)
    for _ in range(max_iter):
        pr = 1.0 / (1.0 + np.exp(-(Xb @ w)))
        g = Xb.T @ (pr - y) / n + R @ w
        H = (Xb * (pr * (1 - pr))[:, None]).T @ Xb / n + R + 1e-10 * np.eye(d + 1)
        step = np.linalg.solve(H, g)
        t = 1.0
        while True:
            w_new = w - t * step
            f_new = obj(w_new)
            if f_new <= f + 1e-12 or t < 1e-6:
                break
            t *= 0.5
        if abs(f - f_new) < tol:
            w, f = w_new, f_new
            break
        w, f = w_new, f_new
    return w


def logistic_predict(w: np.ndarray, X: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-(w[0] + X @ w[1:])))


def gini(y: np.ndarray) -> float:
    if len(y) == 0:
        return 0.0
    p = y.mean()
    return 1.0 - p * p - (1 - p) * (1 - p)


def cart_fit(X: np.ndarray, y: np.ndarray, max_depth: int = 4, min_leaf: int = 20, depth: int = 0):
    """Binary CART with Gini; returns a nested dict; leaves hold the positive rate."""
    node = {"n": len(y), "p": float(y.mean()) if len(y) else 0.0}
    if depth >= max_depth or len(y) < 2 * min_leaf or node["p"] in (0.0, 1.0):
        return node
    best = (0.0, None, None)
    g0 = gini(y)
    for j in range(X.shape[1]):
        order = np.argsort(X[:, j], kind="stable")
        xs, ys = X[order, j], y[order]
        csum = np.cumsum(ys)
        n = len(ys)
        pos = np.arange(1, n)
        valid = (xs[1:] != xs[:-1]) & (pos >= min_leaf) & (n - pos >= min_leaf)
        if not valid.any():
            continue
        nl = pos[valid].astype(float)
        pl = csum[:-1][valid] / nl
        pr = (csum[-1] - csum[:-1][valid]) / (n - nl)
        gl = 1 - pl ** 2 - (1 - pl) ** 2
        gr = 1 - pr ** 2 - (1 - pr) ** 2
        gain = g0 - (nl * gl + (n - nl) * gr) / n
        b = int(np.argmax(gain))
        if gain[b] > best[0]:
            i = pos[valid][b]
            best = (float(gain[b]), j, float((xs[i - 1] + xs[i]) / 2))
    if best[1] is None:
        return node
    j, thr = best[1], best[2]
    left = X[:, j] <= thr
    node.update(feature=j, threshold=thr, gain=best[0],
                left=cart_fit(X[left], y[left], max_depth, min_leaf, depth + 1),
                right=cart_fit(X[~left], y[~left], max_depth, min_leaf, depth + 1))
    return node


def cart_predict(node: dict, X: np.ndarray) -> np.ndarray:
    out = np.empty(len(X))
    for r in range(len(X)):
        nd = node
        while "feature" in nd:
            nd = nd["left"] if X[r, nd["feature"]] <= nd["threshold"] else nd["right"]
        out[r] = nd["p"]
    return out


def cart_rules(node: dict, names, depth: int = 0) -> list[str]:
    pad = "  " * depth
    if "feature" not in node:
        return [f"{pad}→ P(risk) = {node['p']:.2f} (n = {node['n']})"]
    f = names[node["feature"]]
    return ([f"{pad}if {f} ≤ {node['threshold']:.3g}:"] + cart_rules(node["left"], names, depth + 1)
            + [f"{pad}else ({f} > {node['threshold']:.3g}):"] + cart_rules(node["right"], names, depth + 1))


# =============================================================================================
# classification metrics
# =============================================================================================
def _mid_ranks(x: np.ndarray) -> np.ndarray:
    order = np.argsort(x, kind="stable")
    r = np.empty(len(x))
    r[order] = np.arange(1, len(x) + 1)
    _, inv = np.unique(x, return_inverse=True)
    return (np.bincount(inv, weights=r) / np.bincount(inv))[inv]


def roc_auc(y: np.ndarray, s: np.ndarray) -> float:
    y = np.asarray(y).astype(bool)
    n1, n0 = y.sum(), (~y).sum()
    if n1 == 0 or n0 == 0:
        return float("nan")
    r = _mid_ranks(np.asarray(s, dtype=float))
    return float((r[y].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))


def average_precision(y: np.ndarray, s: np.ndarray) -> float:
    y = np.asarray(y).astype(bool)
    order = np.argsort(-np.asarray(s, dtype=float), kind="stable")
    ys = y[order]
    tp = np.cumsum(ys)
    prec = tp / np.arange(1, len(ys) + 1)
    return float((prec * ys).sum() / max(ys.sum(), 1))


def youden_threshold(y: np.ndarray, s: np.ndarray) -> float:
    y = np.asarray(y).astype(bool)
    thr = np.unique(s)
    best, bt = -1.0, 0.5
    P, N = y.sum(), (~y).sum()
    order = np.argsort(-s, kind="stable")
    ss, ys = s[order], y[order]
    tp = np.cumsum(ys)
    fp = np.cumsum(~ys)
    last = np.r_[ss[1:] != ss[:-1], True]           # predict positive for s ≥ ss[i]
    J = tp[last] / max(P, 1) - fp[last] / max(N, 1)
    i = int(np.argmax(J))
    del thr, best, bt
    return float(ss[last][i])


def threshold_metrics(y: np.ndarray, s: np.ndarray, thr: float) -> dict:
    y = np.asarray(y).astype(bool)
    pred = s >= thr
    tp, fp = (pred & y).sum(), (pred & ~y).sum()
    fn, tn = (~pred & y).sum(), (~pred & ~y).sum()
    tpr = tp / max(tp + fn, 1)
    tnr = tn / max(tn + fp, 1)
    prec = tp / max(tp + fp, 1)
    return {"balanced_accuracy": float((tpr + tnr) / 2), "F1": float(2 * prec * tpr / max(prec + tpr, 1e-12)),
            "FNR": float(1 - tpr), "FPR": float(1 - tnr)}


def brier(y, s) -> float:
    return float(np.mean((np.asarray(s, dtype=float) - np.asarray(y, dtype=float)) ** 2))


NAV_TYPES = tuple(sorted(EXCLUSION_SETS["E5"]))
