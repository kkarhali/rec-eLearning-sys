"""FR-12: ملخص آلي لميزانية الحوسبة من سجلات الزمن والذاكرة التي كتبها خط التجارب.

    python3 scripts/compute_budget_summary.py [--out results/budget_summary.md] [--check]

يقرأ فقط (لا يكتب شيئاً في results/dev2013/ ولا results/conf2014/ ولا results/frozen/):
  * results/dev2013/timing.csv و results/conf2014/timing.csv: سطر لكل (نموذج، عرض، نقطة قطع، مرحلة) من الحزام
    (src/ml/harness.py): الثواني داخل عملية بخيط حسابي واحد، والذاكرة القصوى للعملية (ru_maxrss)؛
  * ملفات *_meta.json: ثواني المعالج المسجلة لـGRU-lite واستئصال الإشارة، والثواني لتحليل المتعلمين والهجين، وزمن الجدار
    وعدد العمليات لكل تشغيل، وخطوات reproduce_dev.
ويكتب ملخصاً بالعربية في --out (الافتراضي results/budget_summary.md) يقارن كل تشغيل بسقف ثماني ساعات معالج (3-5-8).
ومع --check يفشل (رمز 1) إن اختلف الملف المكتوب عمّا يولّده السكربت الآن، فلا يُعدَّل رقم فيه يدوياً.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DEV, CONF = ROOT / "results" / "dev2013", ROOT / "results" / "conf2014"
CAP_HOURS = 8.0
CAP = CAP_HOURS * 3600


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()[:16]


def jload(p: Path) -> dict:
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def h(sec: float) -> str:
    return f"{sec / 3600:.2f}"


def per_model(t: pd.DataFrame) -> pd.DataFrame:
    g = t.groupby("model")
    out = pd.DataFrame({
        "jobs": g.size(),
        "tune_s": t[t["phase"] == "tune"].groupby("model")["seconds"].sum(),
        "test_s": t[t["phase"] == "test"].groupby("model")["seconds"].sum(),
        "max_job_s": g["seconds"].max(),
        "max_rss_mb": g["maxrss_mb"].max(),
    }).fillna(0.0)
    out["total_s"] = out["tune_s"] + out["test_s"]
    return out.sort_values("total_s", ascending=False)


def table(df: pd.DataFrame) -> list[str]:
    lines = ["| النموذج | أسطر السجل | ضبط (ث) | اختبار (ث) | المجموع (ث) | أطول سطر (ث) | أقصى ذاكرة للعملية (MB) |",
             "|---|---|---|---|---|---|---|"]
    for m, r in df.iterrows():
        lines.append(f"| {m} | {int(r.jobs)} | {r.tune_s:.1f} | {r.test_s:.1f} | {r.total_s:.1f} | {r.max_job_s:.1f} | {r.max_rss_mb:.0f} |")
    lines.append(f"| المجموع | {int(df.jobs.sum())} | {df.tune_s.sum():.1f} | {df.test_s.sum():.1f} | {df.total_s.sum():.1f} | "
                 f"{df.max_job_s.max():.1f} | {df.max_rss_mb.max():.0f} |")
    return lines


def ablation_dedup() -> tuple[float, int]:
    """ثواني استئصال الإشارة دون تكرار: في ablation_tuning.csv يحمل كل سطر نقطة تكرار لـWRMF (iters=…) زمن الملاءمة
    الواحدة نفسه، فيعدّه مجموع ablation_meta.json مرة لكل نقطة. يُحسب هنا الزمن مرة لكل إعداد دون iters، ويُضاف إليه زمن
    ملاءمة الاختبار بالقاعدة نفسها التي في الملف الأصلي. ويعيد (الثواني، عدد الأسطر المكررة المحذوفة)."""
    tun = pd.read_csv(DEV / "ablation_tuning.csv")
    base = tun["config"].str.replace(r"(^|;)iters=\d+", "", regex=True)
    key = tun[["presentation", "cut", "model", "variant"]].astype(str).agg("|".join, axis=1) + "|" + base
    dedup = tun.assign(_k=key).drop_duplicates("_k")
    rows = pd.read_csv(DEV / "ablation_signals.csv")
    fit = rows.drop_duplicates(["model", "variant", "presentation", "cut", "seed"])["fit_score_seconds"].sum()
    return float(dedup["seconds"].sum() + fit), int(len(tun) - len(dedup))


def build() -> str:
    src = [DEV / "timing.csv", CONF / "timing.csv", DEV / "gru_meta.json", DEV / "ablation_meta.json",
           DEV / "learner_meta.json", DEV / "hybrid_meta.json", DEV / "run_meta.json", DEV / "repro_meta.json",
           CONF / "run_meta.json", DEV / "ablation_tuning.csv", DEV / "ablation_signals.csv"]
    missing = [str(p.relative_to(ROOT)) for p in src if not p.exists()]
    if missing:
        raise SystemExit(f"سجلات غائبة: {missing}")
    dev_t, conf_t = pd.read_csv(src[0]), pd.read_csv(src[1])
    gru, abl, lrn, hyb = (jload(p) for p in src[2:6])
    run, repro, conf = jload(src[6]), jload(src[7]), jload(src[8])
    dm, cm = per_model(dev_t), per_model(conf_t)

    harness_s = float(dm.total_s.sum())
    gru_s = float(gru.get("cpu_seconds_tune", 0.0)) + float(gru.get("cpu_seconds_test", 0.0))
    abl_meta = float(abl.get("cpu_seconds", 0.0))
    abl_s, abl_dup = ablation_dedup()
    lrn_s, hyb_s = float(lrn.get("seconds", 0.0)), float(hyb.get("seconds", 0.0))
    measured = harness_s + gru_s + abl_s + lrn_s + hyb_s
    workers = int(run.get("workers", 4))
    repro_wall = float(repro.get("wall_seconds", 0.0))
    repro_bound = repro_wall * workers
    p1, p2 = float(conf.get("phase1_seconds", 0.0)), float(conf.get("phase2_seconds", 0.0))
    cw = int(conf.get("workers", 4))

    L = ["# ملخص ميزانية الحوسبة (FR-12)", "",
         "مولَّد آلياً بالأمر `python3 scripts/compute_budget_summary.py` من سجلات خط التجارب، دون رقم مكتوب يدوياً. "
         "السقف المسجَّل قبل التجميد ثماني ساعات معالج لكل من تشغيل التطوير الكامل والتشغيل التأكيدي (3-5-8، NFR-03).", "",
         "**كيف تُقرأ الأرقام.** كل سطر في `timing.csv` يسجّل ثواني الجدار لمرحلة (ضبط أو اختبار) لنموذج على (عرض، نقطة قطع) "
         "داخل عملية عاملة بخيط حسابي واحد، فهي تقريب لثواني المعالج لذلك السطر. وثواني GRU-lite واستئصال الإشارة مسجّلة ثواني معالج "
         "في ملفاتها. وثواني تحليل المتعلمين والهجين ثواني جدار لعملية واحدة. والحد الأعلى لأي تشغيل = زمن الجدار × عدد العمليات "
         "المتوازية، بافتراض ألا يزيد العمل المتوازي على عددها.", "",
         "## 1. تشغيل التطوير (عروض 2013)", "",
         f"### 1-أ سجل الحزام لخطوط الأساس (`results/dev2013/timing.csv`؛ {dev_t['presentation'].nunique()} عروض × "
         f"{dev_t['cut'].nunique()} نقاط قطع)", ""]
    L += table(dm)
    L += ["", "### 1-ب بقية خطوات التطوير", "",
          "| الخطوة | المصدر | الثواني | النوع |", "|---|---|---|---|",
          f"| خطوط الأساس (سجل الحزام) | `timing.csv` | {harness_s:.1f} | مجموع أسطر الحزام |",
          f"| GRU-lite (ضبط واختبار) | `gru_meta.json` | {gru_s:.1f} | ثواني معالج |",
          f"| استئصال الإشارة | `ablation_tuning.csv` و`ablation_signals.csv` | {abl_s:.1f} | ثواني معالج دون تكرار (انظر الملاحظة) |",
          f"| تحليل المتعلمين | `learner_meta.json` | {lrn_s:.1f} | ثواني جدار (عملية واحدة) |",
          f"| الهجين وقاعدة القبول | `hybrid_meta.json` | {hyb_s:.1f} | ثواني جدار (عملية واحدة) |",
          f"| **المجموع المسجَّل** | | **{measured:.1f}** ({h(measured)} ساعة) | |", "",
          f"ملاحظة: يسجّل `ablation_meta.json` لاستئصال الإشارة {abl_meta:.1f} ثانية. وهذا المجموع يعدّ زمن ملاءمة WRMF الواحدة "
          f"مرة لكل نقطة تكرار محفوظة ({abl_dup} سطراً مكرراً)، فيزيد على الواقع. والرقم في الجدول يعدّ كل ملاءمة مرة واحدة.", "",
          "### 1-ج المقارنة بالسقف", "",
          "| المقياس | الساعات | نسبته من السقف |", "|---|---|---|",
          f"| مجموع ثواني المعالج المسجَّلة (1-ب) | {h(measured)} | {measured / CAP:.1%} |",
          f"| حد أعلى: زمن جدار `reproduce_dev` ({repro_wall:.1f} ث) × {workers} عمليات | {h(repro_bound)} | {repro_bound / CAP:.1%} |",
          "", f"الحكم: {'ضمن' if repro_bound <= CAP else 'يتجاوز'} سقف {CAP_HOURS:.0f} ساعات معالج بالحد الأعلى، "
          f"و{'ضمنه' if measured <= CAP else 'يتجاوزه'} بالمجموع المسجَّل.", "",
          "خطوات `reproduce_dev` وأزمنة جدارها (`repro_meta.json`):", "",
          "| الخطوة | ثواني الجدار |", "|---|---|"]
    L += [f"| {s['step']} | {float(s['seconds']):.1f} |" for s in repro.get("steps", [])]
    L += ["", "## 2. التشغيل التأكيدي (عروض 2014، قراءة فقط)", "",
          f"### 2-أ سجل الحزام لخطوط الأساس (`results/conf2014/timing.csv`؛ {conf_t['presentation'].nunique()} عرضاً × "
          f"{conf_t['cut'].nunique()} نقاط قطع)", ""]
    L += table(cm)
    L += ["", "### 2-ب المقارنة بالسقف لكل طور (`results/conf2014/run_meta.json`)", "",
          "| الطور | زمن الجدار (ث) | حد أعلى = الجدار × العمليات (ساعة) | نسبته من السقف |", "|---|---|---|---|",
          f"| الأول (الفرضيات) | {p1:.1f} | {h(p1 * cw)} | {p1 * cw / CAP:.1%} |",
          f"| الثاني (الحساسية والإنصاف وأثر البروتوكول) | {p2:.1f} | {h(p2 * cw)} | {p2 * cw / CAP:.1%} |", "",
          f"الحكم: الطور الأول {'ضمن' if p1 * cw <= CAP else 'يتجاوز'} السقف، والطور الثاني "
          f"{'ضمن' if p2 * cw <= CAP else 'يتجاوز'} السقف، بالحد الأعلى ({cw} عمليات). "
          "ولا يسجّل الحزام في التأكيدي إلا خطوط الأساس؛ فبقية النماذج داخلة في الحد الأعلى للطور دون سطر خاص بها.", "",
          "## 3. ما لا يغطيه السجل", "",
          "- ذاكرة الخدمة أثناء العرض (NFR-02) لا يسجّلها خط التجارب؛ والذاكرة هنا ذاكرة العمليات العاملة وحدها.",
          "- ثواني الجدار في 1-أ و2-أ تقريب لثواني المعالج بشرط الخيط الحسابي الواحد في العملية العاملة.", "",
          "## المصادر وبصماتها (SHA-256، أول 16 خانة)", "",
          "| الملف | البصمة |", "|---|---|"]
    L += [f"| `{p.relative_to(ROOT)}` | `{sha(p)}` |" for p in src]
    return "\n".join(L) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", default=str(ROOT / "results" / "budget_summary.md"))
    ap.add_argument("--check", action="store_true", help="يفشل إن اختلف الملف الموجود عمّا يولّده السكربت")
    a = ap.parse_args(argv)
    out = Path(a.out)
    text = build()
    locked = [DEV, CONF, ROOT / "results" / "frozen"]
    if any(out.resolve().is_relative_to(d.resolve()) for d in locked):
        print("لا يُكتب داخل results/dev2013 أو conf2014 أو frozen", file=sys.stderr)
        return 2
    if a.check:
        same = out.exists() and out.read_text(encoding="utf-8") == text
        print("budget summary: " + ("identical" if same else "DIFFERS"))
        return 0 if same else 1
    out.write_text(text, encoding="utf-8")
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
