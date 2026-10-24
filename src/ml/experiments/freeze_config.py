"""Frozen configuration and the freeze checklist (D-62 ش6, ش10).

    python3 -m src.ml.experiments.freeze_config            # → results/frozen/freeze03_config.json
    python3 -m src.ml.experiments.freeze_config --checklist # → results/frozen/freeze_checklist.md

The config collects every frozen choice: model spaces (B1–B10, GRU-lite, (6), (7), signal family τ/β/α), the
composition, its weight grid and floor rule, B_np* and S*, seeds, bootstrap B and seed, δ, δ_AUC, Holm m, cuts, E,
Youden thresholds, the k rule, the MD5 of the seven raw files, and the SHA-256 of mde80.json, hybrid_frozen.json
and risk_final.json. The checklist reports ش1–ش10 with the path of the evidence for each condition.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import time
from pathlib import Path

from .. import data, harness, signals, stats
from ..models import BASELINES, COMPONENTS, sample_space
from ..models.gru_lite import GRULite
from ..splits import CUTS
from .learner_analysis import CART_GRID, LAMBDAS

FROZEN = data.RESULTS_DIR / "frozen"
DEV = data.RESULTS_DIR / "dev2013"
RAW_FILES = ("assessments.csv", "courses.csv", "studentAssessment.csv", "studentInfo.csv",
             "studentRegistration.csv", "studentVle.csv", "vle.csv")


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def md5(p: Path) -> str:
    h = hashlib.md5()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _jsonable(v):
    if hasattr(v, "key"):
        return v.key
    if isinstance(v, float) and v == float("inf"):
        return "inf"
    return v


def spaces() -> dict:
    out = {}
    for name in list(BASELINES) + list(COMPONENTS):
        cls = BASELINES.get(name) or COMPONENTS[name]
        full = cls.param_space()
        used = harness.model_configs(name) if name in BASELINES else full
        out[name] = {"full_space_size": len(full),
                     "evaluated_settings": [{k: _jsonable(v) for k, v in c.items()} for c in used],
                     "strategy": "grid" if len(full) <= harness.BUDGET else
                     f"random subset of {len(used)} (seed crc32(name) + 20261024)"}
    out["B7_WRMF"]["iteration_checkpoints"] = list(BASELINES["B7_WRMF"].ITER_CHECKPOINTS)
    out["GRU_lite"] = {"settings": [{k: v for k, v in c.items()} for c in GRULite.param_space()],
                       "d_e": 64, "d_h": 64, "T": 20, "batch": 128, "max_epochs": 30, "patience": 3, "l2": 1e-5,
                       "clip": 5.0, "adam": [0.9, 0.999, 1e-8], "status": "passed the sanity gates (gru_sanity.md)"}
    return out


def build_config() -> dict:
    fr = json.loads((DEV / "hybrid_frozen.json").read_text())
    meta = json.loads((DEV / "learner_meta.json").read_text())
    ref = {}
    for line in (data.REPO_ROOT / "data" / "oulad_md5_reference.txt").read_text().splitlines():
        parts = line.split()
        if len(parts) >= 2:
            ref[Path(parts[-1]).name] = parts[0]
    md5s = {f: {"md5": md5(data.RAW_DIR / f), "reference": ref.get(f)} for f in RAW_FILES}
    for v in md5s.values():
        v["match"] = v["md5"] == v["reference"]
    try:
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=data.REPO_ROOT).decode().strip()
    except Exception:
        commit = "unknown"
    cfg = {
        "freeze": "freeze-03 (D-62); specification frozen at meeting 03",
        "presentations": {"development": list(data.DEV_PRESENTATIONS), "confirmatory": list(data.CONF_PRESENTATIONS)},
        "exclusion_set_E": sorted(data.E5), "cuts": list(CUTS), "horizon_days": 14,
        "seeds_tuning": [0], "seeds_report": list(harness.SEEDS), "budget_settings": harness.BUDGET,
        "signal_family": {"tau": [_jsonable(t) for t in signals.TAU_SPACE], "beta": [0.0] + list(signals.BETA_SPACE),
                          "alpha": list(signals.ALPHA_SPACE), "levels": list(signals.LEVELS)},
        "model_spaces": spaces(),
        "hybrid": {"components": fr["components"], "floor_component": fr["floor_component"],
                   "floor_rule": fr["floor_rule"], "weight_grid_points": fr["weight_grid_points"],
                   "accept_only_components": fr["accept_only_components"], "B_np_star": fr["B_np_star"],
                   "S_star": fr["S_star"], "C7_window_space": [3, 7, 14, 21, 28],
                   "H2b": fr.get("H2b")},
        "inference": {"delta_ndcg10": stats.DELTA, "delta_auc": 0.02, "alpha": stats.ALPHA,
                      "holm_family": ["H1", "H2-a", "H3", "H4-a"], "holm_m": 4,
                      "p_value": "two-sided exact sign flip (2^n)", "interval": "cluster bootstrap-t over presentations",
                      "bootstrap_B": 10_000, "bootstrap_seed": 0,
                      "verdict_tables": "D-26 (one-sided H1/H2-a/H4-a; six-level H3)",
                      "inconclusive_text": "غير حاسمة: لا يكشف التصميم بقوة 80% أثراً أصغر من MDE80 = x (D-48)",
                      "degenerate_rule": "D-52"},
        "learners": {"risk_cut_primary": 56, "risk_cuts_secondary": [28, 112],
                     "youden_thresholds_day56": {k: round(float(v), 4) for k, v in meta["youden_thresholds_day56"].items()},
                     "logistic_lambdas": list(LAMBDAS), "cart_grid": [list(x) for x in CART_GRID],
                     "k_rule": "smallest k in top-2 silhouette ∩ top-2 DBI with mean ARI ≥ 0.8 over 5 seeds, else best "
                               "silhouette flagged unstable (§4.7.2, D-39-b); k ∈ [2..8], 10 restarts",
                     "overlap_removal": "D-47 (confirmatory_student_ids)"},
        "raw_md5": md5s,
        "sha256": {p: sha256(DEV / p) for p in ("mde80.json", "hybrid_frozen.json")}
                  | {"risk_final.json": sha256(FROZEN / "risk_final.json")},
        "git_commit_when_written": commit, "date": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    return cfg


def checklist() -> str:
    def ok(b):
        return "✓" if b else "✗"

    fr = json.loads((DEV / "hybrid_frozen.json").read_text()) if (DEV / "hybrid_frozen.json").exists() else {}
    m80 = json.loads((DEV / "mde80.json").read_text()) if (DEV / "mde80.json").exists() else []
    h1 = next((r for r in m80 if r["hypothesis"] == "H1"), None)
    repro = (DEV / "repro_diff.md").read_text() if (DEV / "repro_diff.md").exists() else ""
    dry = data.RESULTS_DIR / "dryrun2013" / "run_meta.json"
    drym = json.loads(dry.read_text()) if dry.exists() else {}
    cfgp = FROZEN / "freeze03_config.json"
    peer = sorted((data.REPO_ROOT / "docs" / "meetings").glob("*peer*freeze*")) + \
        sorted((data.REPO_ROOT / "docs" / "meetings").glob("*peer-signoff-D47*"))
    doc02 = (data.REPO_ROOT / "docs" / "working" / "02-hypotheses-algorithms.md").read_text()
    tags = subprocess.run(["git", "tag", "-l", "freeze-03"], cwd=data.REPO_ROOT, capture_output=True, text=True).stdout.strip()
    rows = [
        ("ش1", "run_hybrid بأرضية D-51 افتراضياً + الملفات", bool(fr.get("floor_rule")) and fr.get("nominal_floor_sensitivity") is not None,
         "results/dev2013/hybrid_frozen.json (floor_rule)، hybrid_acceptance.md", "مهندس ML"),
        ("ش2", "MDE80 لـH1 بالـHYB* الجديد", bool(h1 and "D-51" in h1["pair"]),
         f"results/dev2013/mde80.md (H1 = {h1['MDE80']:.4f})" if h1 else "results/dev2013/mde80.md", "مهندس ML"),
        ("ش3", "الهجين على B؛ M1 افتراضياً؛ وسم «منحلّ»؛ H2-ب غير منطبقة",
         (DEV / "hybrid.csv").exists() and "منحلّ" in (DEV / "hybrid_acceptance.md").read_text() and bool(fr.get("H2b")),
         "hybrid.csv (task B)، serving.py (risk_model=\"M1\")، stats.cluster_bootstrap_t + اختبار، hybrid_frozen.json (H2b)",
         "مهندس ML"),
        ("ش4", "نماذج الخطر النهائية", (FROZEN / "risk_final.json").exists(), "results/frozen/risk_final.json", "مهندس ML"),
        ("ش5", "reproduce_dev + repro_diff.md", "**الحالة: مطابق**" in repro,
         "results/dev2013/repro_diff.md", "مهندس ML"),
        ("ش6", "freeze03_config.json + SHA-256", cfgp.exists(), "results/frozen/freeze03_config.json", "مهندس ML"),
        ("ش7", "run_confirmatory + تشغيل جاف كامل على 2013", drym.get("status") == "completed",
         "src/ml/experiments/run_confirmatory.py، results/dryrun2013/", "مهندس ML"),
        ("ش8", "مراجعة الزميل وتوقيعه", any("موافق" in p.read_text() and "غير موافق في الحالة الحالية" not in p.read_text()
                                            for p in peer), "docs/meetings/*peer*", "الزميل الباحث"),
        ("ش9", "تحديث الوثيقة 02 بالملحق ب وREADME", "جدول 2-ب" in doc02 and "[x_H1]" not in doc02,
         "docs/working/02-hypotheses-algorithms.md، src/ml/README.md", "مصمّم الفرضيات + مهندس ML"),
        ("ش10", "تحقق المشرف وتوقيعه ثم الوسم", tags == "freeze-03", "§8 من محضر الاجتماع 03؛ git tag freeze-03",
         "المشرف ← مهندس ML"),
    ]
    sha = {}
    for p in (cfgp, DEV / "mde80.json", DEV / "hybrid_frozen.json", FROZEN / "risk_final.json"):
        if p.exists():
            sha[p.name] = sha256(p)
    md = ["# قائمة شروط وسم freeze-03 (D-62) — مولَّدة بـ`python3 -m src.ml.experiments.freeze_config --checklist`\n",
          f"الوقت: {time.strftime('%Y-%m-%d %H:%M:%S')}\n",
          "| # | الشرط | الحالة | الدليل | المسؤول |", "|---|---|---|---|---|"]
    md += [f"| {a} | {b} | {ok(c)} | {d} | {e} |" for a, b, c, d, e in rows]
    md += ["", "## SHA-256", *[f"- `{k}`: `{v}`" for k, v in sha.items()]]
    return "\n".join(md)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--checklist", action="store_true")
    a = ap.parse_args(argv)
    FROZEN.mkdir(parents=True, exist_ok=True)
    if a.checklist:
        (FROZEN / "freeze_checklist.md").write_text(checklist(), encoding="utf-8")
        print(FROZEN / "freeze_checklist.md")
        return
    cfg = build_config()
    p = FROZEN / "freeze03_config.json"
    p.write_text(json.dumps(cfg, indent=1, ensure_ascii=False, default=_jsonable))
    print(f"{p} sha256={sha256(p)}")


if __name__ == "__main__":
    main()
