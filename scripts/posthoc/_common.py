"""Shared helpers of the post-hoc analyses requested by the mock-defence committee (A-4, A-5).

POST-HOC. Everything in scripts/posthoc/ is outside the registered Holm family (m = 4) and outside the frozen
protocol; results are descriptive. Nothing here writes to src/ml/, results/conf2014/, results/dev2013/,
results/frozen/ or results/dryrun2013/: outputs go to results/posthoc/ only, and 2014 rows are read only with an
explicit ``allow_confirmatory=True`` after the locked E10 run (each such read is appended to
results/access_log.jsonl with ``event = "posthoc_read"``).
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from src.ml import components as CP, data, stats  # noqa: E402

OUT = ROOT / "results" / "posthoc"
DEV = ROOT / "results" / "dev2013"
CONF = ROOT / "results" / "conf2014"
CACHE_DEV = data.CACHE_DIR / "components"                     # 2013 component scores (run_hybrid / reproduce_dev)
CACHE_CONF = data.CACHE_DIR / "components_conf2014" / "E5"    # 2014 component scores of the E10 run (main analysis E5)
LOCK_SHA256 = "ab1c563985703a64bc1d5371b4bdeec7a28cb11e67bcb54632d4106aae16334d"
TOL = 1e-6                                                    # reproduction tolerance (CSV files hold 6 decimals)
POSTHOC_NOTE = "post-hoc; outside the Holm family (m = 4); descriptive; p uncorrected"


def git_commit() -> tuple[str, bool]:
    try:
        c = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, stderr=subprocess.DEVNULL).decode().strip()
        dirty = bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT,
                                             stderr=subprocess.DEVNULL).decode().strip())
        return c, dirty
    except Exception:
        return "unknown", True


def log_posthoc_read(script: str, what: str, presentations) -> None:
    """Append one line to results/access_log.jsonl for a post-lock read of 2014 rows (append only)."""
    commit, dirty = git_commit()
    rec = {"time": time.strftime("%Y-%m-%dT%H:%M:%S"), "event": "posthoc_read", "script": script, "what": what,
           "presentations": sorted(presentations), "commit": commit, "dirty": dirty,
           "rule": "committee condition A-4 (mock defence); after the locked E10 run (LOCK ab1c5639…); "
                   "allow_confirmatory=True passed explicitly; no demographic attribute read"}
    with open(data.RESULTS_DIR / "access_log.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def check_lock_sha() -> None:
    import hashlib
    h = hashlib.sha256((CONF / "LOCK").read_bytes()).hexdigest()
    if h != LOCK_SHA256:
        raise SystemExit(f"results/conf2014/LOCK SHA-256 {h} != {LOCK_SHA256}: refusing to read locked results")


def pres_means(df: pd.DataFrame, model: str, task="A", slice_="all", metric="NDCG@10", **filt) -> pd.Series:
    """Unit of analysis (as run_confirmatory.pres_means): seeds → origins → presentation."""
    r = df[(df["model"] == model) & (df["task"] == task) & (df["slice"] == slice_)]
    for k, v in filt.items():
        r = r[r[k] == v]
    return r.groupby(["presentation", "cut"])[metric].mean().groupby("presentation").mean().sort_index()


def fold_means(df: pd.DataFrame, value: str) -> pd.Series:
    return df.groupby(["presentation", "cut"])[value].mean().groupby("presentation").mean().sort_index()


def pair_stats(diff: pd.Series, label: str, year: str, **extra) -> list[dict]:
    """Same inference as H1/H3: cluster bootstrap-t over presentations (B = 10,000, seed 0) and the exact
    two-sided sign-flip p (uncorrected); plus the course-level resampling of table 5-8-هـ (D-31)."""
    d = diff.dropna().sort_index()
    rows = []
    c = stats.compare(d.to_numpy())
    rows.append({"comparison": label, "year": year, "unit": "presentation", "n_units": len(d), "mean": c["mean"],
                 "ci_lo": c["ci_lo"], "ci_hi": c["ci_hi"], "degenerate": c["degenerate"], "pct_lo": c["pct_lo"],
                 "pct_hi": c["pct_hi"], "p_signflip_uncorrected": c["p"], "n_pos": int((d > 0).sum()),
                 "sd": float(np.std(d, ddof=1)), "status": POSTHOC_NOTE, **extra})
    module = d.index.str.split("_").str[0]
    dm = d.groupby(module).mean()
    c = stats.compare(dm.to_numpy())
    rows.append({"comparison": label, "year": year, "unit": "course (D-31 robustness, table 5-8-هـ)",
                 "n_units": len(dm), "mean": c["mean"], "ci_lo": c["ci_lo"], "ci_hi": c["ci_hi"],
                 "degenerate": c["degenerate"], "pct_lo": c["pct_lo"], "pct_hi": c["pct_hi"],
                 "p_signflip_uncorrected": c["p"], "n_pos": int((dm > 0).sum()), "sd": float(np.std(dm, ddof=1)),
                 "status": POSTHOC_NOTE, **extra})
    return rows


def use_cache(year: str) -> Path:
    """Point the component cache of src.ml at the 2013 or the 2014 (E5) scores (module attribute, no file change)."""
    CP.COMP_DIR = CACHE_DEV if year == "2013" else CACHE_CONF
    return CP.COMP_DIR


def write_csv(df: pd.DataFrame, name: str) -> Path:
    OUT.mkdir(parents=True, exist_ok=True)
    p = OUT / name
    df.to_csv(p, index=False, float_format="%.6f")
    return p


def check(label: str, got: pd.Series, ref: pd.Series, tol: float = TOL) -> dict:
    j = pd.concat([got.rename("got"), ref.rename("ref")], axis=1)
    if j.isna().any().any():
        raise SystemExit(f"[reproduction] {label}: index mismatch\n{j}")
    diff = float((j["got"] - j["ref"]).abs().max())
    ok = diff <= tol
    print(f"[reproduction] {label}: n={len(j)} max|Δ|={diff:.2e} → {'PASS' if ok else 'FAIL'}", flush=True)
    return {"check": label, "n": len(j), "max_abs_diff": diff, "tolerance": tol, "pass": ok}
