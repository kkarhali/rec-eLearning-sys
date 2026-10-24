"""GRU-lite on the nine development presentations (D-35) → results/dev2013/gru.csv (+ gru_tuning.csv).

    python3 -m src.ml.experiments.run_gru [--presentations ...] [--cuts ...] [--workers 4]

Per (presentation, origin): tune the 6 settings (η × target) with seed 0 and early stopping on validation
NDCG@10 (task A; ≤ 30 epochs, patience 3); refit on ≤ t with the selected epochs for seeds 0–4; evaluate
tasks A and B (B with the task-A setting, D-42). Scores are cached for the hybrid (components.py).
Sensitivity (D-35): d_h = 128 for the selected setting on AAA_2013J, EEE_2013J, GGG_2013J (seed 0).
Requires the sanity gates (results/dev2013/gru_sanity.json) to have passed.
"""
from __future__ import annotations

import os

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")

import argparse  # noqa: E402
import json  # noqa: E402
import multiprocessing as mp  # noqa: E402
import time  # noqa: E402

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from .. import components, data, metrics  # noqa: E402
from ..harness import SEEDS, config_key, eval_rows  # noqa: E402
from ..models.gru_lite import GRULite  # noqa: E402
from ..splits import CUTS, make_fold  # noqa: E402

OUT = data.RESULTS_DIR / "dev2013"
DH128_PRES = ("AAA_2013J", "EEE_2013J", "GGG_2013J")
_PRES: dict = {}


def run_job(args):
    name, cut, seeds = args
    p = _PRES[name]
    t_job = time.time()
    rows, tuning = [], []
    tr, tg = make_fold(p, cut, "tune")
    tA = tg.task("A")
    val_fn = lambda S: metrics.summarize(metrics.evaluate(S, tA[1], tA[0], tA[2], tA[3], tr.tiebreak, ks=(10,)))["NDCG@10"]  # noqa: E731
    best = None
    for cfg in GRULite.param_space():
        t = time.time()
        m = GRULite(seed=seeds[0], **cfg, val_fn=val_fn).fit(tr)
        secs = time.time() - t
        tuning.append({"presentation": name, "cut": cut, "config": config_key(cfg), "best_epoch": m.best_epoch,
                       "val_NDCG@10": m.best_val, "epochs_run": len(m.history), "seconds": secs,
                       "train_loss": json.dumps([round(h["train_loss"], 4) for h in m.history]),
                       "val_curve": json.dumps([round(h["val_ndcg10"], 4) for h in m.history])})
        if best is None or m.best_val > best[0]:
            best = (m.best_val, cfg, m.best_epoch, m)
    val, cfg, ep, mbest = best
    components.save_scores(name, cut, "GRU_lite", "tune", seeds[0], mbest.score())
    tr2, tg2 = make_fold(p, cut, "test")
    views = {t: tg2.task(t) for t in ("A", "B")}
    key = config_key({**cfg, "epochs": ep})
    for s in seeds:
        t = time.time()
        S = GRULite(seed=s, **cfg, epochs=ep).fit(tr2).score()
        secs = time.time() - t
        components.save_scores(name, cut, "GRU_lite", "test", s, S)
        for task in ("A", "B"):
            rows += eval_rows(name, cut, "GRU_lite", task, s, key, val, S, views[task], tr2, secs)
    if name in DH128_PRES:
        t = time.time()
        S = GRULite(seed=seeds[0], **cfg, epochs=ep, dh=128).fit(tr2).score()
        rows += eval_rows(name, cut, "GRU_lite_dh128", "A", seeds[0], key + ";dh=128", np.nan, S, views["A"], tr2,
                          time.time() - t)
    print(f"[gru] {name} t={cut} best={key} val={val:.3f} ({time.time() - t_job:.0f}s)", flush=True)
    return rows, tuning


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--presentations", nargs="*", default=list(data.DEV_PRESENTATIONS))
    ap.add_argument("--cuts", nargs="*", type=int, default=list(CUTS))
    ap.add_argument("--seeds", nargs="*", type=int, default=list(SEEDS))
    ap.add_argument("--workers", type=int, default=4)
    a = ap.parse_args(argv)
    data.assert_allowed(a.presentations)
    sanity = json.loads((OUT / "gru_sanity.json").read_text())
    if not sanity.get("gates_passed"):
        raise SystemExit("GRU-lite has not passed the sanity gates (D-12/D-35): no results are produced.")
    t0 = time.time()
    _PRES.update(data.load_dev_presentations(tuple(a.presentations)))
    order = ["FFF_2013J", "FFF_2013B", "DDD_2013J", "BBB_2013J", "DDD_2013B", "BBB_2013B", "EEE_2013J",
             "GGG_2013J", "AAA_2013J"]
    jobs = [(n, c, tuple(a.seeds)) for c in sorted(a.cuts, reverse=True) for n in order if n in a.presentations]
    with mp.get_context("fork").Pool(a.workers) as pool:
        res = pool.map(run_job, jobs, chunksize=1)
    rows = pd.DataFrame([r for rr, _ in res for r in rr])
    tun = pd.DataFrame([r for _, tt in res for r in tt])
    rows.sort_values(["task", "model", "presentation", "cut", "seed", "slice"]).to_csv(OUT / "gru.csv", index=False,
                                                                                       float_format="%.6f")
    tun.sort_values(["presentation", "cut", "config"]).to_csv(OUT / "gru_tuning.csv", index=False, float_format="%.6f")
    meta = {"wall_seconds": round(time.time() - t0, 1), "cpu_seconds_tune": float(tun["seconds"].sum()),
            "cpu_seconds_test": float(rows[rows["slice"] == "all"].drop_duplicates(["model", "presentation", "cut", "seed"])["fit_score_seconds"].sum()),
            "workers": a.workers, "date": time.strftime("%Y-%m-%d %H:%M:%S")}
    (OUT / "gru_meta.json").write_text(json.dumps(meta, indent=2))
    print(f"[gru] finished in {meta['wall_seconds'] / 60:.1f} min", flush=True)


if __name__ == "__main__":
    main()
