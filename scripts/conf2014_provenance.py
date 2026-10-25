#!/usr/bin/env python3
"""Unified provenance statement for every results/conf2014/ file used in the thesis or the presentation (D-97).

References (decided in D-97, annex of meeting 04):
  * the LOCK file itself must hash to ``LOCK_SHA256`` (ab1c5639…);
  * phase-1 files covered by LOCK (incl. verdicts.csv): the SHA-256 recorded in ``results/conf2014/LOCK``;
  * every other file — phase-2 outputs, and the phase-1 files that are outside LOCK by construction
    (``run_meta.json``, ``deviations.md``; D-75 (1) ``UNLOCKED``) — the blob committed with the E10 results in
    commit ``86c0885`` (read with ``git show``; without git the check refuses, it does not pass silently).

The file list is explicit: the ten §5-8 tables of D-90 (and the appendix file), the seven figures (their companion
CSV, which the derived figures are drawn from, and the original SVG and PNG), and verdicts.csv.
Any mismatch, missing file or unreadable reference refuses (exit status 1) and no statement is written.

Usage:  python3 scripts/conf2014_provenance.py            # verify and write deliverables/06-final-thesis/conf2014_provenance.json
        (also imported by scripts/derive_conf2014_figures.py, which refuses to draw unless verify() passes)
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONF = ROOT / "results" / "conf2014"
OUT = ROOT / "deliverables" / "06-final-thesis" / "conf2014_provenance.json"
LOCK_SHA256 = "ab1c563985703a64bc1d5371b4bdeec7a28cb11e67bcb54632d4106aae16334d"
E10_RESULTS_COMMIT = "86c0885"

FIGS = ["fig1_forest", "fig2_per_presentation", "fig3_signal_ablation", "fig4_models_dev_vs_target", "fig5_roc",
        "fig6_h4b", "fig7_fairness"]
TABLE_FILES = [  # D-90: sources of the ten §5-8 tables, plus intervals_appendix.csv for the appendix
    "run_meta.json", "LOCK", "deviations.md", "folds.csv", "hybrid_2014.json", "verdicts.csv", "per_presentation.csv",
    "h1_decomposition.csv", "per_origin.csv", "ablation_signals.csv", "summary.md", "h4a_auc.csv", "secondary.csv",
    "h4b.csv", "baselines.csv", "hybrid.csv", "sensitivity_E4.csv", "sensitivity_none.csv", "sensitivity_other.csv",
    "ablation_components.csv", "protocol_sampled.csv", "fairness.csv", "intervals_appendix.csv"]
FIGURE_FILES = [f"figures/{f}{ext}" for f in FIGS for ext in (".csv", ".svg", ".png")]
FILES = list(dict.fromkeys(TABLE_FILES + FIGURE_FILES))
USE = {**{f: "table (D-90)" for f in TABLE_FILES}, "intervals_appendix.csv": "appendix (D-90)",
       "verdicts.csv": "table (D-90) and verdict labels of the figures",
       **{f: "figure source (D-95)" for f in FIGURE_FILES if f.endswith(".csv")},
       **{f: "original figure (D-95: the original, kept as is)" for f in FIGURE_FILES if not f.endswith(".csv")}}
UNLOCKED_PHASE1 = {"run_meta.json", "deviations.md"}


class ProvenanceError(RuntimeError):
    pass


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def committed_blob(rel: str) -> bytes:
    try:
        return subprocess.run(["git", "show", f"{E10_RESULTS_COMMIT}:results/conf2014/{rel}"], cwd=ROOT,
                              capture_output=True, check=True).stdout
    except (OSError, subprocess.CalledProcessError) as exc:
        raise ProvenanceError(f"cannot read {rel} at commit {E10_RESULTS_COMMIT}: {exc}") from exc


def verify(files=FILES) -> dict:
    """Check every file against its reference; raise ProvenanceError on the first problem. Returns the statement."""
    lock_path = CONF / "LOCK"
    if not lock_path.is_file():
        raise ProvenanceError("results/conf2014/LOCK is missing")
    lock_bytes = lock_path.read_bytes()
    if sha256_bytes(lock_bytes) != LOCK_SHA256:
        raise ProvenanceError("results/conf2014/LOCK does not match its recorded SHA-256 (ab1c5639…)")
    locked = json.loads(lock_bytes)["files"]
    entries = []
    for rel in files:
        p = CONF / rel
        if not p.is_file():
            raise ProvenanceError(f"results/conf2014/{rel} is missing")
        h = sha256_bytes(p.read_bytes())
        if rel == "LOCK":
            ref, ref_hash = "recorded LOCK SHA-256 (ui_open.json, meeting 04)", LOCK_SHA256
        elif rel in locked:
            ref, ref_hash = "LOCK", locked[rel]
        else:
            why = "phase 1, outside LOCK by construction (UNLOCKED)" if rel in UNLOCKED_PHASE1 else "phase 2"
            ref, ref_hash = f"commit {E10_RESULTS_COMMIT} ({why})", sha256_bytes(committed_blob(rel))
        ok = h == ref_hash
        entries.append({"file": f"results/conf2014/{rel}", "use": USE.get(rel, ""), "sha256": h, "reference": ref,
                        "reference_sha256": ref_hash, "match": ok})
        if not ok:
            raise ProvenanceError(f"results/conf2014/{rel}: SHA-256 {h[:12]}… does not match {ref} ({ref_hash[:12]}…)")
    return {"decision": "D-97 (annex of meeting 04); D-90 tables, D-95 figures",
            "lock_sha256": LOCK_SHA256, "e10_results_commit": E10_RESULTS_COMMIT,
            "references": {"LOCK": "phase-1 files covered by LOCK, incl. verdicts.csv",
                           f"commit {E10_RESULTS_COMMIT}": "phase-2 outputs, and run_meta.json and deviations.md "
                                                          "(phase 1, outside LOCK by construction)"},
            "n_files": len(entries), "all_match": all(e["match"] for e in entries), "files": entries}


def main() -> int:
    try:
        st = verify()
    except ProvenanceError as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 1
    st["generated_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    st["script_sha256"] = sha256_bytes(Path(__file__).read_bytes())
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(st, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    n_lock = sum(e["reference"] == "LOCK" for e in st["files"])
    print(f"{st['n_files']} files, all match: {st['all_match']} (LOCK {n_lock}, commit {E10_RESULTS_COMMIT} "
          f"{sum(e['reference'].startswith('commit') for e in st['files'])}, LOCK file 1) → {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
