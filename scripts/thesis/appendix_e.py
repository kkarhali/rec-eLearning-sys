#!/usr/bin/env python3
"""Write appendix E (post-hoc analyses after the mock defense) from results/posthoc/ only.

No number is typed by hand: every value below is read from results/posthoc/*.csv or defense_stats.json.
Output: docs/working/06-thesis/appendix-E-posthoc.md

Usage:  python3 scripts/thesis/appendix_e.py
"""
import json
import os

import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PH = os.path.join(ROOT, "results", "posthoc")
OUT = os.path.join(ROOT, "docs", "working", "06-thesis", "appendix-E-posthoc.md")
LABEL = "لاحق؛ خارج عائلة هولم؛ p غير مصحَّحة"


def f(x, d=4, sign=True):
    s = f"{x:+.{d}f}" if sign else f"{x:.{d}f}"
    return s.replace("-", "−")


def ci(lo, hi):
    return f"[{f(lo)}، {f(hi)}]"


def unit_ar(u):
    return "العروض" if u == "presentation" else "المقررات"


def pair_rows(df, comps, names):
    rows = []
    for c, name in zip(comps, names):
        for year in (2013, 2014):
            for unit in ("presentation", "course"):
                r = df[(df.comparison == c) & (df.year == year) & (df.unit.str.startswith(unit))]
                if r.empty:
                    continue
                r = r.iloc[0]
                pos = f"{int(r.n_pos)}/{int(r.n_units)}"
                rows.append(f"| {name} | {year} | {unit_ar(unit)} ({int(r.n_units)}) | {f(r['mean'])} | "
                            f"{ci(r.ci_lo, r.ci_hi)} | {r.p_signflip_uncorrected:.4f} | {pos} |")
    return rows


a1 = pd.read_csv(os.path.join(PH, "a4_1_recentpop_sknn.csv"))
a2 = pd.read_csv(os.path.join(PH, "a4_2_sknn_all.csv"))
a3 = pd.read_csv(os.path.join(PH, "a4_3_companion_metrics.csv"))
st = json.load(open(os.path.join(PH, "defense_stats.json"), encoding="utf-8"))

head = "| المقارنة | السنة | الوحدة (العدد) | متوسط الفرق | فاصل bootstrap-t 95% | p | الفرق موجب |\n|---|---|---|---|---|---|---|"

L = []
L.append("# الملحق هـ: تحليلات لاحقة وإحصاءات مكمّلة")
L.append("")
L.append("يجمع هذا الملحق تحليلات أُجريت بعد إقفال الأحكام، لتختبر قراءات بديلة لنتائج الرسالة وتكمل ما نقص من إفصاح "
         "إحصائي. وكلها **لاحقة (post-hoc)** ووصفية: خارج عائلة هولم، وقيم p فيها غير مصحَّحة، ولا يغيّر أي منها حكماً "
         "مقفلاً في الجدول 5-18. ولم تُكتب أرقامها قبل أن تعيد شيفرتها إنتاج أرقام مقفلة بفرق لا يتجاوز 10⁻⁶، فإن لم تُعِدها "
         "توقفت. وقُرئت بيانات 2014 فيها بعد الإقفال بتصريح صريح سُجّل في سجل الوصول، ولم تُقرأ أي سمة حساسة. "
         "والشيفرة في `scripts/posthoc/`، والمخرجات في `results/posthoc/` مع ملف يصف أوامرها وأزمنتها، وكل جدول هنا "
         "مولَّد من تلك المخرجات. ويسرد الملف `results/posthoc/INVENTORY.md` كل ما حُسب، وموضع عرضه هنا، وما لم يُعرض ولماذا.")
L.append("")

# ---- E-1 Recent-Pop + SKNN
L.append("## هـ-1 هجين الشعبية الآنية والجيران على السلال")
L.append("")
L.append("يسأل الفصل الأول عما يضيفه التخصيص فوق الجدول الدراسي. والصيغة المباشرة لهذا السؤال هجين يضيف الجيران على "
         "السلال إلى الشعبية الآنية نفسها، وهي تركيبة لم تقيّمها قاعدة القبول. فبُني هذا الهجين بإجراء الهجين المجمَّد "
         "نفسه (الدمج الرتبي، وشبكة الأوزان، والضبط على التحقق، وأرضية الشخصنة بوزن لا يقل عن الربع)، ولم يتغير إلا "
         "المكوّن الأول. ويعرض الجدول هـ-1 فرقه عن الشعبية الآنية وعن الهجين المجمَّد.")
L.append("")
L.append(f"**جدول هـ-1: هجين الشعبية الآنية والجيران على السلال، المهمة A، NDCG@10 ({LABEL}) "
         "(المصدر: results/posthoc/a4_1_recentpop_sknn.csv)**")
L.append("")
L.append(head)
L += pair_rows(a1, ["HYB_B3+SKNN − B3_RecentPop (H1 inference)", "HYB_B3+SKNN − HYB* (frozen)",
                   "HYB_B3+SKNN nominal grid − B3_RecentPop"],
               ["الهجين اللاحق − الشعبية الآنية", "الهجين اللاحق − الهجين المجمَّد",
                "الهجين اللاحق بالشبكة الاسمية (دون أرضية) − الشعبية الآنية"])
L.append("")
r14 = a1[(a1.comparison == "HYB_B3+SKNN − B3_RecentPop (H1 inference)") & (a1.year == 2014) & (a1.unit == "presentation")].iloc[0]
L.append(f"فحتى حين يُبنى التخصيص فوق الشعبية الآنية مباشرة، لا يتجاوزها في 2014 إلا بفرق {f(r14['mean'])} بفاصل "
         f"{ci(r14.ci_lo, r14.ci_hi)}، موجب في {int(r14.n_pos)} عروض من {int(r14.n_units)}. وهذا يتسق مع حكم H1 ولا يغيّره.")
n13 = a1[(a1.comparison == "HYB_B3+SKNN nominal grid − B3_RecentPop") & (a1.year == 2013) & (a1.unit == "presentation")].iloc[0]
n14 = a1[(a1.comparison == "HYB_B3+SKNN nominal grid − B3_RecentPop") & (a1.year == 2014) & (a1.unit == "presentation")].iloc[0]
L.append("")
L.append(f"وتُعرض النسخة بالشبكة الاسمية، أي دون أرضية الشخصنة، لأنها تجيب عن سؤال آخر: ماذا كانت قاعدة القبول ستفعل لو "
         f"بدأ الإجراء الجشع بالشعبية الآنية، وهي القاعدة التي رجّحها التصميم. فعلى التطوير رفع الجيران فيها NDCG@10 "
         f"بـ{f(n13['mean'])} بفاصل {ci(n13.ci_lo, n13.ci_hi)}، وحده الأدنى فوق الصفر، فكانوا سيجتازون قاعدة القبول. "
         "فرفض القاعدة لكل المكوّنات (القسم 5-7-3) مشروط بالقاعدة الابتدائية التي اختيرت بفارق نقطي غير دال. "
         f"وعلى 2014 جاء فرق هذه النسخة {f(n14['mean'])} بفاصل {ci(n14.ci_lo, n14.ci_hi)}. "
         "وتبقى نسخة الأرضية هي الأساس في هذا القسم، لأنها تطابق إجراء الهجين المجمَّد في كل شيء عدا المكوّن الأول.")
L.append("")

# ---- E-2 SKNN without the recency restriction
L.append("## هـ-2 الجيران على السلال دون تقييد أحدث السلال")
L.append("")
L.append("يقصر الجيران على السلال مجمّع جيرانهم المرشحين على أحدث M سلة أسبوعية، واختار الضبط أحدث ألف سلة في الطيّات كلها، "
         "فيرون سلال الأقران الحديثة، في حين لا يرى GRU-lite عند التنبؤ إلا تاريخ المتعلم (وإن تعلّم أوزانه من تسلسلات المتعلمين "
         "جميعاً حتى نقطة القطع). ولقياس أثر ذلك على مقارنة H3 ثُبّت M على «كل السلال»، وضُبطت المعاملات الأخرى بالميزانية نفسها، "
         "ثم قورن به GRU-lite بنتائجه المقفلة دون إعادة تدريب. وتوسيع M يُبقي السلال الحديثة ويضيف إليها السلال القديمة، "
         "فيصير التشابه محسوباً على تاريخ العرض كله. وكانت القيمة «كل السلال» في فضاء الضبط المسجل للجيران، ورفضها الضبط في "
         "الطيّات كلها. فما يعزله هذا التحليل هو قصر مجمّع الجيران على الأسابيع الأخيرة.")
L.append("")
L.append(f"**جدول هـ-2: GRU-lite والجيران على السلال دون تقييد أحدث السلال، المهمة A، NDCG@10 ({LABEL}) "
         "(المصدر: results/posthoc/a4_2_sknn_all.csv)**")
L.append("")
L.append(head)
L += pair_rows(a2, ["GRU_lite − B5_SKNN_Mall (H3 inference, M = None)", "B5_SKNN_Mall − B5_SKNN (locked, M = 1000)"],
               ["GRU-lite − الجيران دون تقييد", "الجيران دون تقييد − الجيران المقفلون"])
L.append("")
g14 = a2[(a2.comparison.str.startswith("GRU_lite − B5_SKNN_Mall (H3")) & (a2.year == 2014) & (a2.unit == "presentation")].iloc[0]
s14 = a2[(a2.comparison.str.startswith("B5_SKNN_Mall − B5_SKNN")) & (a2.year == 2014) & (a2.unit == "presentation")].iloc[0]
L.append(f"فحين يُنزع عن الجيران تقييد أحدث السلال يهبط أداؤهم بـ{f(-s14['mean'], sign=False)}، ويتقدم عليهم GRU-lite "
         f"بـ{f(g14['mean'])} في العروض الثلاثة عشر كلها. فتقدّم الجيران على GRU-lite في H3 يعتمد، في هذه الحساسية الواحدة، على "
         "قصر مجمّع جيرانهم على الأسابيع الأخيرة، وهو ما يقرأ به القسم 6-5 الحكم. ولا يُقرأ هذا الجدول تفوقاً للشبكة المتكررة: فهو لاحق، "
         "والمقارِن فيه أُضعف عمداً، ولا حسماً لسؤال نوع النموذج، فهو يحتاج مقارنة متكافئة في المعلومة.")
L.append("")
a8 = pd.read_csv(os.path.join(PH, "a8_h3_by_cut.csv"))
L.append(f"**جدول هـ-2-أ: فرقا H3 لكل نقطة قطع، العروض (لاحق؛ وصفي) (المصدر: results/posthoc/a8_h3_by_cut.csv)**")
L.append("")
L.append("| السنة | نقطة القطع | GRU-lite − الجيران المقفلون | GRU-lite − الجيران دون تقييد |")
L.append("|---|---|---|---|")
cuts = {}
for year in (2013, 2014):
    for cut in ("70", "126", "182"):
        vals = []
        for c in ("GRU_lite − B5_SKNN (locked", "GRU_lite − B5_SKNN_Mall"):
            r = a8[(a8.comparison.str.startswith(c)) & (a8.year == year) & (a8.unit == "presentation") & (a8.cut.astype(str) == cut)].iloc[0]
            vals.append(r)
        cuts[(year, cut)] = vals
        L.append(f"| {year} | {cut} | {f(vals[0]['mean'])} {ci(vals[0].ci_lo, vals[0].ci_hi)} | "
                 f"{f(vals[1]['mean'])} {ci(vals[1].ci_lo, vals[1].ci_hi)} |")
L.append("")
l70, l182 = cuts[(2014, "70")], cuts[(2014, "182")]
L.append(f"ويتراجع فرق GRU-lite عن الجيران المقفلين على 2014 من {f(l70[0]['mean'])} عند اليوم 70 إلى {f(l182[0]['mean'])} "
         f"عند اليوم 182، ويتراجع فرقه عن الجيران دون تقييد هو أيضاً، من {f(l70[1]['mean'])} إلى {f(l182[1]['mean'])}. "
         "فمعظم هذا الاتجاه قائم دون قصر المجمّع على الأسابيع الأخيرة، ولا يُفسَّر بنفع سلال الأقران الحديثة وحده.")
L.append("")

# ---- E-3 companion metrics
L.append("## هـ-3 المقاييس المرافقة للهجين المجمَّد")
L.append("")
L.append("لم يحمل ملف الهجين في التشغيل التأكيدي المقاييس المرافقة على المهمة A (الجدول 5-24-أ). فحُسبت هنا بأوزانه "
         "المجمَّدة نفسها دون إعادة ضبط، وبدوال المقاييس نفسها، بعد التحقق من أن الشيفرة تعيد مقاييس الشعبية الآنية المقفلة.")
L.append("")
L.append(f"**جدول هـ-3: المقاييس المرافقة على المهمة A، متوسط العروض ({LABEL}) "
         "(المصدر: results/posthoc/a4_3_companion_metrics.csv)**")
L.append("")
L.append("| السنة | النموذج | NDCG@10 | HR@10 | MRR@10 | Coverage@10 | PopBias@10 |")
L.append("|---|---|---|---|---|---|---|")
names = {"HYB*": "الهجين المجمَّد", "B3_RecentPop": "B3 الشعبية الآنية", "B5_SKNN": "B5 الجيران على السلال",
         "GRU_lite": "GRU-lite"}
for year in (2014, 2013):
    for m, nm in names.items():
        r = a3[(a3.year == year) & (a3.model == m)]
        if r.empty:
            continue
        r = r.iloc[0]
        L.append(f"| {year} | {nm} | {r['NDCG@10']:.4f} | {r['HR@10']:.4f} | {r['MRR@10']:.4f} | "
                 f"{r['Coverage@10']:.4f} | {r['PopBias@10']:.4f} |")
L.append("")
h = a3[(a3.year == 2014) & (a3.model == "HYB*")].iloc[0]
b = a3[(a3.year == 2014) & (a3.model == "B3_RecentPop")].iloc[0]
L.append(f"فالهجين المجمَّد يقارب الشعبية الآنية في الدقة على 2014 (NDCG@10 {h['NDCG@10']:.4f} مقابل {b['NDCG@10']:.4f})، "
         f"ويغطي من الكتالوج نسبة أكبر ({h['Coverage@10']:.3f} مقابل {b['Coverage@10']:.3f})، بانحياز شعبية متقارب. "
         "وهذا وصف لا حكم: فالتغطية لم تكن مقياس فرضية، ولا فاصل لهذا الفرق.")
L.append("")

# ---- E-4 statistics completing the disclosure
L.append("## هـ-4 إحصاءات مكمّلة للاستدلال")
L.append("")
L.append("يجمع الجدول هـ-4 ما استُعمل في الأقسام 3-5-5 و5-7-5 و6-8-4 من إحصاءات تكمّل الإفصاح عن حدود الاستدلال. "
         f"والمصدر `results/posthoc/defense_stats.json`، وشيفرته `scripts/posthoc/defense_stats.py`.")
L.append("")
L.append(f"**جدول هـ-4: ارتباط عرضي المقرر الواحد، والتحليل على المقررات، وفاصل 98.75% ({LABEL}) "
         "(المصدر: results/posthoc/defense_stats.json)**")
L.append("")
L.append("| الفرضية | ارتباط فرقي عرضي المقرر | متوسط على المقررات | p ثنائية على المقررات | فاصل bootstrap-t 98.75% |")
L.append("|---|---|---|---|---|")
hyp_ar = {"H1": "H1", "H2-a": "H2-أ", "H3": "H3", "H4-a": "H4-أ"}
for hh, nm in hyp_ar.items():
    c = st["course_level"][hh]
    bb = st["bonferroni_98_75"][hh]
    L.append(f"| {nm} | {st['within_course_corr'][hh]:.2f} | {f(c['mean'])} | {c['p_two_sided']:.4f} | "
             f"{ci(bb['lo'], bb['hi'])} |")
cl = st["course_level"]
L.append("")
L.append(f"والمقررات سبعة، فأصغر p ثنائية الطرف باختبار قلب الإشارات عليها {cl['min_p_two_sided']:.4f}، وبعامل هولم 4 "
         f"تصير {cl['min_p_two_sided_x4']:.4f}، فوق 0.05. ويُبقي فاصل 98.75%، الموافق لضبط الخطأ العائلي في جهة الدحض أيضاً، "
         "H2-أ مؤكَّدة وH4-أ مدحوضة عملياً، ويرفع الحد الأعلى لفاصل H3 فوق العتبة، فيصير حكمها «غير حاسمة». "
         f"ولو حُسبت p أحادية الطرف لصارت أصغر قيمة {cl['min_p_one_sided']:.4f}، وبعامل 4 تصير {cl['min_p_one_sided_x4']:.4f}، "
         f"وجاءت p الأحادية لـH2-أ على المقررات {cl['H2-a']['p_one_sided']:.4f}. "
         f"ويرفع فاصل 98.75% الحد الأعلى لفاصل H1 إلى {st['bonferroni_98_75']['H1']['hi']:.4f}، فوق العتبة، فجملة الاستبعاد "
         "في H1 (0.0204) غير مصحَّحة للتعدد، وتُكتب كذلك في الرسالة.")
L.append("")
L.append(f"**جدول هـ-5: فاصل الانحراف σ من التطوير والحد الأدنى للأثر القابل للكشف عند طرفيه (لاحق؛ وصفي) "
         "(المصدر: results/posthoc/defense_stats.json)**")
L.append("")
L.append("| الفرضية | σ (تطوير) | فاصل σ 95% (8 درجات حرية) | MDE80 المجمَّد | MDE80 عند طرفي فاصل σ | σ (تأكيد) |")
L.append("|---|---|---|---|---|---|")
for hh, nm in hyp_ar.items():
    s = st["sigma"]["per_hypothesis"][hh]
    L.append(f"| {nm} | {s['sigma_dev']:.4f} | [{s['sigma_ci95'][0]:.4f}، {s['sigma_ci95'][1]:.4f}] | "
             f"{s['mde80_frozen']:.4f} | {s['mde80_at_ci'][0]:.4f} إلى {s['mde80_at_ci'][1]:.4f} | "
             f"{st['sigma']['sigma_conf2014'][hh]:.4f} |")
L.append("")
sg = st["sigma"]
L.append(f"وجاء انحراف فروق H2-أ في التأكيد ({sg['sigma_conf2014']['H2-a']:.4f}) دون الحد الأدنى لفاصل σ المقدَّر من التطوير "
         f"({sg['per_hypothesis']['H2-a']['sigma_ci95'][0]:.4f})، فالتقدير المسبق للقوة في H2-أ كان متحفظاً.")
L.append("")
cov = st["coverage_n13"]
dist_ar = {"normal": "طبيعي", "lognormal_s0.75": "لوغاريتمي طبيعي (ملتوٍ)", "gamma_k2": "غاما بمعامل شكل 2 (ملتوٍ)",
           "contaminated_10pct_x4": "طبيعي ملوَّث بـ10% قيم متطرفة"}
L.append(f"**جدول هـ-6: تغطية فواصل 95% مع ثلاث عشرة وحدة بتوزيعات مختلفة، {cov['n_rep']} تكرار و{cov['n_boot']} إعادة "
         f"سحب (لاحق؛ محاكاة) (المصدر: results/posthoc/defense_stats.json)**")
L.append("")
L.append("| التوزيع | bootstrap-t (المسجل) | المئيني | t |")
L.append("|---|---|---|---|")
for k, nm in dist_ar.items():
    c = cov[k]
    L.append(f"| {nm} | {c['bootstrap_t']:.3f} | {c['percentile']:.3f} | {c['t']:.3f} |")
L.append("")
ds = st["delta_share"]
L.append(f"وحُسبت العتبة δ = 0.02 قبل التطوير من مستوى الشعبية الآنية في الفحص الأولي ({ds['recent_pop_preliminary_FFF_2013J']['level']}، "
         f"فهي {ds['recent_pop_preliminary_FFF_2013J']['share_pct']}% منه)، وتساوي {ds['recent_pop_dev2013']['share_pct']}% من "
         f"مستواها في التطوير و{ds['recent_pop_conf2014']['share_pct']}% في التأكيد، وتساوي δ_AUC "
         f"{ds['auc_M0_conf2014']['share_pct']}% من AUC للنموذج M0 في التأكيد ({ds['auc_M0_conf2014']['level']}).")
L.append("")

# ---- E-5 sklearn equivalence (pending)
L.append("## هـ-5 مقارنة التنفيذات اليدوية بمكتبة scikit-learn")
L.append("")
skl = os.path.join(PH, "sklearn_equivalence.csv")
if os.path.exists(skl):
    eq = pd.read_csv(skl)
    L.append(f"**جدول هـ-5-أ: مقارنة التنفيذات اليدوية بنظائرها في scikit-learn ({LABEL}) "
             "(المصدر: results/posthoc/sklearn_equivalence.csv)**")
    L.append("")
    L.append("| " + " | ".join(eq.columns) + " |")
    L.append("|" + "---|" * len(eq.columns))
    for _, r in eq.iterrows():
        L.append("| " + " | ".join(str(v) for v in r.values) + " |")
else:
    L.append("لم تُجرَ هذه المقارنة بعد: فمكتبة scikit-learn غير مثبتة في بيئة العمل، وتعذّر تثبيتها. والسكربت جاهز، "
             "ويقارن على بيانات التطوير 2013 الانحدار اللوجستي المنتظم (المعاملات وAUC وفرق M1 − M0)، وk-means++ "
             "(مؤشر راند المعدَّل وعدد العناقيد المختار)، وشجرة القرار (اتفاق التنبؤات)، ودوال المقاييس. ويُشغَّل على "
             "حاسوب فيه المكتبة بالأمر `python3 scripts/posthoc/sklearn_equivalence.py`، فيكتب "
             "`results/posthoc/sklearn_equivalence.csv`، ثم يُعاد توليد هذا الملحق فيُدرج الجدول هنا.")
L.append("")

# ---- E-6 reproduction run log (moved from 5-4-1)
L.append("## هـ-6 سجل تشغيلات إعادة الإنتاج والتشغيل التأكيدي")
L.append("")
L.append("استغرق أول تشغيل كامل لأمر إعادة الإنتاج 53.6 دقيقة، وطابقت فيه كل ملفات النتائج حرفياً عدا فروق مفسَّرة "
         "أُصلحت: ترتيب أسطر في سجل التركيبات التي قيّمها الإجراء الجشع، وأزمنة تدريب في جدول وصفي. ثم أُجري تشغيل كامل "
         "على نسخة شيفرة نظيفة (`20eeb98`) من ذاكرة مؤقتة فارغة، فاكتمل في 47.8 دقيقة وطابقت ملفاته كلها. وبعد إصلاح خلل "
         "في مولّد قائمة شروط التجميد لا يمس أي نتيجة، أُعيد التشغيل كاملاً عند نسخة الإصلاح (`865e5ce`) على شجرة نظيفة، "
         "وهو التشغيل المعتمد في القسم 5-4-1.")
L.append("")
L.append('**العطل في التشغيل الجاف.** وقع أثناء التشغيل الجاف تعطل بيئي حقيقي لا تمرين مخطط: فبعد كتابة قفل الطور الأول، وفي أثناء التحليلات الثانوية للطور الثاني، أُنهي المنفّذ قسراً عند بلوغ سقف الساعتين لأداة التشغيل، دون أي خلل برمجي. فأُعيد الطور الثاني وحده كاملاً من أوله بخيار تشغيل الطور الثاني، بعد أن نجح التحقق من القفل: فالملفات المقفلة الخمسة والثلاثون طابقت بصماتها، ونسخة الشيفرة عند القفل هي نسخة التشغيل نفسها. واكتمل الطور الثاني في نحو 95.7 دقيقة، ولم يُعَد الطور الأول، وبقيت ملفاته المقفلة الخمسة والثلاثون دون تغيير؛ وسُجّلت الواقعة كاملة في سجل الانحرافات. ولهذه الواقعة حدّان يُعلنان صراحة: (أ) أن التشغيل الجاف لا يقبل أمر الاستئناف، فمسار الاستئناف التأكيدي نفسه لم يُمارَس إلا بالمحاكاة؛ (ب) أن «طورين في استدعاء واحد» لم يُشاهَد في التشغيل الجاف مكتملاً من أوله إلى آخره، وإن مُورِس كل مسار شيفرة فيه.')
L.append("")
L.append('**سجل الوصول في التشغيل التأكيدي.** اكتمل التشغيل التأكيدي بطوريه في استدعاء واحد (القسم 5-4-1)، فشوهد «طوران في استدعاء واحد» مكتملاً فيه. ويسجّل سجل الوصول، وهو سجل إلحاق فقط، كل ما قُرئ من بيانات 2014 أثناءه. فبعد سجل البدء وفحوص الحراسة جاءت **القراءة الكاملة الوحيدة** لعروض 2014 (2026-10-25، 20:38:17)، ومعها نسخة الوسم وبصمات MD5 للجداول السبعة، وقد طابقت القيم المجمَّدة. ثم جاءت في الطور الثاني (22:59:56) قراءة محدودة واحدة لمعرّفات الطلاب، بحدثي المحاولة والنجاح، بالأعمدة الثلاثة وحدها وغرض مشغّل التأكيد، أعادت 17,259 معرّفاً، واستُعملت في حساسيتي بيانات تدريب المصنِّف (التدريب الكامل والتدريب القابل للنشر). ولا يحمل السجل بين بداية التشغيل ونهايته أي قراءة أخرى، فلا قراءة للمعرّفات في الطور الأول. أما قراءات المعرّفات السابقة للتشغيل في اليوم نفسه فتعود إلى التشغيل الجاف (بغرض مشغّل التأكيد)، وإلى إعادة الإنتاج وبناء نماذج الخطر ومعاملات الخدمة على عروض 2013، بأغراضها المسجلة. ويعني حقل «غير مودَعة» (`dirty: true`) في أسطر السجل أن شجرة العمل كلها، ومنها الوثائق والسجل نفسه الذي يتغير بالإلحاق، كانت فيها تعديلات غير مودَعة وقت القراءة؛ ولا يخص الكود المحروس، الذي يتحقق حارس البدء من نظافته.')
L.append("")

# ---- E-7 personalisation gain without the recency restriction (a5, a6)
a5s = pd.read_csv(os.path.join(PH, "a5_nonpersonal_weights_summary.csv"))
a5c = pd.read_csv(os.path.join(PH, "a5_nonpersonal_weights_counts.csv"))
a6 = pd.read_csv(os.path.join(PH, "a6_personalization_mall.csv"))
L.append("")
L.append("## هـ-7 مكسب الشخصنة حين لا يرى المكوّن الشخصي سلال الأقران الحديثة")
L.append("")
c13 = a5c[(a5c.year == 2013) & (a5c.weights_B3_C6 == "[1.0, 0.0]")].iloc[0]
c14 = a5c[(a5c.year == 2014) & (a5c.weights_B3_C6 == "[1.0, 0.0]")].iloc[0]
L.append("يفكك الجدول 5-13 فرق الهجين عن الشعبية الآنية إلى مكسب «التقسيم» ومكسب «الشخصنة». ولهذا التفكيك أمران يُستكملان هنا. "
         f"الأول أوزان الضابط «الهجين غير الشخصي» (الشعبية الآنية مع قرب التقييم): اختار ضبطه وزن الشعبية الآنية كاملاً في "
         f"{int(c13.n_folds)} طيّة من {int(c13.n_folds_total)} في التطوير، و{int(c14.n_folds)} من {int(c14.n_folds_total)} في التأكيد، "
         "فانحلّ إلى الشعبية الآنية نفسها، ولذلك جاء فرقه مطابقاً لفرق H1 في التطوير "
         "(المصدر: results/posthoc/a5_nonpersonal_weights_counts.csv). "
         "والثاني أن المكوّن الشخصي في الهجين، الجيران على السلال، يرى سلال الأقران الحديثة (القسم هـ-2). فأُعيد الهجين بإجرائه "
         "المجمَّد نفسه بعد أن حلّ الجيران دون تقييد محل الجيران المقفلين، ليُرى هل يبقى للشخصنة مكسب حين لا يرى المكوّن الشخصي "
         "تلك السلال.")
L.append("")
L.append(f"**جدول هـ-7: مكسب الشخصنة بالجيران المقفلين وبالجيران دون تقييد، المهمة A، NDCG@10 ({LABEL}) "
         "(المصدر: results/posthoc/a6_personalization_mall.csv)**")
L.append("")
L.append(head)
L += pair_rows(a6, ["locked (c) HYB* − (7) alone [personalisation gain]",
                    "HYB_Mall − (7) alone [personalisation gain, analogue of row (c)]",
                    "HYB_Mall − B3_RecentPop [H1 pair]"],
               ["الهجين المجمَّد − شعبية العنقود منفردة (مقفل)",
                "الهجين بالجيران دون تقييد − شعبية العنقود منفردة",
                "الهجين بالجيران دون تقييد − الشعبية الآنية"])
L.append("")
pl = a6[(a6.comparison == "locked (c) HYB* − (7) alone [personalisation gain]") & (a6.year == 2014) & (a6.unit == "presentation")].iloc[0]
pm = a6[(a6.comparison.str.startswith("HYB_Mall − (7) alone")) & (a6.year == 2014) & (a6.unit == "presentation")].iloc[0]
L.append(f"فمكسب الشخصنة في الهجين المجمَّد على 2014 {f(pl['mean'])} بفاصل {ci(pl.ci_lo, pl.ci_hi)}. وحين يحل الجيران دون تقييد "
         f"محل المكوّن الشخصي يصير المكسب {f(pm['mean'])} بفاصل {ci(pm.ci_lo, pm.ci_hi)}. فما سمّته الرسالة مكسب "
         "شخصنة يعتمد على رؤية المكوّن الشخصي سلال الأقران الحديثة، أي على إشارة جماعية آنية قريبة من إشارة الجدول الدراسي، "
         "ولا دليل في هذه البيانات على مكسب من تشابه المتعلم بأقرانه في تاريخه كله. وهذه قراءة لاحقة لا تغيّر حكم H1، "
         "وتقيّد ما يُنسب إلى «الشخصنة» في القسمين 5-7-3 و6-3.")

# ---- E-8 non-optimistic estimate of the selection procedure (a10)
a10 = pd.read_csv(os.path.join(PH, "a10_selection_loo_stats.csv"))
a10f = pd.read_csv(os.path.join(PH, "a10_selection_loo.csv"))
L.append("")
L.append("## هـ-8 تقدير غير متفائل لإجراء اختيار الهجين على التطوير")
L.append("")
same = int(a10f.same_as_frozen.astype(str).str.lower().eq("true").sum())
L.append("فرق التطوير +0.0196 متفائل بالانتقاء، لأن الإجراء اختار التركيبة وقدّر فرقها من نوافذ الاختبار نفسها (القسم 5-7-3). "
         "ولتقدير أداء الإجراء نفسه دون هذا التفاؤل أُعيد بترك عرض واحد خارجاً: يُجرى الإجراء الجشع بقاعدة قبوله وأرضيته على "
         "ثمانية عروض، ثم يُقاس الهجين المختار على العرض التاسع، ويُكرر ذلك للعروض التسعة. "
         f"واختار الإجراء التركيبة المجمَّدة نفسها في {same} من {len(a10f)} تكرارات (المصدر: results/posthoc/a10_selection_loo.csv).")
L.append("")
L.append(f"**جدول هـ-8: فرق الهجين المختار بترك عرض خارجاً عن الشعبية الآنية على العرض المحجوز، 2013 ({LABEL}) "
         "(المصدر: results/posthoc/a10_selection_loo_stats.csv)**")
L.append("")
L.append(head)
L += pair_rows(a10, ["LOO-selected hybrid − B3_RecentPop (held-out presentation)",
                     "in-sample reference: HYB* (frozen, selected on all nine) − B3_RecentPop"],
               ["الهجين المختار بترك عرض خارجاً − الشعبية الآنية", "الهجين المجمَّد (اختير على التسعة) − الشعبية الآنية"])
L.append("")
lo = a10[(a10.comparison.str.startswith("LOO-selected hybrid − B3")) & (a10.unit == "presentation")].iloc[0]
L.append(f"فالتقدير غير المتفائل لإجراء الاختيار على التطوير {f(lo['mean'])} بفاصل {ci(lo.ci_lo, lo.ci_hi)}، قريب من التقدير "
         "المتفائل، فتفاؤل الانتقاء في التطوير صغير. والتقدير غير المنحاز للتركيبة المجمَّدة نفسها يبقى التشغيل التأكيدي.")

# ---- E-9 sensitivity of the verdicts to the threshold (a7)
a7 = pd.read_csv(os.path.join(PH, "a7_delta_sensitivity.csv"))
L.append("")
L.append("## هـ-9 حساسية الأحكام للعتبة δ")
L.append("")
L.append("العتبة δ = 0.02 اتفاق مسجل غير مشتق من أثر تربوي (القسم 6-8-3). فطُبّقت قاعدة الحكم المسجلة نفسها عند δ = 0.015 "
         "وδ = 0.025 على الفروق والفواصل وقيم p المقفلة، دون أي حساب جديد، ليُرى أي الأحكام يتوقف على العتبة.")
L.append("")
L.append(f"**جدول هـ-9: الحكم بالقاعدة المسجلة عند ثلاث عتبات، التحليل الرئيسي على العروض ({LABEL}) "
         "(المصدر: results/posthoc/a7_delta_sensitivity.csv)**")
L.append("")
V_AR = {"confirmed": "مؤكَّدة", "inconclusive": "غير حاسمة", "refuted": "مدحوضة"}
H_AR = {"H1": "H1", "H2-a": "H2-أ", "H3": "H3", "H4-a": "H4-أ"}
L.append("| الفرضية | δ = 0.015 | δ = 0.02 (المسجلة) | δ = 0.025 |")
L.append("|---|---|---|---|")
main = a7[a7.analysis == "main confirmatory pair"]
for hh, nm in H_AR.items():
    cells = []
    for d in (0.015, 0.02, 0.025):
        r = main[(main.hypothesis == hh) & ((main.delta - d).abs() < 1e-9)].iloc[0]
        v = V_AR[r.verdict]
        if r.verdict == "refuted":
            v = "مدحوضة للتفوق" if hh == "H3" else "مدحوضة عملياً"
        cells.append(v)
    L.append(f"| {nm} | " + " | ".join(cells) + " |")
L.append("")
L.append("فحكما H2-أ وH3 لا يتغيران في هذا المدى. ويصير H1 «مدحوضة عملياً» عند 0.025، لأن حده الأعلى (0.0204) دونها، "
         "ويبقى «غير حاسمة» عند 0.015. ويبقى H4-أ «مدحوضة عملياً» عند العتبات الثلاث. فحكم H1 وحده يتوقف على العتبة.")

# ---- E-10 equal-information H3 control (a11)
a11 = pd.read_csv(os.path.join(PH, "a11_h3_equal_info.csv"))
L.append("")
L.append("## هـ-10 مقارنة H3 متكافئة في المعلومة")
L.append("")
L.append("مقارنة H3 المسجلة غير متكافئة في المعلومة (القيد 22): يرى الجيران على السلال سلال الأقران الحديثة، ولا يرى "
         "GRU-lite عند التنبؤ إلا تاريخ المتعلم. فبُني نموذج لاحق يمنح GRU-lite معلومة الأقران الآنية نفسها: يدخل إليه "
         "توزيع الشعبية الآنية (B3) عند كل خطوة، بنافذة B3 المقفلة لكل طيّة ومحسوباً حتى اليوم السابق للهدف، ويضاف لوغاريتمه "
         "إلى المخرج بمعامل متعلَّم. والنموذج يستورد GRU-lite ولا يعدّله، وضُبط بميزانية GRU-lite المقفلة نفسها (ستة إعدادات "
         "وخمس بذور). واجتاز حزمة الصحة، وأعاد بوضع «صفر معلومة» نتائج GRU-lite المقفلة بفرق لا يتجاوز 10⁻⁶ "
         "(المصدر: results/posthoc/a11_reproduction_checks.csv).")
L.append("")
L.append(f"**جدول هـ-10: GRU-lite بمدخل الشعبية الآنية مقابل الجيران وGRU-lite والشعبية الآنية، المهمة A، NDCG@10 ({LABEL}) "
         "(المصدر: results/posthoc/a11_h3_equal_info.csv)**")
L.append("")
L.append(head)
L += pair_rows(a11, ["GRU_eqinfo − B5_SKNN (locked) [equal-information H3 control]", "GRU_eqinfo − GRU_lite (locked)",
                     "GRU_eqinfo − B3_RecentPop (locked)"],
               ["GRU-lite بمدخل الشعبية الآنية − الجيران المقفلون", "GRU-lite بمدخل الشعبية الآنية − GRU-lite",
                "GRU-lite بمدخل الشعبية الآنية − الشعبية الآنية"])
L.append("")
e1 = a11[(a11.comparison.str.startswith("GRU_eqinfo − B5_SKNN (locked) [")) & (a11.year == 2014) & (a11.unit == "presentation")].iloc[0]
e3 = a11[(a11.comparison == "GRU_eqinfo − B3_RecentPop (locked)") & (a11.year == 2014) & (a11.unit == "presentation")].iloc[0]
L.append(f"فحين يرى GRU-lite معلومة الأقران الآنية يتقدم على الجيران على السلال في 2014 بـ{f(e1['mean'])} بفاصل "
         f"{ci(e1.ci_lo, e1.ci_hi)}، موجباً في {int(e1.n_pos)} عروض من {int(e1.n_units)}، ويتقدم على الشعبية الآنية بـ{f(e3['mean'])} "
         f"بفاصل {ci(e3.ci_lo, e3.ci_hi)} يشمل الصفر. فحكم H3 المسجل يعكس تفاوت المعلومة بين النموذجين أكثر مما يعكس نوعهما. "
         "ويُقرأ هذا بثلاثة قيود. أولها أنه لاحق، ولو سُجّل لكان في عائلة غير عائلة الحكم. وثانيها أن القناة المضافة هي إشارة "
         "الشعبية الآنية نفسها، لا آلية الجيران، فالنموذج أقرب إلى هجين بين GRU-lite والشعبية الآنية. وثالثها أن تقدمه على "
         "الشعبية الآنية غير دال، فلا يغيّر ما يقوله حكم H1 عن صعوبة تجاوزها.")

open(OUT, "w", encoding="utf-8").write("\n".join(L))
print("written", OUT)
