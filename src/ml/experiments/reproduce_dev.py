"""One command that reproduces every development result from an empty cache (D-62 ش5).

    python3 -m src.ml.experiments.reproduce_dev            # full run (≈ 50 min on 4 cores)
    python3 -m src.ml.experiments.reproduce_dev --diff-only # recompute repro_diff.md against the last snapshot

Steps (each in a fresh process, in this order):
  1 eda   2 run_baselines   3 gru_sanity   4 run_gru   5 run_ablation   6 learner_analysis   7 run_hybrid
  8 power   9 risk_final + build_artifacts (artifacts/ is outside git and rebuilt here, D-70)
  then freeze_config, report and the checklist.
Before running, results/dev2013/ and results/frozen/ are copied to data/repro_snapshot/ and data/cache/ is
emptied. Afterwards every file is compared with its snapshot; only volatile fields (timings, dates, commit,
memory, speed) are masked. Any other difference is listed in results/dev2013/repro_diff.md (status
"مطابق" = identical, otherwise "فروق").
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

import pandas as pd

from .. import data

DEV = data.RESULTS_DIR / "dev2013"
FROZEN = data.RESULTS_DIR / "frozen"
SNAP = data.REPO_ROOT / "data" / "repro_snapshot"
STEPS = ["eda", "run_baselines", "gru_sanity", "run_gru", "run_ablation", "learner_analysis", "run_hybrid",
         "power", "risk_final", "build_artifacts", "freeze_config", "report"]
VOLATILE_COLS = {"fit_score_seconds", "seconds", "maxrss_mb", "seconds_total"}
VOLATILE_KEYS = {"wall_seconds", "cpu_seconds", "cpu_seconds_tune", "cpu_seconds_test", "seconds", "seconds_total",
                 "date", "git_commit", "git_commit_at_freeze_run", "git_commit_when_written", "command",
                 "positions_per_second", "maxrss_mb"}
MASKS = [
    (re.compile(r"\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}"), "<TIME>"),
    (re.compile(r"\b[0-9a-f]{10,40}\b"), "<HASH>"),
    (re.compile(r"\d+(\.\d+)?\s*(دقيقة|دقائق|ث\b|s\b|ثانية)"), "<DUR>"),
    (re.compile(r"[\d,]+ خطوة \(متعلم، يوم\) في الثانية"), "<SPEED>"),
    (re.compile(r"\(\d+ ث لـ\d+ دورات"), "(<DUR>"),
]


def git_state():
    try:
        c = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=data.REPO_ROOT).decode().strip()
        dirty = bool(subprocess.check_output(["git", "status", "--porcelain", "--", "src"], cwd=data.REPO_ROOT).decode().strip())
    except Exception:
        c, dirty = "unknown", None
    return c, dirty


def _mask(text: str) -> str:
    for rx, rep in MASKS:
        text = rx.sub(rep, text)
    return text


def _strip(obj):
    if isinstance(obj, dict):
        return {k: _strip(v) for k, v in obj.items() if k not in VOLATILE_KEYS}
    if isinstance(obj, list):
        return [_strip(x) for x in obj]
    return obj


def compare_file(old: Path, new: Path) -> list[str]:
    if not new.exists():
        return [f"missing after reproduction: {new.name}"]
    if old.suffix == ".csv":
        a = pd.read_csv(old, dtype=str, keep_default_na=False)
        b = pd.read_csv(new, dtype=str, keep_default_na=False)
        a = a[[c for c in a.columns if c not in VOLATILE_COLS]]
        b = b[[c for c in b.columns if c not in VOLATILE_COLS]]
        if list(a.columns) != list(b.columns):
            return [f"columns differ: {list(a.columns)} vs {list(b.columns)}"]
        if a.shape != b.shape:
            return [f"shape {a.shape} vs {b.shape}"]
        diff = (a.to_numpy() != b.to_numpy())
        if diff.any():
            r, c = diff.nonzero()
            ex = [f"row {i} {a.columns[j]}: {a.iat[i, j]} → {b.iat[i, j]}" for i, j in list(zip(r, c))[:5]]
            return [f"{int(diff.sum())} cells differ"] + ex
        return []
    if old.suffix == ".json":
        try:
            a, b = _strip(json.loads(old.read_text())), _strip(json.loads(new.read_text()))
        except json.JSONDecodeError:
            return ["invalid json"]
        return [] if a == b else ["json content differs (non-volatile keys)"]
    if old.suffix in (".md", ".jsonl", ".txt"):
        a, b = _mask(old.read_text()).splitlines(), _mask(new.read_text()).splitlines()
        bad = [f"line {i}: {x[:120]} → {y[:120]}" for i, (x, y) in enumerate(zip(a, b)) if x != y]
        if len(a) != len(b):
            bad.append(f"line count {len(a)} vs {len(b)}")
        return bad[:6]
    return [] if old.read_bytes() == new.read_bytes() else ["binary differs"]


def diff_report(started: str, commit: str, dirty, elapsed: float | None) -> bool:
    rows, ok = [], True
    for sub, live in (("dev2013", DEV), ("frozen", FROZEN)):
        snapdir = SNAP / sub
        if not snapdir.exists():
            continue
        for old in sorted(snapdir.glob("*")):
            if old.is_dir() or old.name in ("repro_diff.md", "freeze_checklist.md"):
                continue
            issues = compare_file(old, live / old.name)
            rows.append((f"{sub}/{old.name}", issues))
            ok &= not issues
    md = ["# repro_diff — إعادة إنتاج نتائج التطوير من ذاكرة مؤقتة فارغة (D-62 ش5)\n",
          f"**الحالة: {'مطابق' if ok else 'فروق'}** · بدأ {started} · commit `{commit}`"
          + (" (شجرة src غير مُودَعة: يُعاد على commit نظيف قبل الوسم)" if dirty else "")
          + (f" · المدة {elapsed / 60:.1f} دقيقة" if elapsed else "") + "\n",
          "المقارنة حرفية بعد حجب الحقول المتقلبة وحدها (الأزمنة، والتواريخ، وhash الـcommit، والذاكرة، والسرعة): "
          f"أعمدة CSV {sorted(VOLATILE_COLS)}، ومفاتيح JSON {sorted(VOLATILE_KEYS)}.\n",
          "| الملف | النتيجة |", "|---|---|"]
    for name, issues in rows:
        md.append(f"| `{name}` | {'مطابق' if not issues else '<br>'.join(issues).replace('|', '¦')} |")
    (DEV / "repro_diff.md").write_text("\n".join(md), encoding="utf-8")
    return ok


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--diff-only", action="store_true")
    ap.add_argument("--keep-cache", action="store_true", help="debug only: do not empty data/cache")
    a = ap.parse_args(argv)
    commit, dirty = git_state()
    started = time.strftime("%Y-%m-%d %H:%M:%S")
    if a.diff_only:
        ok = diff_report(started, commit, dirty, None)
        print(f"[repro] diff only: {'identical' if ok else 'DIFFERENCES'}")
        return
    if SNAP.exists():
        shutil.rmtree(SNAP)
    SNAP.mkdir(parents=True)
    for sub, live in (("dev2013", DEV), ("frozen", FROZEN)):
        if live.exists():
            shutil.copytree(live, SNAP / sub)
    if not a.keep_cache and data.CACHE_DIR.exists():
        shutil.rmtree(data.CACHE_DIR)
    t0 = time.time()
    log = []
    for step in STEPS:
        t = time.time()
        cmd = [sys.executable, "-m", f"src.ml.experiments.{step}"] + (["results/dev2013"] if step == "report" else [])
        r = subprocess.run(cmd, cwd=data.REPO_ROOT, capture_output=True, text=True)
        log.append({"step": step, "returncode": r.returncode, "seconds": round(time.time() - t, 1)})
        print(f"[repro] {step}: rc={r.returncode} ({time.time() - t:.0f}s)", flush=True)
        if r.returncode != 0:
            print(r.stdout[-2000:], r.stderr[-4000:])
            raise SystemExit(f"step {step} failed")
    subprocess.run([sys.executable, "-m", "src.ml.experiments.freeze_config", "--checklist"], cwd=data.REPO_ROOT)
    ok = diff_report(started, commit, dirty, time.time() - t0)
    (DEV / "repro_meta.json").write_text(json.dumps({"started": started, "commit": commit, "src_dirty": dirty,
                                                     "steps": log, "identical": ok,
                                                     "wall_seconds": round(time.time() - t0, 1)}, indent=2))
    print(f"[repro] finished in {(time.time() - t0) / 60:.1f} min: {'identical' if ok else 'DIFFERENCES'}")


if __name__ == "__main__":
    main()
