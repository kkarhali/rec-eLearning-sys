"""Shared helpers of the session-2 post-hoc analyses (a5–a10), on top of ``_common``.

POST-HOC. Requested by the simulated committee of the second mock-defence session
(docs/defense/session2/r1-alomar.md م-ع-3, م-ع-4; docs/defense/session2/r1-alkanj.md م-ك-1, م-ك-2, م-ك-5).
Outside the registered Holm family (m = 4); descriptive; p uncorrected. Nothing here writes to src/ml/,
results/conf2014/, results/dev2013/, results/frozen/ or results/dryrun2013/.
"""
from __future__ import annotations

import hashlib
import json
import time

import _common as C  # noqa: E402  (sets sys.path)
import numpy as np
import pandas as pd

from src.ml import data, stats
from src.ml.experiments import run_hybrid as RH

FROZEN = ["C7_ClusterPop", "B5_SKNN"]                  # frozen HYB* (floor component last)
NONPERSONAL = ["B3_RecentPop", "C6_AssessProx"]        # (1) + (6): non-personal hybrid of the D-60 decomposition
FLOOR = RH.floor_step(2)                               # 0.25 (D-51)
RULE = ("session-2 committee items (docs/defense/session2/r1-alomar.md, r1-alkanj.md); after the locked E10 run "
        "(LOCK ab1c5639…); allow_confirmatory=True passed explicitly where raw rows are read; no demographic "
        "attribute read")


def log_read(script: str, what: str, presentations) -> None:
    """One append-only line in results/access_log.jsonl (event = "posthoc_read"), same fields as _common."""
    commit, dirty = C.git_commit()
    rec = {"time": time.strftime("%Y-%m-%dT%H:%M:%S"), "event": "posthoc_read", "script": script, "what": what,
           "presentations": sorted(presentations), "commit": commit, "dirty": dirty, "rule": RULE}
    with open(data.RESULTS_DIR / "access_log.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def check_locked_files(names) -> list[dict]:
    """LOCK SHA-256 first, then the SHA-256 of every named results/conf2014 file listed in the LOCK manifest."""
    C.check_lock_sha()
    man = json.loads((C.CONF / "LOCK").read_text())["files"]
    out = []
    for n in names:
        if n not in man:
            out.append({"year": "2014", "check": f"conf2014/{n} not in the LOCK manifest (secondary file; read as is)",
                        "n": 1, "max_abs_diff": float("nan"), "tolerance": float("nan"), "pass": True,
                        "stop_condition": False})
            continue
        h = hashlib.sha256((C.CONF / n).read_bytes()).hexdigest()
        ok = h == man[n]
        print(f"[lock] conf2014/{n}: {'PASS' if ok else 'FAIL'}", flush=True)
        if not ok:
            raise SystemExit(f"results/conf2014/{n} SHA-256 differs from the LOCK manifest: refusing to read it")
        out.append({"year": "2014", "check": f"conf2014/{n} SHA-256 = LOCK manifest", "n": 1, "max_abs_diff": 0.0,
                    "tolerance": 0.0, "pass": True})
    return out


def per_pres(res, col="test_all") -> pd.Series:
    return RH.per_pres(res, col)


def fold_frame(res, model: str, year: str) -> pd.DataFrame:
    return pd.DataFrame([{"year": year, "model": model, "presentation": r["presentation"], "cut": r["cut"],
                          "components": " + ".join(r["combo"]), "weights": json.dumps(r["weights"]),
                          **{f"w_{c}": w for c, w in zip(r["combo"], r["weights"])},
                          "val_NDCG@10": r["val"], "NDCG@10": r["test_all"], "NDCG@10_cold_q1": r["test_cold_q1"],
                          "NDCG@10_top_q4": r["test_top_q4"], "n_seeds": r["n_seeds"]} for r in res])


DEC_LABELS = ["(a) HYB* − non-personal hybrid (1)+(6)", "(b) (7) alone − B3 [partitioning gain]",
              "(c) HYB* − (7) alone [personalisation gain]", "(d) HYB* nominal floor − B3"]


def decomposition(final, nominal, c7, nph, bnp: pd.Series) -> list[dict]:
    """The D-60 decomposition exactly as run_hybrid.frozen_analyses computes it (same order and statistics)."""
    hyb = per_pres(final)
    dec = [(DEC_LABELS[0], hyb - per_pres(nph)), (DEC_LABELS[1], per_pres(c7) - bnp),
           (DEC_LABELS[2], hyb - per_pres(c7)), (DEC_LABELS[3], per_pres(nominal) - bnp)]
    rows = []
    for label, dd in dec:
        dd = dd.dropna()
        c = stats.compare(dd.to_numpy())
        rows.append({"component": label, **c, "n_pos": int((dd > 0).sum()), "n": len(dd)})
    return rows


def check_decomposition(year: str, rows: list[dict], src) -> list[dict]:
    """Reproduce results/<src>/h1_decomposition.csv (mean, CI, percentile CI, p, n_pos) to ≤ 1e-6."""
    ref = pd.read_csv(src / "h1_decomposition.csv").set_index("component")
    got = pd.DataFrame(rows).set_index("component")
    out = []
    for col in ("mean", "ci_lo", "ci_hi", "pct_lo", "pct_hi", "p"):
        out.append({"year": year, **C.check(f"{year} D-60 decomposition {col} (4 rows) vs {src.name}/h1_decomposition.csv",
                                            got[col].astype(float), ref[col].astype(float))})
    ok = bool((got["n_pos"] == ref["n_pos"]).all() and (got["n"] == ref["n"]).all())
    print(f"[reproduction] {year} D-60 decomposition n_pos/n identical: {ok}", flush=True)
    out.append({"year": year, "check": f"{year} D-60 decomposition n_pos and n vs {src.name}/h1_decomposition.csv",
                "n": len(got), "max_abs_diff": 0.0 if ok else float("nan"), "tolerance": 0.0, "pass": ok})
    return out


def check_hybrid_folds(year: str, final, src, label="HYB*") -> list[dict]:
    """HYB* per fold (NDCG@10 and weights) vs results/<src>/hybrid.csv."""
    hl = pd.read_csv(src / "hybrid.csv")
    hl = hl[(hl["model"] == label) & (hl["task"] == "A")].set_index(["presentation", "cut"]).sort_index()
    fz = fold_frame(final, label, year).set_index(["presentation", "cut"]).sort_index()
    out = [{"year": year, **C.check(f"{year} {label} NDCG@10 per fold vs {src.name}/hybrid.csv", fz["NDCG@10"], hl["NDCG@10"])},
           {"year": year, **C.check(f"{year} {label} validation NDCG@10 per fold vs {src.name}/hybrid.csv",
                                    fz["val_NDCG@10"], hl["val_NDCG@10"])}]
    same_w = all(json.loads(a) == json.loads(b) for a, b in zip(fz["weights"], hl.loc[fz.index, "weights"]))
    print(f"[reproduction] {year} {label} weights identical: {same_w}", flush=True)
    out.append({"year": year, "check": f"{year} {label} weights per fold identical to {src.name}/hybrid.csv",
                "n": len(fz), "max_abs_diff": 0.0 if same_w else float("nan"), "tolerance": 0.0, "pass": same_w})
    return out


def require(checks: list[dict], year: str, tool: str) -> None:
    bad = [c["check"] for c in checks if c["year"] == year and c.get("stop_condition", True) and not c["pass"]]
    if bad:
        raise SystemExit(f"[{tool}] reproduction failed for {year} ({bad}); no new number written")


def folds_for(names):
    from src.ml.splits import CUTS
    return [(n, c) for c in sorted(CUTS, reverse=True) for n in names]


def weight_counts(df: pd.DataFrame) -> dict:
    return {k: int(v) for k, v in df["weights"].value_counts().items()}


__all__ = ["C", "np", "pd", "FROZEN", "NONPERSONAL", "FLOOR", "log_read", "check_locked_files", "per_pres",
           "fold_frame", "decomposition", "check_decomposition", "check_hybrid_folds", "require", "folds_for",
           "weight_counts", "DEC_LABELS"]
