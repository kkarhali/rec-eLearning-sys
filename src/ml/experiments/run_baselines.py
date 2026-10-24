"""B1–B9 on the nine development presentations (2013), origins 70/126/182, tasks A and B.

    python3 -m src.ml.experiments.run_baselines                # full run (≈ see README)
    python3 -m src.ml.experiments.run_baselines --presentations FFF_2013J --cuts 70 --models B2_Pop B3_RecentPop

Outputs (results/dev2013/ by default): baselines.csv, tuning.csv, timing.csv, folds.csv,
run_meta.json and summary.md. The 2014 presentations are refused by the data layer (D-09).
"""
from __future__ import annotations

import os

# one BLAS thread per worker process: many small solves parallelise better across processes
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")

import argparse  # noqa: E402
import json  # noqa: E402
import multiprocessing as mp  # noqa: E402
import platform  # noqa: E402
import subprocess  # noqa: E402
import time  # noqa: E402
from pathlib import Path  # noqa: E402

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from .. import data  # noqa: E402
from ..harness import SEEDS, run_job  # noqa: E402
from ..models import BASELINES  # noqa: E402
from ..splits import CUTS  # noqa: E402
from .report import build_summary  # noqa: E402

_PRES: dict = {}
# rough cost order for load balancing (largest presentations first)
_COST_ORDER = ["FFF_2013J", "FFF_2013B", "DDD_2013J", "DDD_2013B", "BBB_2013J", "BBB_2013B",
               "EEE_2013J", "GGG_2013J", "AAA_2013J"]


def _worker(args):
    name, cut, models, exclusion, seeds = args
    t = time.time()
    res = run_job(_PRES[name], cut, models, exclusion=exclusion, seeds=seeds)
    print(f"[run] {name} t={cut} done in {time.time() - t:.0f}s", flush=True)
    return res


def git_commit() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=data.REPO_ROOT,
                                       stderr=subprocess.DEVNULL).decode().strip()
    except Exception:
        return "unknown"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--presentations", nargs="*", default=list(data.DEV_PRESENTATIONS))
    ap.add_argument("--cuts", nargs="*", type=int, default=list(CUTS))
    ap.add_argument("--models", nargs="*", default=list(BASELINES))
    ap.add_argument("--seeds", nargs="*", type=int, default=list(SEEDS))
    ap.add_argument("--exclusion", default="E5", choices=list(data.EXCLUSION_SETS))
    ap.add_argument("--workers", type=int, default=min(4, os.cpu_count() or 1))
    ap.add_argument("--out", default=str(data.RESULTS_DIR / "dev2013"))
    a = ap.parse_args(argv)

    data.assert_allowed(a.presentations)          # D-09 guard: refuses any 2014 presentation
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    _PRES.update(data.load_dev_presentations(tuple(a.presentations)))
    print(f"[run] data ready in {time.time() - t0:.1f}s", flush=True)

    order = sorted(a.presentations, key=lambda n: _COST_ORDER.index(n) if n in _COST_ORDER else 99)
    jobs = [(n, c, a.models, a.exclusion, tuple(a.seeds)) for c in sorted(a.cuts, reverse=True) for n in order]
    if a.workers > 1:
        with mp.get_context("fork").Pool(a.workers) as pool:
            results = pool.map(_worker, jobs, chunksize=1)
    else:
        results = [_worker(j) for j in jobs]

    rows = pd.DataFrame([r for res in results for r in res.rows])
    tuning = pd.DataFrame([r for res in results for r in res.tuning])
    timing = pd.DataFrame([r for res in results for r in res.timing])
    folds = pd.DataFrame([r for res in results for r in res.folds])
    sort_cols = ["task", "model", "presentation", "cut", "seed", "slice"]
    rows.sort_values(sort_cols).to_csv(out / "baselines.csv", index=False, float_format="%.6f")
    tuning.sort_values(["model", "presentation", "cut", "config"]).to_csv(out / "tuning.csv", index=False,
                                                                          float_format="%.6f")
    timing.sort_values(["model", "presentation", "cut", "phase"]).to_csv(out / "timing.csv", index=False,
                                                                         float_format="%.3f")
    folds.sort_values(["presentation", "cut"]).to_csv(out / "folds.csv", index=False, float_format="%.6f")
    wall = time.time() - t0
    meta = {
        "command": "python3 -m src.ml.experiments.run_baselines " + " ".join(argv or []),
        "args": vars(a), "git_commit": git_commit(), "data_fingerprint": data.raw_fingerprint(),
        "python": platform.python_version(), "numpy": np.__version__, "pandas": pd.__version__,
        "wall_seconds": round(wall, 1), "workers": a.workers,
        "date": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    (out / "run_meta.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False))
    build_summary(out)
    print(f"[run] finished in {wall / 60:.1f} min → {out}", flush=True)


if __name__ == "__main__":
    main()
