"""Confirmatory run E10 (D-63) — one run on the thirteen 2014 presentations after the tag ``freeze-03``.

    python3 -m src.ml.experiments.run_confirmatory --tag freeze-03            # the confirmatory run (once)
    python3 -m src.ml.experiments.run_confirmatory --tag freeze-03 --phase 2  # re-run phase 2 only (after LOCK)
    python3 -m src.ml.experiments.run_confirmatory --dry-run-dev [--force]    # full dry run on the 2013 presentations
                                                                              # (alias --dry-run-2013) → results/dryrun2013/
Guards (confirmatory mode): HEAD = the tag, clean working tree, ``results/conf2014/`` absent; then
``results/conf2014/.lock`` is written, the full 2014 read is logged in ``results/access_log.jsonl``, and only then is
``allow_confirmatory=True`` passed. The integrity of the frozen files is checked against the SHA-256 recorded in
``results/frozen/freeze03_config.json``. The dry run never touches 2014.

Phase 1 (E10): B1–B10 (tasks A and B), GRU-lite, the H2-a pair (WRMF W* and L0, ≤ 20 settings each), HYB* (D-51)
and the acceptance-only hybrid with weights re-tuned on each presentation's validation window inside the frozen
grid, task B with task-A weights (D-57), H4-a with the final risk models (D-58), H4-b (exploratory), the H1
decomposition (D-60). Then verdicts (bootstrap-t, exact sign-flip p, Holm m = 4, D-26 tables, D-48 text with the
frozen MDE80) are written and locked (SHA-256 in LOCK) BEFORE phase 2. No hypothesis result is printed.
Phase 2 (E11–E13): signal and component ablations, E sensitivities (E∖{page}, none), other sensitivities
(course-level bootstrap, each origin, nominal floor, H4-a full and deployable training, appendix intervals),
descriptive fairness (D-21; no model is trained on sensitive attributes), sampled-negative protocol, figures.
"""
from __future__ import annotations

import os

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")

import argparse  # noqa: E402
import hashlib  # noqa: E402
import json  # noqa: E402
import multiprocessing as mp  # noqa: E402
import platform  # noqa: E402
import shutil  # noqa: E402
import subprocess  # noqa: E402
import sys  # noqa: E402
import time  # noqa: E402
from pathlib import Path  # noqa: E402

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from .. import components as CP, data, hybrid, learners as L, metrics, plots, stats  # noqa: E402
from ..harness import SEEDS, run_job as baseline_job  # noqa: E402
from ..models import BASELINES  # noqa: E402
from ..splits import CUTS  # noqa: E402
from . import report  # noqa: E402
from . import run_ablation, run_gru, run_hybrid  # noqa: E402
from .learner_analysis import build_table, feature_sets, standardise  # noqa: E402

FROZEN = data.RESULTS_DIR / "frozen"
DEV = data.RESULTS_DIR / "dev2013"
HYPOTHESES = ("H1", "H2-a", "H3", "H4-a")
MODULE_START_DAY = {"B": 31, "J": 273}       # B presentations start in February, J in October (OULAD)


class GuardError(RuntimeError):
    pass


# =============================================================================================
# guards and integrity
# =============================================================================================
def _git(*args) -> str:
    return subprocess.check_output(["git", *args], cwd=data.REPO_ROOT, stderr=subprocess.DEVNULL).decode().strip()


def check_guards(tag: str, out: Path, git=_git) -> str:
    """D-63 §1: HEAD = tag, clean tree, output directory absent. Returns the tagged commit."""
    try:
        tagged = git("rev-parse", f"{tag}^{{commit}}")
    except Exception as exc:
        raise GuardError(f"tag {tag} does not exist") from exc
    head = git("rev-parse", "HEAD")
    if head != tagged:
        raise GuardError(f"HEAD {head[:10]} is not the tagged commit {tagged[:10]}")
    if git("status", "--porcelain"):
        raise GuardError("working tree is not clean")
    if out.exists():
        raise GuardError(f"{out} already exists: a second confirmatory run needs a written decision of the supervisor")
    return tagged


def guard_rehearsal(tag: str, out: Path, git=_git) -> dict:
    """Dry run (D-62 ش7): evaluate every D-63 §1 guard without stopping, so the 2014 path is rehearsed on 2013.

    Each guard is reported separately, then ``check_guards`` itself is exercised with the tag mapped to HEAD (the tag
    does not exist yet before freeze-03); it must pass on a clean tree with ``results/conf2014/`` absent.
    """
    head = git("rev-parse", "HEAD")
    try:
        tagged = git("rev-parse", f"{tag}^{{commit}}")
    except Exception:
        tagged = None
    dirty = git("status", "--porcelain")
    rep = {"head": head, "tag": tag, "tag_exists": tagged is not None, "head_is_tag": tagged == head,
           "tree_clean": not dirty, "dirty_paths": dirty.splitlines()[:20], "conf2014_absent": not out.exists()}

    def at_head(*args):
        if args[:1] == ("rev-parse",) and args[1].startswith(tag):
            return head
        return git(*args)
    try:
        check_guards(tag, out, git=at_head)
        rep["check_guards_with_tag_at_HEAD"] = "pass"
    except GuardError as exc:
        rep["check_guards_with_tag_at_HEAD"] = f"blocked: {exc}"
    return rep


def access_log_lines() -> list[str]:
    p = data.RESULTS_DIR / "access_log.jsonl"
    return p.read_text(encoding="utf-8").splitlines() if p.exists() else []


def audit_2014(before: list[str], ctx) -> dict:
    """Dry run: no full 2014 read was logged, only D-47 id reads (3 columns), and no 2014 row reached any frame."""
    new = [json.loads(l) for l in access_log_lines()[len(before):] if l.strip()]
    full = [r for r in new if r.get("event") == "confirmatory_full_read"]
    ids = [r for r in new if r.get("columns") == ["code_module", "code_presentation", "id_student"]]
    other = [r for r in new if r not in full and r not in ids]
    conf = set(data.CONF_PRESENTATIONS)
    seen = sorted(ctx.presentations())
    leaked = {k: sorted(v & conf) for k, v in ctx.loaded.items() if v & conf}
    rep = {"new_access_log_records": len(new), "confirmatory_full_read": len(full), "d47_id_reads_3_columns": len(ids),
           "other_records": len(other), "presentations_loaded": seen,
           "any_2014_presentation_loaded": bool(set(seen) & conf),
           "loader_presentations": {k: len(v) for k, v in ctx.loaded.items()}, "loaders_with_2014_rows": leaked}
    rep["ok"] = not full and not other and not rep["any_2014_presentation_loaded"] and not leaked
    return rep


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def check_integrity() -> dict:
    cfg = json.loads((FROZEN / "freeze03_config.json").read_text())
    files = {"mde80.json": DEV / "mde80.json", "hybrid_frozen.json": DEV / "hybrid_frozen.json",
             "risk_final.json": FROZEN / "risk_final.json"}
    bad = {k: (sha256(p), cfg["sha256"].get(k)) for k, p in files.items() if sha256(p) != cfg["sha256"].get(k)}
    if bad:
        raise GuardError(f"frozen files changed since freeze03_config.json: {bad}")
    raw = {f: hashlib.md5((data.RAW_DIR / f).read_bytes()).hexdigest() for f in cfg["raw_md5"]}
    bad_raw = {f: (m, cfg["raw_md5"][f]["md5"]) for f, m in raw.items() if m != cfg["raw_md5"][f]["md5"]}
    if bad_raw or len(raw) != 7:
        raise GuardError(f"raw OULAD files differ from the frozen MD5 (freeze03_config.json): {bad_raw or sorted(raw)}")
    cfg["raw_md5_checked"] = raw
    return cfg


def verify_lock(out: Path, tag: str, dry: bool, git=_git) -> dict:
    """Before phase 2 (also when run alone, peer m2): LOCK exists and matches the phase-1 verdict files, and its commit
    is HEAD; in confirmatory mode HEAD must also be the tagged commit."""
    p = out / "LOCK"
    if not p.exists():
        raise GuardError("phase 2 needs the phase-1 LOCK")
    lock = json.loads(p.read_text())
    for f in ("verdicts.csv", "verdicts.md"):
        if not (out / f).exists() or sha256(out / f) != lock.get(f"{f.replace('.', '_')}_sha256"):
            raise GuardError(f"{f} does not match LOCK")
    head = git("rev-parse", "HEAD")
    if lock.get("commit") != head:
        raise GuardError(f"LOCK commit {str(lock.get('commit'))[:10]} is not HEAD {head[:10]}")
    if not dry:
        try:
            tagged = git("rev-parse", f"{tag}^{{commit}}")
        except Exception as exc:
            raise GuardError(f"tag {tag} does not exist") from exc
        if head != tagged or lock.get("tag") != tag:
            raise GuardError(f"HEAD {head[:10]} / LOCK tag {lock.get('tag')} do not match tag {tag} ({tagged[:10]})")
    return lock


def log_full_read(tag: str, commit: str, md5: dict):
    rec = {"time": time.strftime("%Y-%m-%dT%H:%M:%S"), "event": "confirmatory_full_read", "tag": tag, "commit": commit,
           "files_md5": md5, "files_md5_match_frozen": True, "purpose": "E10 (D-63)"}
    with open(data.RESULTS_DIR / "access_log.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


# =============================================================================================
# helpers
# =============================================================================================
def pres_means(df: pd.DataFrame, model: str, task="A", slice_="all", metric="NDCG@10", **filt) -> pd.Series:
    r = df[(df["model"] == model) & (df["task"] == task) & (df["slice"] == slice_)]
    for k, v in filt.items():
        r = r[r[k] == v]
    return r.groupby(["presentation", "cut"])[metric].mean().groupby("presentation").mean().sort_index()


def by_cut(df: pd.DataFrame, model: str, metric="NDCG@10", **filt) -> pd.DataFrame:
    r = df[(df["model"] == model) & (df["task"] == "A") & (df["slice"] == "all")]
    for k, v in filt.items():
        r = r[r[k] == v]
    return r.groupby(["presentation", "cut"])[metric].mean()


def _md(df: pd.DataFrame) -> str:
    cols = list(df.columns)
    out = ["| " + " | ".join(map(str, cols)) + " |", "|" + "---|" * len(cols)]
    for _, r in df.iterrows():
        out.append("| " + " | ".join(f"{v:.4f}" if isinstance(v, float) else str(v) for v in r.values) + " |")
    return "\n".join(out)


class Context:
    def __init__(self, names, out: Path, allow: bool, workers: int, dry: bool, cache_tag: str):
        self.names, self.out, self.allow, self.workers, self.dry = list(names), out, allow, workers, dry
        self.cache_root = data.CACHE_DIR / f"components_{cache_tag}"
        self.figs = out / "figures"
        self.timing = {}
        self._pres = None
        self.loaded = {}              # loader → presentations present in what it returned (2014 audit of the dry run)
        self.frozen = json.loads((DEV / "hybrid_frozen.json").read_text())
        self.risk = json.loads((FROZEN / "risk_final.json").read_text())
        self.mde80 = {r["hypothesis"]: r for r in json.loads((DEV / "mde80.json").read_text())}

    def presentations(self):
        if self._pres is None:
            role = "dev" if self.dry else "conf"
            ev = data.load_daily_events(role, allow_confirmatory=self.allow)
            self.note("load_daily_events", ev)
            self._pres = {n: data.load_presentation(n, events=ev, allow_confirmatory=self.allow) for n in self.names}
        return self._pres

    def note(self, loader: str, df):
        if isinstance(df, pd.DataFrame) and "presentation" in df:
            self.loaded.setdefault(loader, set()).update(map(str, pd.unique(df["presentation"])))

    def folds(self):
        return [(n, c) for c in sorted(CUTS, reverse=True) for n in self.names]

    def pool(self):
        return mp.get_context("fork").Pool(self.workers)


def _set_globals(ctx: Context, exclusion: str):
    pres = ctx.presentations()
    for mod in (run_gru, run_ablation, run_hybrid):
        mod._PRES.clear()
        mod._PRES.update(pres)
    run_hybrid.EXCLUSION = exclusion
    CP.COMP_DIR = ctx.cache_root / exclusion


def _baseline_worker(args):
    name, cut, models, exclusion = args
    return baseline_job(_set_globals.pres[name], cut, models, exclusion=exclusion, seeds=SEEDS)


def run_baselines(ctx: Context, exclusion="E5", models=None):
    models = models or list(BASELINES)
    _set_globals(ctx, exclusion)
    _set_globals.pres = ctx.presentations()
    with ctx.pool() as pool:
        res = pool.map(_baseline_worker, [(n, c, models, exclusion) for n, c in ctx.folds()], chunksize=1)
    return (pd.DataFrame([r for x in res for r in x.rows]), pd.DataFrame([r for x in res for r in x.tuning]),
            pd.DataFrame([r for x in res for r in x.timing]), pd.DataFrame([r for x in res for r in x.folds]))


def run_gru_all(ctx: Context, exclusion="E5"):
    _set_globals(ctx, exclusion)
    with ctx.pool() as pool:
        res = pool.map(run_gru.run_job, [(n, c, SEEDS, exclusion, ()) for n, c in ctx.folds()], chunksize=1)
    return pd.DataFrame([r for rr, _ in res for r in rr]), pd.DataFrame([r for _, tt in res for r in tt])


def run_signal_pair(ctx: Context, exclusion="E5", models=("B7_WRMF",), variants=("L0", "Wstar")):
    _set_globals(ctx, exclusion)
    with ctx.pool() as pool:
        res = pool.map(run_ablation.run_job, [(n, c, SEEDS, models, variants, exclusion) for n, c in ctx.folds()],
                       chunksize=1)
    return pd.DataFrame([r for rr, _ in res for r in rr]), pd.DataFrame([r for _, tt in res for r in tt])


def run_frozen_hybrid(ctx: Context, base: pd.DataFrame, gru: pd.DataFrame, exclusion="E5"):
    """HYB* inside the frozen composition and grid (weights and component parameters re-tuned on validation)."""
    _set_globals(ctx, exclusion)
    sel = base[(base["task"] == "A") & (base["slice"] == "all") & (base["seed"] <= 0)]
    run_hybrid._CFG.clear()
    run_hybrid._CFG.update({(r.model, r.presentation, int(r.cut)): CP.parse_config(r.config) for r in sel.itertuples()})
    combo = ctx.frozen["components"]
    cands = sorted(set(combo) | {"B3_RecentPop", "C6_AssessProx", "C7_ClusterPop", "B5_SKNN"})
    with ctx.pool() as pool:
        pool.map(run_hybrid.build_fold, [(n, c, cands, SEEDS) for n, c in ctx.folds()], chunksize=1)
    with ctx.pool() as pool:
        ev = run_hybrid.Evaluator(pool, ctx.folds())
        an = run_hybrid.frozen_analyses(ev, pool, combo, ctx.frozen["floor_component"], base, gru,
                                        ctx.frozen["S_star_nonneural"], ctx.frozen["B_np_star"])
        an["ablation_components"] = {f"HYB* − {c}": run_hybrid.per_pres(ev.fold_results([x for x in combo if x != c]))
                                     for c in combo}
    return an


# =============================================================================================
# H4-a with the final risk models
# =============================================================================================
def _risk_fit_dry(df, X, y, keep, held, lam):
    tr = (df["presentation"].to_numpy() != held) & keep
    return L.logistic_fit(X[tr], y[tr], lam)


def h4a(ctx: Context, exclude_overlap=True, training="final"):
    """AUC per target presentation for M0/M1/M2/CART/majority at day 56, plus cuts 28/112 (M0–M2).

    Confirmatory: the frozen models of risk_final.json. Dry run on 2013: the same specification refitted
    leave-one-presentation-out with the frozen λ (2013 presentations cannot be scored by a model trained on them).
    ``training`` ∈ {final, full (no overlap removal), deployable (2013 presentations ended before day 56)}, plus
    ``frozen``: the frozen weights/tree of risk_final.json applied as-is (the confirmatory branch), run in the dry run
    so that no code path is executed for the first time on 2014 (peer m1); on 2013 it is in-sample.
    """
    pres_t = ctx.presentations()
    sa_t = data.load_student_assessment("dev" if ctx.dry else "conf", allow_confirmatory=ctx.allow)
    rows, oof_all = [], {}
    dev_pres = data.load_dev_presentations() if (ctx.dry or training != "final") and training != "frozen" else None
    sa_d = data.load_student_assessment("dev") if dev_pres else None
    ctx.note("load_student_assessment", sa_t)
    ctx.note("load_student_assessment", sa_d)
    overlap = data.confirmatory_student_ids() if (dev_pres and exclude_overlap) else set()
    for tc in (56, 28, 112):
        spec = ctx.risk["cuts"][str(tc)]["models"]
        dft = build_table(pres_t, tc, sa_t)
        y = dft["y"].to_numpy()
        fs = feature_sets(dft)
        scores = {}
        if (training == "final" and not ctx.dry) or training == "frozen":
            for m in ("M0", "M1", "M2"):
                X = standardise(dft, spec[m]["features"])
                scores[m] = L.logistic_predict(np.array(spec[m]["weights"]), X)
            Xc = standardise(dft, spec["CART_M2"]["features"])
            scores["CART_M2"] = L.cart_predict(spec["CART_M2"]["tree"], Xc)
        else:
            dfd = build_table(dev_pres, tc, sa_d)
            yd = dfd["y"].to_numpy()
            keep = ~dfd["id_student"].isin(overlap).to_numpy() if exclude_overlap else np.ones(len(dfd), bool)
            for m in ("M0", "M1", "M2", "CART_M2"):
                cols = spec[m]["features"]
                Xd, Xt = standardise(dfd, cols), standardise(dft, cols)
                s = np.full(len(dft), np.nan)
                for held in dft["presentation"].unique():
                    te = (dft["presentation"] == held).to_numpy()
                    tr_mask = keep & (dfd["presentation"].to_numpy() != held) if ctx.dry else keep.copy()
                    if training == "deployable":
                        tr_mask &= np.isin(dfd["presentation"].to_numpy(), deployable_training(held, list(dev_pres)))
                    if tr_mask.sum() == 0 or len(np.unique(yd[tr_mask])) < 2:
                        continue
                    if m == "CART_M2":
                        tree = L.cart_fit(Xd[tr_mask], yd[tr_mask], spec[m]["max_depth"], spec[m]["min_leaf"])
                        s[te] = L.cart_predict(tree, Xt[te])
                    else:
                        w = L.logistic_fit(Xd[tr_mask], yd[tr_mask], spec[m]["lambda"])
                        s[te] = L.logistic_predict(w, Xt[te])
                scores[m] = s
        scores["majority"] = np.full(len(dft), y.mean())
        thr = ctx.risk["youden_thresholds_day56_full_precision"]
        for name, idx in dft.groupby("presentation").indices.items():
            for m, s in scores.items():
                if tc != 56 and m in ("CART_M2", "majority"):
                    continue
                ss = s[idx]
                ok = np.isfinite(ss)
                r = {"presentation": name, "cut": tc, "model": m, "n": int(ok.sum()), "risk_rate": float(y[idx].mean()),
                     "ROC_AUC": L.roc_auc(y[idx][ok], ss[ok]) if ok.any() else np.nan,
                     "PR_AUC": L.average_precision(y[idx][ok], ss[ok]) if ok.any() else np.nan,
                     "Brier": L.brier(y[idx][ok], ss[ok]) if ok.any() and m != "CART_M2" else np.nan,
                     "unseen_course": name.startswith("CCC")}
                if tc == 56 and m in thr and ok.any():
                    r.update(L.threshold_metrics(y[idx][ok], ss[ok], thr[m]))
                rows.append(r)
        if tc == 56:
            oof_all = {"y": y, "scores": scores, "table": dft}
    return pd.DataFrame(rows), oof_all


def deployable_training(test_name: str, dev_names: list[str]) -> list[str]:
    """2013 presentations whose end precedes day 56 of the test presentation (D-27 sensitivity)."""
    def start(n):
        pres = n.split("_")[1]
        return (int(pres[:4]) - 2013) * 365 + MODULE_START_DAY[pres[4]]
    lengths = data.load_courses("all" if not test_name.endswith(("2013B", "2013J")) else "dev",
                                allow_confirmatory=not test_name.endswith(("2013B", "2013J")))
    length = dict(zip(lengths["presentation"], lengths["module_presentation_length"]))
    day56 = start(test_name) + 56
    return [n for n in dev_names if n != test_name and start(n) + length[n] < day56]


# =============================================================================================
# verdicts
# =============================================================================================
def build_verdicts(per_pres: dict[str, pd.Series], mde80: dict, gru_passed: bool) -> pd.DataFrame:
    rows = []
    for h in HYPOTHESES:
        d = per_pres[h].dropna()
        delta = 0.02
        if h == "H3" and not gru_passed:
            rows.append({"hypothesis": h, "status": "untestable (sanity gates not passed)", "p": 1.0})
            continue
        c = stats.compare(d.to_numpy())
        rows.append({"hypothesis": h, "n": c["n"], "mean_delta": c["mean"], "ci_lo": c["ci_lo"], "ci_hi": c["ci_hi"],
                     "degenerate": c["degenerate"], "n_degenerate": c["n_degenerate"], "p": c["p"],
                     "n_delta_pos": int((d > 0).sum()), "delta": delta,
                     "p_margin": stats.margin_test(d.to_numpy(), delta)})
    df = pd.DataFrame(rows)
    df["p_holm"] = stats.holm(df["p"].fillna(1.0).to_numpy())
    verdicts, texts, margin = [], [], []
    for _, r in df.iterrows():
        if "status" in r and isinstance(r.get("status"), str):
            verdicts.append(r["status"])
            texts.append("")
            margin.append(False)
            continue
        if r["hypothesis"] == "H3":
            v = stats.verdict_bidirectional(r["mean_delta"], r["ci_lo"], r["ci_hi"], r["p_holm"], r["delta"])
        else:
            v = stats.verdict(r["mean_delta"], r["ci_lo"], r["ci_hi"], r["p_holm"], r["delta"])
        verdicts.append(v)
        x = mde80.get(r["hypothesis"], {}).get("MDE80")
        texts.append(f"غير حاسمة: لا يكشف التصميم بقوة 80% أثراً أصغر من MDE80 = {x:.4f}" if v == "inconclusive" and x else "")
        margin.append(bool(v in ("confirmed", "superior_confirmed") and stats.confirmed_with_margin(r["ci_lo"], r["delta"])))
    df["verdict"] = verdicts
    df["D48_text"] = texts
    df["confirmed_with_margin"] = margin
    return df


VERDICT_AR = {"confirmed": "مؤكَّدة", "refuted_reverse": "مدحوضة عكسياً",
              "refuted": "مدحوضة عملياً (استُبعد أثر ≥ δ)", "inconclusive": "غير حاسمة",
              "superior_confirmed": "تفوّق مؤكَّد", "inferior_confirmed": "تأخّر مؤكَّد", "equivalent": "تكافؤ عملي",
              "inferior": "تأخّر (مدحوضة عكسياً)"}


def verdicts_md(df: pd.DataFrame, label: str) -> str:
    md = [f"# الأحكام — {label} (مولَّد بـ`run_confirmatory`)\n",
          "عائلة Holm = {H1، H2-أ، H3، H4-أ}، m = 4؛ p ثنائية بقلب إشارات دقيق؛ الفاصل bootstrap-t عنقودي على العروض "
          "(B = 10,000، البذرة 0)؛ الجداول D-26 (أحادي لـH1 وH2-أ وH4-أ، وسداسي لـH3)؛ δ = 0.02 (δ_AUC = 0.02 لـH4-أ)؛ "
          "نص D-48 بقيمة MDE80 المجمَّدة.\n",
          "| الفرضية | Δ̄ | فاصل bootstrap-t | p | p بعد Holm | الحكم | عروض Δ>0 | p الهامش | مؤكَّدة بهامش |",
          "|---|---|---|---|---|---|---|---|---|"]
    for _, r in df.iterrows():
        if not np.isfinite(r.get("mean_delta", np.nan)):
            md.append(f"| {r['hypothesis']} | — | — | 1 | {r['p_holm']:.4f} | {r['verdict']} | — | — | — |")
            continue
        ci = stats.format_ci({"ci_lo": r["ci_lo"], "ci_hi": r["ci_hi"], "degenerate": bool(r["degenerate"]),
                              "n_degenerate": int(r["n_degenerate"])})
        md.append(f"| {r['hypothesis']} | {r['mean_delta']:+.4f} | {ci} | {r['p']:.4f} | {r['p_holm']:.4f} | "
                  f"**{VERDICT_AR.get(r['verdict'], r['verdict'])}** | {int(r['n_delta_pos'])}/{int(r['n'])} | "
                  f"{r['p_margin']:.4f} | {'نعم' if r['confirmed_with_margin'] else '—'} |")
    md.append("")
    for _, r in df.iterrows():
        if r.get("D48_text"):
            md.append(f"- **{r['hypothesis']}:** {r['D48_text']}.")
    md.append("\n- **H2-ب:** غير منطبقة بالبناء (D-59): لا مكوّن في HYB* يقرأ W، فلا أرقام لها.")
    return "\n".join(md)


# =============================================================================================
# phases
# =============================================================================================
def phase1(ctx: Context, label: str):
    t0 = time.time()
    out = ctx.out
    out.mkdir(parents=True, exist_ok=True)
    print("[E10] phase 1: baselines B1–B10", flush=True)
    rows, tuning, timing, folds = run_baselines(ctx)
    rows.sort_values(["task", "model", "presentation", "cut", "seed", "slice"]).to_csv(out / "baselines.csv", index=False, float_format="%.6f")
    tuning.to_csv(out / "tuning.csv", index=False, float_format="%.6f")
    timing.to_csv(out / "timing.csv", index=False, float_format="%.3f")
    folds.to_csv(out / "folds.csv", index=False, float_format="%.6f")
    print("[E10] phase 1: GRU-lite", flush=True)
    gru, gru_t = run_gru_all(ctx)
    gru.to_csv(out / "gru.csv", index=False, float_format="%.6f")
    gru_t.to_csv(out / "gru_tuning.csv", index=False, float_format="%.6f")
    print("[E10] phase 1: H2-a pair", flush=True)
    pair, pair_t = run_signal_pair(ctx)
    pair.to_csv(out / "h2a_pair.csv", index=False, float_format="%.6f")
    print("[E10] phase 1: hybrid", flush=True)
    an = run_frozen_hybrid(ctx, rows, gru)
    run_hybrid.hybrid_rows(an).to_csv(out / "hybrid.csv", index=False, float_format="%.6f")
    weights = {f"{r['presentation']}_{r['cut']}": dict(zip(r["combo"], r["weights"])) for r in an["final"]}
    (out / ("hybrid_2014.json" if not ctx.dry else "hybrid_dryrun2013.json")).write_text(json.dumps(
        {"components": ctx.frozen["components"], "floor_rule": ctx.frozen["floor_rule"], "weights_by_fold": weights}, indent=1))
    print("[E10] phase 1: H4-a", flush=True)
    h4, oof = h4a(ctx)
    h4.to_csv(out / "h4a_auc.csv", index=False, float_format="%.6f")
    if ctx.dry:                                   # rehearse the confirmatory branch (frozen weights, CART tree)
        h4f, _ = h4a(ctx, training="frozen")
        h4f.assign(note="frozen risk_final.json weights; in-sample on 2013 (path rehearsal, not evidence)").to_csv(
            out / "h4a_frozen_branch.csv", index=False, float_format="%.6f")
        ctx.timing["h4a_frozen_branch_rows"] = int(len(h4f))
    # ---- per-presentation differences of the four hypotheses
    hyb = run_hybrid.per_pres(an["final"])
    b3 = pres_means(rows, "B3_RecentPop")
    a56 = h4[(h4["cut"] == 56)].pivot(index="presentation", columns="model", values="ROC_AUC")
    per = {"H1": hyb - b3,
           "H2-a": pres_means(pair, "B7_WRMF", variant="Wstar") - pres_means(pair, "B7_WRMF", variant="L0"),
           "H3": pres_means(gru, "GRU_lite") - pres_means(rows, "B5_SKNN"),
           "H4-a": a56["M1"] - a56["M0"]}
    sanity = json.loads((DEV / "gru_sanity.json").read_text())
    ver = build_verdicts(per, ctx.mde80, sanity.get("gates_passed", False))
    ver.to_csv(out / "verdicts.csv", index=False, float_format="%.6f")
    (out / "verdicts.md").write_text(verdicts_md(ver, label), encoding="utf-8")
    pp = pd.DataFrame({h: s for h, s in per.items()})
    pp.index.name = "presentation"
    pp.to_csv(out / "per_presentation.csv", float_format="%.6f")
    # each origin, descriptive
    cuts = []
    hy_cut = pd.DataFrame(an["final"]).groupby(["presentation", "cut"])["test_all"].mean()
    for (h, a, b) in (("H1", hy_cut, by_cut(rows, "B3_RecentPop")),
                      ("H2-a", by_cut(pair, "B7_WRMF", variant="Wstar"), by_cut(pair, "B7_WRMF", variant="L0")),
                      ("H3", by_cut(gru, "GRU_lite"), by_cut(rows, "B5_SKNN"))):
        d = (a - b).dropna()
        for c, g in d.groupby(level="cut"):
            cuts.append({"hypothesis": h, "cut": c, "mean_delta": float(g.mean()), "n": len(g)})
    pd.DataFrame(cuts).to_csv(out / "per_origin.csv", index=False, float_format="%.6f")
    # ---- LOCK before phase 2
    lock = {"tag": ctx.tag, "commit": ctx.commit, "verdicts_csv_sha256": sha256(out / "verdicts.csv"),
            "verdicts_md_sha256": sha256(out / "verdicts.md"), "time": time.strftime("%Y-%m-%dT%H:%M:%S")}
    (out / "LOCK").write_text(json.dumps(lock, indent=1))
    # ---- secondary, exploratory, decomposition, summaries
    sec = []
    for a_, b_ in (("M2", "M1"), ("M2", "M0"), ("CART_M2", "M0")):
        if a_ in a56 and b_ in a56:
            sec.append({"comparison": f"H4-a secondary {a_} − {b_} (AUC, day 56)", **stats.compare((a56[a_] - a56[b_]).dropna().to_numpy())})
    for tc in (28, 112):
        at = h4[h4["cut"] == tc].pivot(index="presentation", columns="model", values="ROC_AUC")
        sec.append({"comparison": f"H4-a secondary M1 − M0 (AUC, day {tc})", **stats.compare((at["M1"] - at["M0"]).dropna().to_numpy())})
    ccc = h4[(h4["cut"] == 56) & h4["unseen_course"]]
    if len(ccc):
        for m, g in ccc.groupby("model"):
            sec.append({"comparison": f"H4-a CCC unseen-course slice, {m} mean AUC", "mean": float(g["ROC_AUC"].mean()), "n": len(g)})
    sec.append({"comparison": "H2-b", "status": "not applicable by construction (D-59)"})
    pd.DataFrame(sec).to_csv(out / "secondary.csv", index=False, float_format="%.6f")
    pd.DataFrame([{"slice": k, **v, "status": "exploratory"} for k, v in an["h4b"].items()]).to_csv(out / "h4b.csv", index=False, float_format="%.6f")
    pd.DataFrame(an["decomposition"]).to_csv(out / "h1_decomposition.csv", index=False, float_format="%.6f")
    mde80_frozen(ctx, per)
    summary(ctx, rows, gru, an, h4, label)
    figures_phase1(ctx, ver, per, rows, gru, an, oof)
    ctx.timing["phase1_seconds"] = round(time.time() - t0, 1)
    return an


def mde80_frozen(ctx: Context, per: dict):
    src = (DEV / "mde80.md").read_text()
    md = ["# جدول MDE80 المجمَّد (نسخة حرفية، D-61)\n", f"SHA-256 لـ`mde80.json` عند الوسم: `{sha256(DEV / 'mde80.json')}`\n",
          "---\n", src, "\n---\n", "## σ على العروض المستهدفة — **لاحق، وصفي، لا يُستعمل في نص D-48**\n"]
    for h, d in per.items():
        d = d.dropna()
        md.append(f"- {h}: σ = {float(np.std(d, ddof=1)):.4f} (n = {len(d)})")
    (ctx.out / "mde80_frozen.md").write_text("\n".join(md), encoding="utf-8")


def summary(ctx: Context, rows, gru, an, h4, label):
    dev = pd.read_csv(DEV / "baselines.csv")
    devg = pd.read_csv(DEV / "gru.csv")
    allt = pd.concat([rows, gru[gru["model"] == "GRU_lite"]], ignore_index=True)
    alld = pd.concat([dev, devg[devg["model"] == "GRU_lite"]], ignore_index=True)
    tab = []
    for task in ("A", "B"):
        for m in sorted(allt[allt["task"] == task]["model"].unique()):
            t = pres_means(allt, m, task=task)
            d = pres_means(alld, m, task=task)
            tab.append({"task": task, "model": m, "NDCG@10": float(t.mean()), "± (presentations)": float(t.std(ddof=1)),
                        "dev 2013": float(d.mean()) if len(d) else np.nan})
    hb = run_hybrid.hybrid_rows(an)
    for task in ("A", "B"):
        for m in hb[hb["task"] == task]["model"].unique():
            v = hb[(hb["task"] == task) & (hb["model"] == m)].groupby("presentation")["NDCG@10"].mean()
            tab.append({"task": task, "model": m, "NDCG@10": float(v.mean()), "± (presentations)": float(v.std(ddof=1)),
                        "dev 2013": np.nan})
    t = pd.DataFrame(tab)
    a56 = h4[h4["cut"] == 56].groupby("model")[["ROC_AUC", "PR_AUC", "Brier"]].mean()
    md = [f"# ملخص التشغيل — {label}\n", "القيمة = متوسط العروض (بعد متوسط البذور والأصول) ± الانحراف عبر العروض؛ "
          "عمود «dev 2013» للمقارنة من `results/dev2013/`.\n", _md(t) + "\n", "## H4-أ (اليوم 56)\n",
          _md(a56.reset_index()) + "\n", "الأحكام في `verdicts.md`؛ الثانوي والاستكشافي في `secondary.csv` و`h4b.csv` "
          "و`h1_decomposition.csv`.\n"]
    (ctx.out / "summary.md").write_text("\n".join(md), encoding="utf-8")


def figures_phase1(ctx, ver, per, rows, gru, an, oof):
    f = ctx.figs
    fr = []
    for _, r in ver.iterrows():
        if not np.isfinite(r.get("mean_delta", np.nan)):
            continue
        fr.append({"label": r["hypothesis"], "mean": r["mean_delta"], "lo": r["ci_lo"], "hi": r["ci_hi"],
                   "note": VERDICT_AR.get(r["verdict"], r["verdict"])})
    plots.forest(f / "fig1_forest.svg", fr, "الفرضيات الأربع: Δ̄ وفاصل bootstrap-t", ref_lines=(0.0, 0.02))
    plots.strip(f / "fig2_per_presentation.svg", {h: s.dropna().to_dict() for h, s in per.items()}, "Δ_p لكل عرض")
    dev = pd.read_csv(DEV / "baselines.csv")
    dr = []
    for m in sorted(rows[rows["task"] == "A"]["model"].unique()):
        dr.append({"label": m, "a": float(pres_means(dev, m).mean()), "b": float(pres_means(rows, m).mean())})
    dr.append({"label": "GRU_lite", "a": float(pres_means(pd.read_csv(DEV / "gru.csv"), "GRU_lite").mean()),
               "b": float(pres_means(gru, "GRU_lite").mean())})
    dr.append({"label": "HYB*", "a": float(json.loads((DEV / "hybrid_meta.json").read_text())["hyb_ndcg"]),
               "b": float(run_hybrid.per_pres(an["final"]).mean())})
    plots.dumbbell(f / "fig4_models_dev_vs_target.svg", dr, "NDCG@10 (المهمة A): التطوير مقابل الهدف",
                   a_label="2013 dev", b_label="target")
    curves = {}
    for m in ("M0", "M1", "M2"):
        s = oof["scores"][m]
        ok = np.isfinite(s)
        fp, tp = plots.roc_points(oof["y"][ok], s[ok])
        curves[m] = (fp, tp, L.roc_auc(oof["y"][ok], s[ok]))
    plots.roc(f / "fig5_roc.svg", curves, "ROC (اليوم 56)")
    plots.bars(f / "fig6_h4b.svg", [{"group": k, "series": "Δ NDCG@10", "mean": v["mean"], "lo": v["ci_lo"], "hi": v["ci_hi"]}
                                    for k, v in an["h4b"].items()], "H4-ب: الربع الأدنى مقابل الأعلى", ylabel="Δ")


# =============================================================================================
# phase 2
# =============================================================================================
def fairness(ctx: Context, an, oof, n_boot=2000) -> pd.DataFrame:
    role = "dev" if ctx.dry else "conf"
    info = data.load_student_info(include_sensitive=True, role=role, allow_confirmatory=ctx.allow)
    ctx.note("load_student_info", info)
    info = info.set_index(["presentation", "id_student"])
    rng = np.random.default_rng(0)
    rows = []
    # recommendation: per-learner NDCG@10/HR@10 (task A, test windows) for HYB* and B3
    recs = []
    for r in an["final"]:
        name, cut = r["presentation"], r["cut"]
        F = dict(np.load(run_hybrid.fold_dir(name, cut) / "fold_test.npz"))
        ev = F["ev"].astype(bool)
        users = F["users"][ev]
        per_model = {}
        for label, combo, w in (("HYB*", r["combo"], r["weights"]), ("B3_RecentPop", ["B3_RecentPop"], [1.0])):
            vals = []
            for s in (SEEDS if label == "HYB*" else SEEDS[:1]):
                rt = [run_hybrid._rt(name, cut, c, "test", s, F) for c in combo]
                sc = hybrid.fuse(rt, np.asarray(w, dtype=float))
                res = metrics.evaluate(sc, F["cand"][ev], F["tgt"][ev], F["unreach"][ev], np.ones(ev.sum(), bool),
                                       F["tiebreak"][ev], ks=(10,))
                vals.append(np.c_[res["per_user"]["NDCG@10"], res["per_user"]["HR@10"]])
            per_model[label] = np.mean(vals, axis=0)
        for label, v in per_model.items():
            recs.append(pd.DataFrame({"presentation": name, "cut": cut, "model": label, "id_student": users,
                                      "NDCG@10": v[:, 0], "HR@10": v[:, 1]}))
    rec = pd.concat(recs, ignore_index=True)
    rec = rec.join(info[["gender", "disability", "imd_band", "age_band"]], on=["presentation", "id_student"])
    for attr in ("gender", "disability", "imd_band", "age_band"):
        for model, g in rec.groupby("model"):
            for metric in ("NDCG@10", "HR@10"):
                groups = g[attr].fillna("NA").to_numpy()
                vals = g[metric].to_numpy()
                pres = g["presentation"].to_numpy()
                idx_by_p = [np.flatnonzero(pres == p) for p in np.unique(pres)]
                boots = {k: [] for k in np.unique(groups)}
                for _ in range(n_boot):
                    take = np.concatenate([rng.choice(ix, len(ix)) for ix in idx_by_p])
                    gg, vv = groups[take], vals[take]
                    for k in boots:
                        m = gg == k
                        boots[k].append(vv[m].mean() if m.any() else np.nan)
                for k in boots:
                    m = groups == k
                    lo, hi = np.nanquantile(boots[k], [0.025, 0.975])
                    rows.append({"part": "recommendation", "model": model, "attribute": attr, "group": k,
                                 "metric": metric, "n": int(m.sum()), "small_group": bool(m.sum() < 50),
                                 "value": float(vals[m].mean()), "ci_lo": float(lo), "ci_hi": float(hi)})
    # classifier: FNR/FPR of M1 (main) and M2 (appendix) at the frozen Youden thresholds
    t = oof["table"][["presentation", "id_student"]].join(info[["gender", "disability", "imd_band", "age_band"]],
                                                          on=["presentation", "id_student"])
    y = oof["y"]
    thr = ctx.risk["youden_thresholds_day56_full_precision"]
    for m in ("M1", "M2"):
        s = oof["scores"][m]
        for attr in ("gender", "disability", "imd_band", "age_band"):
            groups = t[attr].fillna("NA").to_numpy()
            for k in np.unique(groups):
                ix = np.flatnonzero((groups == k) & np.isfinite(s))
                if not len(ix):
                    continue
                tm = L.threshold_metrics(y[ix], s[ix], thr[m])
                bs = []
                for _ in range(n_boot):
                    b = rng.choice(ix, len(ix))
                    bm = L.threshold_metrics(y[b], s[b], thr[m])
                    bs.append((bm["FNR"], bm["FPR"]))
                bs = np.array(bs)
                rows.append({"part": "classifier", "model": m + (" (appendix)" if m == "M2" else ""), "attribute": attr,
                             "group": k, "metric": "FNR/FPR", "n": len(ix), "small_group": len(ix) < 50,
                             "FNR": tm["FNR"], "FPR": tm["FPR"],
                             "FNR_ci_lo": float(np.quantile(bs[:, 0], 0.025)), "FNR_ci_hi": float(np.quantile(bs[:, 0], 0.975)),
                             "FPR_ci_lo": float(np.quantile(bs[:, 1], 0.025)), "FPR_ci_hi": float(np.quantile(bs[:, 1], 0.975))})
    return pd.DataFrame(rows)


def protocol_sampled(ctx: Context, an, n_neg=20) -> pd.DataFrame:
    """E13: rank each test target among 20 sampled negatives (setting of [20]); HR@10 (illustrative appendix)."""
    rows = []
    for r in an["final"]:
        name, cut = r["presentation"], r["cut"]
        F = dict(np.load(run_hybrid.fold_dir(name, cut) / "fold_test.npz"))
        ev = np.flatnonzero(F["ev"].astype(bool))
        import zlib
        rng = np.random.default_rng([int(cut), zlib.crc32(name.encode())])
        models = {"B3_RecentPop": CP.load_scores(name, cut, "B3_RecentPop", "test", 0),
                  "B5_SKNN": CP.load_scores(name, cut, "B5_SKNN", "test", 0)}
        if CP.has_scores(name, cut, "GRU_lite", "test", 0):
            models["GRU_lite"] = CP.load_scores(name, cut, "GRU_lite", "test", 0)
        rt = [run_hybrid._rt(name, cut, c, "test", 0, F) for c in r["combo"]]
        hyb_full = np.full(F["cand"].shape, -np.inf)
        hyb_full[F["ev"].astype(bool)] = hybrid.fuse(rt, np.asarray(r["weights"], dtype=float))
        models["HYB*"] = hyb_full
        for label, S in models.items():
            hits = []
            for u in ev:
                tg = np.flatnonzero(F["tgt"][u])
                pool_ = np.flatnonzero(F["cand"][u] & ~F["tgt"][u])
                if not len(tg) or len(pool_) < n_neg:
                    continue
                h = []
                for j in tg:
                    neg = rng.choice(pool_, n_neg, replace=False)
                    better = (S[u, neg] > S[u, j]) | ((S[u, neg] == S[u, j]) & (F["tiebreak"][u, neg] < F["tiebreak"][u, j]))
                    h.append(better.sum() < 10)
                hits.append(np.mean(h))
            rows.append({"presentation": name, "cut": cut, "model": label, "HR@10_sampled20": float(np.mean(hits)) if hits else np.nan,
                         "n_learners": len(hits)})
    return pd.DataFrame(rows)


def phase2(ctx: Context, an=None, label=""):
    t0 = time.time()
    out = ctx.out
    ctx.lock_verified = verify_lock(out, ctx.tag, ctx.dry)
    rows = pd.read_csv(out / "baselines.csv")
    gru = pd.read_csv(out / "gru.csv")
    if an is None:
        an = run_frozen_hybrid(ctx, rows, gru)
    print("[E10] phase 2: signal ablation", flush=True)
    abl, abl_t = run_signal_pair(ctx, models=("B7_WRMF", "B4_ItemKNN"), variants=run_ablation.VARIANTS)
    abl.to_csv(out / "ablation_signals.csv", index=False, float_format="%.6f")
    comp = []
    hyb = run_hybrid.per_pres(an["final"])
    for k, v in an["ablation_components"].items():
        c = stats.compare((hyb - v).dropna().to_numpy())
        comp.append({"ablation": k, "NDCG@10_without": float(v.mean()), "delta_full_minus_without": c["mean"],
                     "ci_lo": c["ci_lo"], "ci_hi": c["ci_hi"], "p": c["p"]})
    pd.DataFrame(comp).to_csv(out / "ablation_components.csv", index=False, float_format="%.6f")
    for exc in ("E4", "none"):
        print(f"[E10] phase 2: sensitivity {exc}", flush=True)
        r_, _, _, _ = run_baselines(ctx, exclusion=exc)
        g_, _ = run_gru_all(ctx, exclusion=exc)
        p_, _ = run_signal_pair(ctx, exclusion=exc)
        a_ = run_frozen_hybrid(ctx, r_, g_, exclusion=exc)
        h_ = run_hybrid.hybrid_rows(a_).assign(source="hybrid")
        pd.concat([r_.assign(source="baselines"), g_.assign(source="gru"), p_.assign(source="h2a_pair"), h_],
                  ignore_index=True).assign(exclusion=exc).to_csv(out / f"sensitivity_{exc}.csv", index=False, float_format="%.6f")
    _set_globals(ctx, "E5")
    print("[E10] phase 2: other sensitivities", flush=True)
    per = pd.read_csv(out / "per_presentation.csv", index_col="presentation")
    other = []
    module = per.index.str.split("_").str[0]
    for h in per.columns:
        dm = per[h].groupby(module).mean().dropna()
        other.append({"analysis": "course-level bootstrap (robustness, D-31)", "hypothesis": h, "n_units": len(dm),
                      **stats.compare(dm.to_numpy())})
    if an["nominal"] is not None:
        d = (run_hybrid.per_pres(an["nominal"]) - pres_means(rows, "B3_RecentPop")).dropna()
        other.append({"analysis": "nominal floor (D-51), H1 pair", "hypothesis": "H1", "n_units": len(d), **stats.compare(d.to_numpy())})
    for training in ("full", "deployable"):
        h4s, _ = h4a(ctx, exclude_overlap=(training != "full"), training=training)
        a56 = h4s[h4s["cut"] == 56].pivot(index="presentation", columns="model", values="ROC_AUC")
        d = (a56["M1"] - a56["M0"]).dropna()
        other.append({"analysis": f"H4-a {training} training", "hypothesis": "H4-a", "n_units": len(d),
                      **(stats.compare(d.to_numpy()) if len(d) >= 2 else {"mean": float(d.mean()) if len(d) else np.nan})})
    po = pd.read_csv(out / "per_origin.csv")
    for _, r in po.iterrows():
        other.append({"analysis": f"origin t = {int(r['cut'])} alone (descriptive)", "hypothesis": r["hypothesis"],
                      "n_units": int(r["n"]), "mean": r["mean_delta"]})
    pd.DataFrame(other).to_csv(out / "sensitivity_other.csv", index=False, float_format="%.6f")
    app = []
    for h in per.columns:
        d = per[h].dropna().to_numpy()
        _, plo, phi = stats.cluster_bootstrap_ci(d)
        tlo, thi = stats.t_interval(d)
        app.append({"hypothesis": h, "percentile_lo": plo, "percentile_hi": phi, "t_lo": tlo, "t_hi": thi})
    pd.DataFrame(app).to_csv(out / "intervals_appendix.csv", index=False, float_format="%.6f")
    print("[E10] phase 2: fairness and protocol", flush=True)
    _, oof = h4a(ctx)
    fair = fairness(ctx, an, oof)
    fair.to_csv(out / "fairness.csv", index=False, float_format="%.6f")
    protocol_sampled(ctx, an).to_csv(out / "protocol_sampled.csv", index=False, float_format="%.6f")
    # figures
    devab = pd.read_csv(DEV / "ablation_signals.csv")
    series = {}
    for src, df in (("dev 2013", devab), ("target", abl)):
        series[f"WRMF {src}"] = {v: float(pres_means(df, "B7_WRMF", variant=v).mean()) for v in run_ablation.VARIANTS}
    plots.lines(ctx.figs / "fig3_signal_ablation.svg", series, "استئصال الإشارة (WRMF)")
    fr = fair[(fair["part"] == "recommendation") & (fair["metric"] == "NDCG@10") & (fair["model"] == "HYB*")]
    plots.bars(ctx.figs / "fig7_fairness.svg", [{"group": f"{r.attribute}:{r.group}", "series": "HYB* NDCG@10", "mean": r.value,
                                                 "lo": r.ci_lo, "hi": r.ci_hi} for r in fr.itertuples()],
               "الإنصاف الوصفي: NDCG@10 لـHYB* بحسب المجموعات", ylabel="NDCG@10")
    ctx.timing["phase2_seconds"] = round(time.time() - t0, 1)


def render_pngs(ctx: Context):
    svgs = sorted(ctx.figs.glob("*.svg"))
    if svgs:
        subprocess.run([sys.executable, str(data.REPO_ROOT / "scripts" / "svg2png.py"), *map(str, svgs),
                        "--out-dir", str(ctx.figs)], cwd=data.REPO_ROOT, capture_output=True)


def compare_with_dev(ctx: Context) -> str:
    """Dry run only: intersecting numbers must match the development results."""
    out = ctx.out
    checks = []
    for fname, keycols in (("baselines.csv", ["task", "model", "presentation", "cut", "seed", "slice"]),
                           ("gru.csv", ["task", "model", "presentation", "cut", "seed", "slice"])):
        a = pd.read_csv(DEV / fname)
        b = pd.read_csv(out / fname)
        m = a.merge(b, on=keycols, suffixes=("_dev", "_dry"))
        for col in ("NDCG@10", "HR@10"):
            diff = (m[f"{col}_dev"] - m[f"{col}_dry"]).abs().max()
            checks.append({"file": fname, "metric": col, "rows_compared": len(m), "max_abs_diff": float(diff)})
    hb = pd.read_csv(DEV / "hybrid.csv")
    hd = pd.read_csv(out / "hybrid.csv")
    for model in ("HYB*", "HYB_accept_only", "HYB_nominal_floor"):
        for task in ("A", "B"):
            a = hb[(hb["model"] == model) & (hb["task"] == task)].set_index(["presentation", "cut"])["NDCG@10"]
            b = hd[(hd["model"] == model) & (hd["task"] == task)].set_index(["presentation", "cut"])["NDCG@10"]
            j = a.to_frame("dev").join(b.to_frame("dry"), how="inner")
            if len(j):
                checks.append({"file": f"hybrid.csv {model} {task}", "metric": "NDCG@10", "rows_compared": len(j),
                               "max_abs_diff": float((j["dev"] - j["dry"]).abs().max())})
    ab = pd.read_csv(DEV / "ablation_signals.csv")
    abd = pd.read_csv(out / "ablation_signals.csv") if (out / "ablation_signals.csv").exists() else None
    if abd is not None:
        k = ["model", "variant", "presentation", "cut", "seed", "slice"]
        m = ab.merge(abd, on=k, suffixes=("_dev", "_dry"))
        checks.append({"file": "ablation_signals.csv", "metric": "NDCG@10", "rows_compared": len(m),
                       "max_abs_diff": float((m["NDCG@10_dev"] - m["NDCG@10_dry"]).abs().max())})
    la = pd.read_csv(DEV / "learner_auc.csv")
    la = la[(la["cut"] == 56) & la["overlap_excluded"]].set_index(["presentation", "model"])["ROC_AUC"]
    da = pd.read_csv(out / "h4a_auc.csv")
    da = da[da["cut"] == 56].set_index(["presentation", "model"])["ROC_AUC"]
    j = la.to_frame("dev").join(da.to_frame("dry"), how="inner")
    checks.append({"file": "h4a_auc.csv vs learner_auc.csv (day 56)", "metric": "ROC_AUC", "rows_compared": len(j),
                   "max_abs_diff": float((j["dev"] - j["dry"]).abs().max()),
                   "note": "dev: λ chosen by nested inner LOPO per held-out presentation; dry run: frozen λ (D-58)"})
    df = pd.DataFrame(checks)
    df.to_csv(out / "dryrun_vs_dev.csv", index=False, float_format="%.8f")
    return _md(df)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="freeze-03")
    ap.add_argument("--phase", choices=["all", "1", "2"], default="all")
    ap.add_argument("--dry-run-dev", "--dry-run-2013", dest="dry", action="store_true")
    ap.add_argument("--force", action="store_true", help="dry run only: overwrite results/dryrun2013/")
    ap.add_argument("--workers", type=int, default=4)
    a = ap.parse_args(argv)
    t0 = time.time()
    cfg = check_integrity()
    if a.dry:
        out = data.RESULTS_DIR / "dryrun2013"
        if out.exists() and a.phase in ("all", "1"):
            if not a.force:
                raise GuardError(f"{out} exists (use --force for the dry run)")
            shutil.rmtree(out)
        names, allow, label, commit = data.DEV_PRESENTATIONS, False, "تشغيل جاف على عروض 2013 (D-62 ش7)", _git("rev-parse", "HEAD")
        data.assert_allowed(names)
        rehearsal = guard_rehearsal(a.tag, data.RESULTS_DIR / "conf2014")
    else:
        out = data.RESULTS_DIR / "conf2014"
        if a.phase in ("all", "1"):
            commit = check_guards(a.tag, out)
            out.mkdir(parents=True)
            (out / ".lock").write_text(json.dumps({"tag": a.tag, "commit": commit, "started": time.strftime("%Y-%m-%dT%H:%M:%S")}))
            log_full_read(a.tag, commit, cfg["raw_md5_checked"])
        else:
            commit = _git("rev-parse", "HEAD")
            verify_lock(out, a.tag, dry=False)            # LOCK matches, HEAD = LOCK commit = tag (peer m2)
        names, allow, label = data.CONF_PRESENTATIONS, True, "التشغيل التأكيدي على عروض 2014 (E10)"
    ctx = Context(names, out, allow, a.workers, a.dry, "dryrun2013" if a.dry else "conf2014")
    ctx.tag, ctx.commit = a.tag, commit
    log_before = access_log_lines()
    out.mkdir(parents=True, exist_ok=True)
    (out / "deviations.md").exists() or (out / "deviations.md").write_text("# سجل الانحرافات (D-63 §5)\n\nلا شيء.\n")
    an = phase1(ctx, label) if a.phase in ("all", "1") else None
    status = "phase1"
    if a.phase in ("all", "2"):
        phase2(ctx, an, label)
        status = "completed"
    render_pngs(ctx)
    extra = compare_with_dev(ctx) if a.dry else ""
    meta = {"mode": "dry-run on 2013" if a.dry else "confirmatory", "tag": a.tag, "commit": commit, "status": status,
            "presentations": list(names), "frozen_config_sha256": sha256(FROZEN / "freeze03_config.json"),
            "raw_md5": {k: v["md5"] for k, v in cfg["raw_md5"].items()}, "python": platform.python_version(),
            "numpy": np.__version__, "pandas": pd.__version__, **ctx.timing,
            "wall_seconds": round(time.time() - t0, 1), "workers": a.workers, "date": time.strftime("%Y-%m-%d %H:%M:%S")}
    if a.dry:
        meta["guard_rehearsal"] = rehearsal
        meta["audit_2014"] = audit_2014(log_before, ctx)
        meta["path_checks"] = {"LOCK": (out / "LOCK").exists(),
                               "svg": len(list(ctx.figs.glob("*.svg"))), "png": len(list(ctx.figs.glob("*.png")))}
    (out / "run_meta.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False))
    if extra:
        (out / "dryrun_vs_dev.md").write_text("# التشغيل الجاف مقابل نتائج التطوير\n\n" + extra + "\n", encoding="utf-8")
    print(f"[E10] {meta['mode']} {status} in {(time.time() - t0) / 60:.1f} min → {out}")


if __name__ == "__main__":
    main()
