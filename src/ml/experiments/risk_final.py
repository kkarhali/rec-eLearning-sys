"""Final risk models for the confirmatory run (D-58) → results/frozen/risk_final.json (+ artifacts/risk_final.json).

    python3 -m src.ml.experiments.risk_final

M0, M1, M2 (Logistic L2) and CART (on M2 features) are trained on the nine 2013 presentations together, after
removing every registration of a student who has a 2014 registration (D-27, D-47). λ of each model = the value
maximising the mean leave-one-presentation-out AUC over the nine; CART (depth, min leaf) likewise.
Youden thresholds are frozen from results/dev2013/learner_meta.json (M0 = 0.4744, M1 = 0.4557, M2 = 0.4074).
Features are z-scored within each presentation over its registrations not withdrawn before the cut (applied
identically at prediction time on 2014). Cut 56 is primary; 28 and 112 are secondary (AUC only).
"""
from __future__ import annotations

import os

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")

import hashlib  # noqa: E402
import json  # noqa: E402
import shutil  # noqa: E402
import time  # noqa: E402

import numpy as np  # noqa: E402

from .. import data, learners as L  # noqa: E402
from .learner_analysis import CART_GRID, LAMBDAS, build_table, feature_sets, standardise  # noqa: E402

FROZEN = data.RESULTS_DIR / "frozen"
OUT = data.RESULTS_DIR / "dev2013"


def lopo_auc(df, X, y, keep, fit, predict):
    pres = df["presentation"].to_numpy()
    aucs = []
    for held in dict.fromkeys(pres):
        tr = (pres != held) & keep
        te = pres == held
        model = fit(X[tr], y[tr])
        aucs.append(L.roc_auc(y[te], predict(model, X[te])))
    return float(np.mean(aucs))


def build(t_c, pres, sa, overlap):
    df = build_table(pres, t_c, sa)
    y = df["y"].to_numpy()
    keep = ~df["id_student"].isin(overlap).to_numpy()
    fs = feature_sets(df)
    out = {"cut": t_c, "n_rows": int(len(df)), "n_training_rows": int(keep.sum()),
           "n_overlap_removed": int((~keep).sum()), "models": {}}
    for m, cols in fs.items():
        X = standardise(df, cols)
        scores = {lam: lopo_auc(df, X, y, keep, lambda A, b, lam=lam: L.logistic_fit(A, b, lam), L.logistic_predict)
                  for lam in LAMBDAS}
        lam = max(scores, key=scores.get)
        w = L.logistic_fit(X[keep], y[keep], lam)
        out["models"][m] = {"features": cols, "weights": w.tolist(), "lambda": lam,
                            "lopo_auc_by_lambda": {str(k): v for k, v in scores.items()}}
    Xc = standardise(df, fs["M2"])
    cs = {f"{d},{lf}": lopo_auc(df, Xc, y, keep, lambda A, b, d=d, lf=lf: L.cart_fit(A, b, d, lf), L.cart_predict)
          for d, lf in CART_GRID}
    best = max(cs, key=cs.get)
    d, lf = map(int, best.split(","))
    out["models"]["CART_M2"] = {"features": fs["M2"], "max_depth": d, "min_leaf": lf,
                                "tree": L.cart_fit(Xc[keep], y[keep], d, lf), "lopo_auc_by_setting": cs}
    return out


def main():
    t0 = time.time()
    pres = data.load_dev_presentations()
    sa = data.load_student_assessment("dev")
    overlap = data.confirmatory_student_ids()
    meta = json.loads((OUT / "learner_meta.json").read_text())
    thr = meta["youden_thresholds_day56"]
    res = {"description": "final risk models (D-58), trained on the nine 2013 presentations after the D-47 overlap "
                          "removal; z-score within presentation (registrations not withdrawn before the cut)",
           "youden_thresholds_day56": {k: round(float(v), 4) for k, v in thr.items()},
           "youden_thresholds_day56_full_precision": thr,
           "target": "final_result in {Fail, Withdrawn} vs {Pass, Distinction}; withdrawn before the cut excluded",
           "primary_cut": 56, "secondary_cuts": [28, 112], "cuts": {}}
    for t_c in (56, 28, 112):
        res["cuts"][str(t_c)] = build(t_c, pres, sa, overlap)
        print(f"[risk_final] cut {t_c} done", flush=True)
    res["seconds"] = round(time.time() - t0, 1)
    FROZEN.mkdir(parents=True, exist_ok=True)
    path = FROZEN / "risk_final.json"
    path.write_text(json.dumps(res, indent=1, default=float))
    art = data.REPO_ROOT / "artifacts"
    art.mkdir(exist_ok=True)
    shutil.copy(path, art / "risk_final.json")
    print(f"[risk_final] → {path} sha256={hashlib.sha256(path.read_bytes()).hexdigest()[:16]} "
          f"({res['seconds']:.0f}s)")


if __name__ == "__main__":
    main()
