#!/usr/bin/env python3
"""POST-HOC (session 2, م-ك-4 item 2): inventory of results/posthoc/ → results/posthoc/INVENTORY.md.

Lists every file of results/posthoc/ (logs included), what it holds, the tool that writes it, and whether and where
appendix E shows it. "Shown" is detected from the source of scripts/thesis/appendix_e.py at the time this tool runs
(the file names it reads and the exact comparison labels it passes to its tables), so the inventory must be
regenerated after any change of appendix_e.py or of results/posthoc/. Reads no data; no number is computed.

    python3 scripts/posthoc/a9_inventory.py
"""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
PH = ROOT / "results" / "posthoc"
APP = ROOT / "scripts" / "thesis" / "appendix_e.py"

DESC = {
    "README.md": ("—", "وصف كل أداة: الأمر، والزمن، وما تعيد إنتاجه أولاً، والمخرجات"),
    "INVENTORY.md": ("a9_inventory.py", "هذه القائمة"),
    "defense_stats.json": ("defense_stats.py", "إحصاءات المناقشة الأولى: ارتباط عرضي المقرر، والتحليل على المقررات، وفواصل 98.75%، ونسبة δ، وفاصل σ وMDE80 عند طرفيه، وتغطية الفواصل بالمحاكاة"),
    "a4_1_recentpop_sknn.csv": ("a4_1_recentpop_sknn.py", "هجين B3 + SKNN: الأزواج مع B3 ومع HYB\\*، والشبكة الاسمية بلا أرضية مع B3، على العروض والمقررات"),
    "a4_1_recentpop_sknn_per_presentation.csv": ("a4_1_recentpop_sknn.py", "NDCG@10 لكل عرض: الهجين اللاحق بالأرضية وبدونها، وB3 وB5 وHYB\\*"),
    "a4_1_recentpop_sknn_folds.csv": ("a4_1_recentpop_sknn.py", "الأوزان وقيمة التحقق والاختبار لكل (عرض، أصل)، بالأرضية وبالشبكة الاسمية"),
    "a4_1_reproduction_checks.csv": ("a4_1_recentpop_sknn.py", "التحقق من الإعادة"),
    "a4_2_sknn_all.csv": ("a4_2_sknn_all.py", "GRU-lite − SKNN(M = الكل)، وSKNN(M = الكل) − SKNN المقفل، على العروض والمقررات، ومتوسط كل أصل وصفاً، وقراءة سداسية توضيحية"),
    "a4_2_sknn_all_per_presentation.csv": ("a4_2_sknn_all.py", "GRU-lite وSKNN المقفل وSKNN(M = الكل) لكل عرض"),
    "a4_2_sknn_all_rows.csv": ("a4_2_sknn_all.py", "صفوف الاختبار بصيغة baselines.csv لـSKNN المعاد ولـSKNN(M = الكل)"),
    "a4_2_sknn_all_tuning.csv": ("a4_2_sknn_all.py", "قيمة التحقق لكل إعداد جُرِّب لكل طيّة"),
    "a4_2_reproduction_checks.csv": ("a4_2_sknn_all.py", "التحقق من الإعادة"),
    "a4_3_companion_metrics.csv": ("a4_3_companion_metrics.py", "متوسط العروض وانحرافها لكل نموذج وسنة: NDCG وHR وMRR وP وR وCoverage وPopBias عند 10"),
    "a4_3_companion_metrics_per_presentation.csv": ("a4_3_companion_metrics.py", "المقاييس المرافقة لكل عرض"),
    "a4_3_companion_metrics_folds.csv": ("a4_3_companion_metrics.py", "المقاييس المرافقة لكل (عرض، أصل، بذرة)"),
    "a4_3_reproduction_checks.csv": ("a4_3_companion_metrics.py", "التحقق من الإعادة"),
    "a5_nonpersonal_weights.csv": ("a5_nonpersonal_weights.py", "أوزان الهجين غير الشخصي (1)+(6) لكل (سنة، عرض، أصل)، وقيمة التحقق والاختبار، والفرق عن B3"),
    "a5_nonpersonal_weights_counts.csv": ("a5_nonpersonal_weights.py", "عدد الطيّات لكل متجه أوزان"),
    "a5_nonpersonal_weights_per_presentation.csv": ("a5_nonpersonal_weights.py", "الهجين غير الشخصي وB3 وHYB\\* لكل عرض"),
    "a5_nonpersonal_weights_summary.csv": ("a5_nonpersonal_weights.py", "ملخص لكل سنة"),
    "a5_reproduction_checks.csv": ("a5_nonpersonal_weights.py", "التحقق من الإعادة: تفكيك D-60 وHYB\\*"),
    "a6_personalization_mall.csv": ("a6_personalization_mall.py", "مكسب الشخصنة بـSKNN(M = الكل): الأزواج على العروض والمقررات، وصفوف التفكيك المقفل للمرجع"),
    "a6_personalization_mall_per_presentation.csv": ("a6_personalization_mall.py", "كل النماذج لكل عرض"),
    "a6_personalization_mall_folds.csv": ("a6_personalization_mall.py", "الأوزان والقيم لكل (عرض، أصل، نموذج)"),
    "a6_personalization_mall_weights.csv": ("a6_personalization_mall.py", "توزيع الأوزان"),
    "a6_reproduction_checks.csv": ("a6_personalization_mall.py", "التحقق من الإعادة"),
    "a7_delta_sensitivity.csv": ("a7_delta_sensitivity.py", "الحكم بالقاعدة المسجلة عند δ ∈ {0.015، 0.02، 0.025} للأحكام المقفلة ولصفوف sensitivity_other.csv"),
    "a7_delta_scan.csv": ("a7_delta_sensitivity.py", "مدى δ الذي يثبت فيه كل حكم مقفل"),
    "a7_reproduction_checks.csv": ("a7_delta_sensitivity.py", "التحقق من الإعادة"),
    "a8_h3_by_cut.csv": ("a8_h3_by_cut.py", "فروق الجدول هـ-2 لكل أصل بفواصل على العروض والمقررات"),
    "a8_h3_by_cut_per_presentation.csv": ("a8_h3_by_cut.py", "الفرق لكل (زوج، سنة، أصل، عرض)"),
    "a8_reproduction_checks.csv": ("a8_h3_by_cut.py", "التحقق من الإعادة"),
    "a10_selection_loo.csv": ("a10_selection_loo.py", "اختيار الهجين بترك عرض خارجاً: التركيبة المختارة لكل عرض متروك وقيمتها عليه"),
    "a10_selection_loo_folds.csv": ("a10_selection_loo.py", "الأوزان والقيم لكل أصل في العرض المتروك"),
    "a10_selection_loo_stats.csv": ("a10_selection_loo.py", "الاستدلال على العروض والمقررات"),
    "a10_reproduction_checks.csv": ("a10_selection_loo.py", "التحقق من الإعادة"),
    "a11_h3_equal_info.csv": ("a11_h3_equal_info.py", "GRU-lite بمدخل الشعبية الآنية للأقران: الأزواج مع SKNN وGRU-lite وB3 وSKNN(M = الكل)"),
    "a11_h3_equal_info_per_presentation.csv": ("a11_h3_equal_info.py", "النماذج لكل عرض"),
    "a11_h3_equal_info_rows.csv": ("a11_h3_equal_info.py", "صفوف الاختبار بصيغة baselines.csv (خمس بذور)"),
    "a11_h3_equal_info_tuning.csv": ("a11_h3_equal_info.py", "الإعدادات الستة لكل طيّة: أفضل دورة، والتحقق، ومنحنيات الخسارة والتحقق ومعامل a"),
    "a11_gru_eqinfo_sanity.json": ("a11_h3_equal_info.py", "حزمة الصحة S1–S6 للنموذج المعدَّل"),
    "a11_runtime.csv": ("a11_h3_equal_info.py", "تقدير الزمن من طيّة واحدة قبل التشغيل"),
    "a11_reproduction_checks.csv": ("a11_h3_equal_info.py", "التحقق من الإعادة"),
    "a11_h3_equal_info_feasibility.md": ("—", "مذكرة تصميم المقارنة بعد منح GRU-lite إشارة الشعبية الآنية، وتوثيق التشغيل الأول الذي قُطع"),
    "a12_symmetric_info.csv": ("a12_symmetric_info.py", "أقرب مقارنة متاحة إلى التماثل لـH3، والشعبية الآنية مقابل الجيران، ومكسب الشخصنة دون أرضية"),
    "a12_reproduction_checks.csv": ("a12_symmetric_info.py", "التحقق من الإعادة"),
    "sklearn_equivalence.csv": ("sklearn_equivalence.py", "مقارنة التنفيذات اليدوية بـscikit-learn"),
}
WHY_NOT = {
    "README.md": "ملف توثيق",
    "INVENTORY.md": "ملف توثيق",
    "reproduction": "ملف تحقق من الإعادة، يُذكر في README ولا يُعرض جدولاً",
    "rows/folds/tuning": "بيانات تفصيلية للإعادة؛ الملحق يعرض الملخص",
    "new": "بيانات تفصيلية أو مساعدة للأداة؛ الملحق يعرض ملخصها",
    "log": "سجل تشغيل (خارج git بقاعدة *.log)",
}


def git_tracked(p: Path) -> str:
    try:
        out = subprocess.run(["git", "ls-files", "--error-unmatch", str(p.relative_to(ROOT))], cwd=ROOT,
                             capture_output=True).returncode
        return "نعم" if out == 0 else "لا"
    except Exception:
        return "?"


def main():
    src = APP.read_text(encoding="utf-8")
    read_by_app = set(re.findall(r'os\.path\.join\(PH, "([^"]+)"\)', src))
    labels = set(re.findall(r'"([^"]*(?:−|-)[^"]*)"', src))           # string literals with a minus (comparison labels)
    tab_of = {}
    for t, f in re.findall(r'جدول (هـ-\d+)(?:(?!جدول هـ).)*?\(المصدر: results/posthoc/([^)\s*]+)', src, flags=re.S):
        tab_of.setdefault(f, []).append("الجدول " + t)
    files = sorted(p for p in PH.rglob("*") if p.is_file() and "__pycache__" not in p.parts)
    L = ["# جرد `results/posthoc/`", "",
         "مولَّد بـ`python3 scripts/posthoc/a9_inventory.py` (لاحق؛ م-ك-4، البند 2). يُعاد توليده بعد أي تغيير في "
         "`results/posthoc/` أو في `scripts/thesis/appendix_e.py`، لأن عمود «يعرضه الملحق» يُستخرج آلياً من شيفرة "
         "مولّد الملحق هـ وقت التشغيل: الملفات التي يقرؤها، وتسميات المقارنات التي يمررها إلى جداوله حرفياً.", "",
         f"- عدد الملفات: {len(files)}.",
         f"- الملفات التي يقرؤها مولّد الملحق الآن: {', '.join(f'`{x}`' for x in sorted(read_by_app)) or '—'}.",
         "- كل ما في المجلد لاحق، خارج عائلة هولم، وp فيه غير مصححة.", "",
         "## الملفات", "",
         "| الملف | الأداة | المحتوى | في git | يعرضه الملحق هـ؟ | أين / لماذا لا |", "|---|---|---|---|---|---|"]
    detail = []
    for p in files:
        rel = p.relative_to(PH).as_posix()
        name = p.name
        tool, what = DESC.get(name, ("?", "غير موصوف في هذه القائمة: يُراجَع"))
        if rel.startswith("logs/"):
            tool = re.sub(r"\.log$", ".py", name)
            what, shown, where = "سجل الأوامر وأرقام التحقق الدقيقة", "لا", WHY_NOT["log"]
        elif name in read_by_app:
            shown = "نعم"
            where = "، ".join(tab_of.get(name, [])) or "نص الملحق"
        elif "reproduction_checks" in name:
            shown, where = "لا", WHY_NOT["reproduction"]
        elif name in ("README.md", "INVENTORY.md"):
            shown, where = "لا", WHY_NOT[name]
        elif re.match(r"a(5|6|7|8|10|11|12)_", name):
            shown, where = "لا", WHY_NOT["new"]
        else:
            shown, where = "لا", WHY_NOT["rows/folds/tuning"]
        L.append(f"| `{rel}` | `{tool}` | {what} | {git_tracked(p)} | {shown} | {where} |")
        # comparison-level detail for the files the appendix reads
        if name in read_by_app and p.suffix == ".csv":
            df = pd.read_csv(p)
            if "comparison" in df.columns:
                for c in df["comparison"].drop_duplicates():
                    units = sorted(df.loc[df["comparison"] == c, "unit"].astype(str).unique())
                    detail.append((name, c, "نعم" if c in labels else "**لا**", "؛ ".join(units)))
            elif "model" in df.columns:
                for m in df["model"].drop_duplicates():
                    detail.append((name, f"model = {m}", "نعم" if f'"{m}"' in src else "**لا**", "—"))
    L += ["", "## داخل الملفات التي يقرؤها الملحق: أي الصفوف تُعرض", "",
          "المقارنة معروضة إذا مُرِّرت تسميتها حرفياً إلى جدول في `appendix_e.py`. وصفوف «origin t = … alone» لا تُعرض.",
          "", "| الملف | المقارنة أو النموذج | معروضة؟ | الوحدات في الملف |", "|---|---|---|---|"]
    for f, c, s, u in detail:
        L.append(f"| `{f}` | {c} | {s} | {u} |")
    js = PH / "defense_stats.json"
    if js.exists():
        keys = list(json.loads(js.read_text(encoding="utf-8")).keys())
        shown_keys = [k for k in keys if f'"{k}"' in src or f"'{k}'" in src]
        L += ["", f"**`defense_stats.json`:** المفاتيح {', '.join(f'`{k}`' for k in keys)}. "
              f"يقرأ الملحق منها: {', '.join(f'`{k}`' for k in shown_keys)}."]
    L += ["", "## ما لم يُعرض ولماذا (ملخص)", "",
          "- **صفوف الشبكة الاسمية بلا أرضية في `a4_1_recentpop_sknn.csv`:** محسوبة ولا يعرضها الجدول هـ-1 إلا إذا ظهرت "
          "تسميتها أعلاه بـ«نعم».",
          "- **متوسطات الأصول منفردة في `a4_2_sknn_all.csv`:** تعرضها الأداة a8 بفواصلها في `a8_h3_by_cut.csv`.",
          "- **أعمدة P@10 وR@10 والانحرافات، وصفوف B2_Pop وB7_WRMF و«pipeline check»:** في `a4_3_companion_metrics.csv`، "
          "ولا يعرضها الجدول هـ-3.",
          "- **ملفات الأدوات a5 إلى a12:** أُنتجت في الجلسة الثانية، ويعرض الملحق ملخصاتها في الأقسام هـ-7 إلى هـ-10.",
          "- **ملفات التحقق والصفوف التفصيلية:** للإعادة لا للعرض."]
    for name in sorted(read_by_app):
        if not (PH / name).exists():
            L.append(f"- **`{name}`:** يقرؤه مولّد الملحق إن وُجد، وهو غير موجود الآن (لم تُشغَّل أداته).")
    L.append("")
    (PH / "INVENTORY.md").write_text("\n".join(L), encoding="utf-8")
    print(f"written {PH / 'INVENTORY.md'} ({len(files)} files)")


if __name__ == "__main__":
    main()
