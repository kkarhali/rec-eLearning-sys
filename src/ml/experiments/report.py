"""Builds results/<run>/summary.md from the CSV files written by run_baselines (no new numbers).

    python3 -m src.ml.experiments.report results/dev2013
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from ..stats import compare, mde80

MAIN_METRICS = ["NDCG@10", "HR@10", "P@10", "R@10", "MRR@10", "Coverage@10", "PopBias@10"]
REFERENCE = "B3_RecentPop"


def presentation_units(rows: pd.DataFrame, metric_cols, slice_name="all") -> pd.DataFrame:
    """seed mean → origin mean, one value per (task, model, presentation)."""
    r = rows[rows["slice"] == slice_name]
    by_cut = r.groupby(["task", "model", "presentation", "cut"])[metric_cols].mean()
    return by_cut.groupby(["task", "model", "presentation"]).mean().reset_index()


def seed_sd(rows: pd.DataFrame, metric: str) -> pd.Series:
    """Mean over (presentation, origin) of the SD across seeds (stochastic models only)."""
    r = rows[(rows["slice"] == "all") & (rows["seed"] >= 0)]
    if r.empty:
        return pd.Series(dtype=float)
    sd = r.groupby(["task", "model", "presentation", "cut"])[metric].std(ddof=1)
    return sd.groupby(["task", "model"]).mean()


def _fmt(m, s, digits=3):
    if pd.isna(m):
        return "—"
    return f"{m:.{digits}f} ± {s:.{digits}f}"


def _md_table(df: pd.DataFrame) -> str:
    cols = list(df.columns)
    lines = ["| " + " | ".join(str(c) for c in cols) + " |", "|" + "---|" * len(cols)]
    for _, r in df.iterrows():
        lines.append("| " + " | ".join(str(v) for v in r.values) + " |")
    return "\n".join(lines)


def build_summary(out_dir) -> Path:
    out = Path(out_dir)
    rows = pd.read_csv(out / "baselines.csv")
    folds = pd.read_csv(out / "folds.csv")
    timing = pd.read_csv(out / "timing.csv")
    meta = json.loads((out / "run_meta.json").read_text()) if (out / "run_meta.json").exists() else {}
    metric_cols = [c for c in rows.columns if "@" in c]
    units = presentation_units(rows, metric_cols)
    n_pres = units["presentation"].nunique()
    md = []
    md.append("# نتائج خطوط الأساس B1–B9 — عروض التطوير 2013\n")
    md.append("> مولَّد آلياً بـ`src/ml/experiments/report.py` من ملفات CSV في هذا المجلد؛ لا رقم مكتوب يدوياً.")
    md.append(f"> الأمر: `{meta.get('command', 'python3 -m src.ml.experiments.run_baselines')}` · "
              f"commit `{meta.get('git_commit', '?')[:10]}` · بصمة البيانات `{meta.get('data_fingerprint', '?')}` · "
              f"زمن التشغيل {meta.get('wall_seconds', float('nan')) / 60:.1f} دقيقة على {meta.get('workers', '?')} عمليات · "
              f"numpy {meta.get('numpy', '?')} / pandas {meta.get('pandas', '?')} · {meta.get('date', '')}\n")
    md.append("**الوحدة:** العرض. لكل (نموذج، عرض): متوسط البذور ثم متوسط الأصول الثلاثة (70، 126، 182). "
              f"القيمة = المتوسط عبر {n_pres} عروض ± الانحراف المعياري عبر العروض. "
              "«انحراف البذور» = متوسط الانحراف المعياري عبر البذور الخمس لكل (عرض، أصل) للنماذج العشوائية. "
              "الضبط ببذرة واحدة والتقرير بخمس (D-34). B10 EASE مرجعي فقط (D-37). "
              "الكتالوج كامل بلا سوالب معيَّنة؛ الأهداف خارج الكتالوج إخفاق. الإعداد مختار على نافذة التحقق "
              "بـNDCG@10 لكل (عرض، أصل، مهمة) بميزانية ≤ 20 إعداداً.\n")
    md.append("**تنبيه:** هذه أرقام تطوير (2013) لتثبيت التصميم؛ ليست اختباراً للفرضيات (D-09، D-15). "
              "فواصل الثقة وقيم p في الجدول 5 وصفية على 9 عروض فقط (bootstrap-t العنقودي المعيَّر، ADR-004 §2.2).\n")

    for tnum, (task, title) in enumerate((("A", "المهمة A (الأساسية): موارد جديدة"),
                                          ("B", "المهمة B (الثانوية): أي وصول بما فيه الإعادات")), start=1):
        u = units[units["task"] == task]
        sds = seed_sd(rows[rows["task"] == task], "NDCG@10")
        tab = []
        for model, g in u.groupby("model"):
            rec = {"النموذج": model}
            for m in MAIN_METRICS:
                if m in g:
                    rec[m] = _fmt(g[m].mean(), g[m].std(ddof=1))
            key = (task, model)
            rec["انحراف البذور (NDCG@10)"] = f"{sds[key]:.4f}" if key in sds.index else "—"
            tab.append(rec)
        tab = pd.DataFrame(tab)
        tab["_k"] = [u[u["model"] == m]["NDCG@10"].mean() for m in tab["النموذج"]]
        tab = tab.sort_values("_k", ascending=False).drop(columns="_k")
        md.append(f"## الجدول {tnum}: {title}\n")
        md.append(_md_table(tab) + "\n")

    # per presentation, task A
    ua = units[units["task"] == "A"].pivot(index="model", columns="presentation", values="NDCG@10")
    ua = ua.loc[ua.mean(axis=1).sort_values(ascending=False).index]
    md.append("## الجدول 3: NDCG@10 للمهمة A لكل عرض (متوسط الأصول والبذور)\n")
    md.append(_md_table(ua.round(3).reset_index().rename(columns={"model": "النموذج"})) + "\n")

    # per origin, task A
    r = rows[(rows["slice"] == "all") & (rows["task"] == "A")]
    bc = r.groupby(["model", "presentation", "cut"])["NDCG@10"].mean().groupby(["model", "cut"]).mean().unstack()
    bc = bc.loc[bc.mean(axis=1).sort_values(ascending=False).index]
    md.append("## الجدول 4: NDCG@10 للمهمة A لكل أصل (متوسط العروض)\n")
    md.append(_md_table(bc.round(3).reset_index().rename(columns={"model": "النموذج"})) + "\n")

    # deltas vs Recent-Pop, task A
    md.append(f"## الجدول 5: الفرق في NDCG@10 (المهمة A) مقابل {REFERENCE} — وصفي على عروض التطوير\n")
    ref = units[(units["task"] == "A") & (units["model"] == REFERENCE)].set_index("presentation")["NDCG@10"]
    drows = []
    for model, g in units[units["task"] == "A"].groupby("model"):
        if model == REFERENCE:
            continue
        d = (g.set_index("presentation")["NDCG@10"] - ref).dropna()
        c = compare(d.to_numpy())
        drows.append({"النموذج": model, "Δ المتوسط": f"{c['mean']:+.3f}",
                      "فاصل bootstrap-t العنقودي 95%": f"[{c['ci_lo']:+.3f}, {c['ci_hi']:+.3f}]",
                      "المئيني (ملحق)": f"[{c['pct_lo']:+.3f}, {c['pct_hi']:+.3f}]",
                      "p (تبديل إشارات دقيق، 2^9)": f"{c['p']:.4f}",
                      "عروض Δ>0": f"{int((d > 0).sum())}/{len(d)}"})
    md.append(_md_table(pd.DataFrame(drows)) + "\n")

    # cold-start slices (D-28): bottom quartile vs top quartile; "< 5" descriptive
    if (rows["slice"] == "cold_q1").any():
        def sl(name, metric="NDCG@10"):
            u = presentation_units(rows, [metric], name)
            return u[u["task"] == "A"].groupby("model")[metric].mean()
        ra = rows[rows["task"] == "A"]
        n_lt5 = ra[ra["slice"] == "lt5"].groupby(["model"])["n_eval"].mean()
        n_all = ra[ra["slice"] == "all"].groupby(["model"])["n_eval"].mean()
        n_q1 = ra[ra["slice"] == "cold_q1"].groupby(["model"])["n_eval"].mean()
        ct = pd.DataFrame({"NDCG@10 الربع الأدنى": sl("cold_q1").round(3),
                           "HR@10 الربع الأدنى": sl("cold_q1", "HR@10").round(3),
                           "NDCG@10 الربع الأعلى": sl("top_q4").round(3),
                           "NDCG@10 الكل": sl("all").round(3)})
        ct = ct.sort_values("NDCG@10 الربع الأدنى", ascending=False)
        md.append("## الجدول 6: شريحة البدء البارد (D-28، استكشافية): الربع الأدنى من الموارد المختلفة في التدريب "
                  f"بين المقيَّمين لكل (عرض، أصل)، المهمة A — حصة الربع الأدنى ≈ {(n_q1 / n_all).mean():.1%}، "
                  f"وحصة «< 5 موارد» (وصف) ≈ {(n_lt5 / n_all).mean():.1%}\n")
        md.append(_md_table(ct.reset_index().rename(columns={"model": "النموذج"})) + "\n")

    # optimism gap (D-29): validation NDCG@10 of the selected configuration − test NDCG@10
    vcol = "val_NDCG@10"
    if vcol in rows.columns:
        ra = rows[(rows["slice"] == "all") & (rows["task"] == "A")]
        g = ra.groupby(["model", "presentation", "cut"])[[vcol, "NDCG@10"]].mean()
        g = g.groupby(["model", "presentation"]).mean()
        g["gap"] = g[vcol] - g["NDCG@10"]
        gt = g.groupby("model").agg(val=(vcol, "mean"), test=("NDCG@10", "mean"), gap=("gap", "mean"),
                                    gap_sd=("gap", "std")).round(3).sort_values("test", ascending=False)
        md.append("## الجدول 6-ب: فجوة التفاؤل (تحقق − اختبار) للإعداد المختار، NDCG@10، المهمة A (D-29)\n")
        md.append("التحقق (t−14, t] والاختبار (t, t+14] نافذتان مختلفتان زمنياً، فالفجوة تجمع أثر الاختيار وأثر الزمن.\n")
        md.append(_md_table(gt.reset_index().rename(columns={"model": "النموذج"})) + "\n")

    # MDE80 illustration (ADR-004 §2.2): sigma of per-presentation differences of the strongest
    # personal baseline vs Recent-Pop on the development set, used as a proxy for H1
    ua = units[units["task"] == "A"].set_index(["model", "presentation"])["NDCG@10"]
    personal = [m for m in ("B4_ItemKNN", "B5_SKNN", "B6_Markov", "B7_WRMF", "B9_CBF") if m in ua.index]
    if personal and REFERENCE in ua.index:
        best = max(personal, key=lambda m: ua[m].mean())
        sig = float((ua[best] - ua[REFERENCE]).std(ddof=1))
        m80 = mde80(sig, n=13)
        md.append("## الجدول 6-ج: أصغر أثر قابل للكشف بقوة 80% (توضيحي)\n")
        md.append(f"σ (انحراف فروق NDCG@10 لكل عرض بين {best} و{REFERENCE} على التطوير، بديلاً مؤقتاً لـH1) = "
                  f"{sig:.4f}؛ بالقاعدة الكاملة (Δ̄ ≥ 0.02، حد bootstrap-t الأدنى > 0، 4·p < 0.05) على 13 عرضاً: "
                  f"**MDE80 ≈ {m80:.4f}** (`stats.mde80`). يُعاد حسابه بفروق الهجين بعد E2/E3 ويُكتب قبل التجميد.\n")

    # selected configurations
    sel = rows[(rows["slice"] == "all") & (rows["seed"] <= 0)]  # one row per (task, model, pres, cut)
    st = []
    for (task, model), g in sel.groupby(["task", "model"]):
        vc = g["config"].value_counts()
        st.append({"المهمة": task, "النموذج": model, "الإعداد الأكثر اختياراً": vc.index[0],
                   "مرات": f"{vc.iloc[0]}/{len(g)}", "إعدادات مختلفة": len(vc)})
    md.append("## الجدول 7: الإعدادات المختارة على التحقق (المنوال عبر 27 (عرض، أصل))\n")
    md.append(_md_table(pd.DataFrame(st)) + "\n")

    # folds
    f = folds.copy()
    f["evaluated_A_share"] = f["n_eval_A"] / f["n_window_learners"]
    ft = f.groupby("presentation").agg(catalogue=("catalogue", "mean"), density=("density", "mean"),
                                       learners=("n_learners_train", "mean"),
                                       eval_A=("n_eval_A", "mean"), eval_B=("n_eval_B", "mean"),
                                       eval_A_share=("evaluated_A_share", "mean"),
                                       unreachable=("unreachable_share", "mean")).round(3)
    md.append("## الجدول 8: خصائص الطيّات في مرحلة الاختبار (متوسط الأصول الثلاثة)\n")
    md.append("`eval_A_share` = المقيَّمون في المهمة A ÷ المتعلمون النشطون في نافذة الاختبار (أي نشاط غير مستبعد)؛ "
              "`unreachable` = حصة أزواج الاختبار على موارد خارج الكتالوج (إخفاق لكل النماذج).\n")
    md.append(_md_table(ft.reset_index()) + "\n")

    # timing
    tt = timing.groupby(["model", "phase"])["seconds"].sum().unstack().fillna(0).round(1)
    tt["المجموع (ث، CPU-عملية)"] = tt.sum(axis=1).round(1)
    mem = timing.groupby("model")["maxrss_mb"].max().round(0)
    tt["أقصى RSS للعملية (MB)"] = mem
    md.append("## الجدول 9: زمن التدريب والتقييم لكل نموذج (مجموع 27 (عرض، أصل)، ثوانٍ)\n")
    md.append(_md_table(tt.reset_index().rename(columns={"model": "النموذج"})) + "\n")
    md.append("قيم K = 5 و20 والشرائح cold_q1/top_q4/lt5 لكل (عرض، أصل، بذرة) في `baselines.csv`؛ "
              "كل إعدادات الضبط وقيمها على التحقق في `tuning.csv`.\n")
    path = out / "summary.md"
    path.write_text("\n".join(md), encoding="utf-8")
    return path


if __name__ == "__main__":
    print(build_summary(sys.argv[1] if len(sys.argv) > 1 else "results/dev2013"))
