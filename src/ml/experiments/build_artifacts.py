"""Artifacts for the replay service (D-49) → artifacts/<presentation>/<cut>/ (git-ignored; rebuild with this command).

    python3 -m src.ml.experiments.build_artifacts

Per development presentation and cut c ∈ {70, 126, 182}, heavy components of the frozen hybrid are trained on
days ≤ c with the frozen configuration of that (presentation, cut) and seed 0:
  * wrmf.npz  — item factors Y, items, config (learner factors are folded in at request time);
  * gru.npz   — GRU-lite parameters, items, config (learner state = forward pass at request time).
Learner models (teacher dashboard; D-22: risk shown to teachers only):
  * artifacts/<presentation>/risk_<tc>.json — Logistic L2 (M1 and M2) trained on the OTHER eight development
    presentations (overlap-excluded, D-47) at tc ∈ {28, 56, 112}, λ from learner_meta, Youden thresholds;
  * artifacts/<presentation>/clusters_56.npz — day-56 k-means++ centres and z-score parameters (D-39-c).
"""
from __future__ import annotations

import os

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")

import json  # noqa: E402
import time  # noqa: E402

import numpy as np  # noqa: E402

from .. import components as CP, data, learners as L  # noqa: E402
from ..models import BASELINES  # noqa: E402
from ..models.gru_lite import GRULite  # noqa: E402
from ..splits import CUTS, build_train  # noqa: E402
from .learner_analysis import build_table, feature_sets  # noqa: E402

ART = data.REPO_ROOT / "artifacts"
OUT = data.RESULTS_DIR / "dev2013"
HEAVY = ("B7_WRMF", "GRU_lite")


def build_heavy(p, frozen):
    for c in CUTS:
        d = ART / p.name / str(c)
        d.mkdir(parents=True, exist_ok=True)
        tr = build_train(p, c, c, "test")
        cfgs = frozen["component_configs_by_fold"][f"{p.name}_{c}"]
        if "B7_WRMF" in frozen["components"]:
            cfg = CP.parse_config(cfgs["B7_WRMF"])
            m = BASELINES["B7_WRMF"](seed=0, **cfg).fit(tr)
            np.savez(d / "wrmf.npz", Y=m.Y, items=tr.items, config=json.dumps(cfgs["B7_WRMF"]))
        if "GRU_lite" in frozen["components"]:
            cfg = CP.parse_config(cfgs["GRU_lite"])
            m = GRULite(seed=0, **cfg).fit(tr)
            np.savez(d / "gru.npz", items=tr.items, config=json.dumps(cfgs["GRU_lite"]),
                     **{f"p_{k}": v for k, v in m.p.items()})


def build_learner_models(pres, meta):
    sa = data.load_student_assessment("dev")
    overlap = data.confirmatory_student_ids()
    lam = meta.get("lambda_by_heldout_day56", {})
    thr = meta.get("youden_thresholds_day56", {})
    for tc in (28, 56, 112):
        df = build_table(pres, tc, sa)
        fs = feature_sets(df)
        y = df["y"].to_numpy()
        keep = ~df["id_student"].isin(overlap).to_numpy()
        pres_col = df["presentation"].to_numpy()
        Xs, oof = {}, {}
        for m in ("M1", "M2"):
            cols = fs[m]
            X = np.zeros((len(df), len(cols)))
            for _, idx in df.groupby("presentation").indices.items():
                X[idx] = L.zscore(df.iloc[idx][cols].to_numpy(dtype=float))
            Xs[m] = X
            oof[m] = np.full(len(df), np.nan)
            for name in pres:
                lm = float(lam.get(m, {}).get(name, 0.1)) if isinstance(lam.get(m), dict) else 0.1
                tr = (pres_col != name) & keep
                oof[m][pres_col == name] = L.logistic_predict(L.logistic_fit(Xs[m][tr], y[tr], lm), Xs[m][pres_col == name])
        # D-65: the frozen D-58 threshold at day 56; pooled out-of-fold Youden thresholds for the display cuts 28 and 112
        thresholds = {m: (float(thr.get(m, 0.5)), "D-58 frozen (day 56)") if tc == 56 else
                      (L.youden_threshold(y, oof[m]), f"pooled out-of-fold Youden at day {tc} (display only, D-65)")
                      for m in ("M1", "M2")}
        for name in pres:
            out = {"tc": tc, "trained_on": [n for n in pres if n != name], "provenance": "lopo_2013", "models": {}}
            tr = (pres_col != name) & keep
            for m in ("M1", "M2"):
                lm = float(lam.get(m, {}).get(name, 0.1)) if isinstance(lam.get(m), dict) else 0.1
                w = L.logistic_fit(Xs[m][tr], y[tr], lm)
                out["models"][m] = {"features": fs[m], "weights": w.tolist(), "lambda": lm,
                                    "youden_threshold": thresholds[m][0], "threshold_source": thresholds[m][1]}
            (ART / name).mkdir(parents=True, exist_ok=True)
            (ART / name / f"risk_{tc}.json").write_text(json.dumps(out, indent=1))
        if tc == 56:
            for name, idx in df.groupby("presentation").indices.items():
                sub = df.iloc[idx]
                cols = fs["M1"] + ["date_registration"]
                Xr = sub[cols].to_numpy(dtype=float)
                mu, sd = Xr.mean(axis=0), Xr.std(axis=0)
                sd = np.where(sd > 0, sd, 1.0)
                ch = L.choose_k((Xr - mu) / sd)
                np.savez(ART / name / "clusters_56.npz", centres=ch.centres, mu=mu, sd=sd, k=ch.k, stable=ch.stable,
                         features=np.array(cols), students=sub["id_student"].to_numpy(), labels=ch.labels)


def main():
    t0 = time.time()
    frozen = json.loads((OUT / "hybrid_frozen.json").read_text())
    meta = json.loads((OUT / "learner_meta.json").read_text())
    pres = data.load_dev_presentations()
    for p in pres.values():
        build_heavy(p, frozen)
        print(f"[artifacts] heavy {p.name}", flush=True)
    build_learner_models(pres, meta)
    print(f"[artifacts] done in {(time.time() - t0) / 60:.1f} min → {ART}")


if __name__ == "__main__":
    main()
