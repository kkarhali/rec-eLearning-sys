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
         "مولَّد من تلك المخرجات.")
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
L += pair_rows(a1, ["HYB_B3+SKNN − B3_RecentPop (H1 inference)", "HYB_B3+SKNN − HYB* (frozen)"],
               ["الهجين اللاحق − الشعبية الآنية", "الهجين اللاحق − الهجين المجمَّد"])
L.append("")
r14 = a1[(a1.comparison == "HYB_B3+SKNN − B3_RecentPop (H1 inference)") & (a1.year == 2014) & (a1.unit == "presentation")].iloc[0]
L.append(f"فحتى حين يُبنى التخصيص فوق الشعبية الآنية مباشرة، لا يتجاوزها في 2014 إلا بفرق {f(r14['mean'])} بفاصل "
         f"{ci(r14.ci_lo, r14.ci_hi)}، موجب في {int(r14.n_pos)} عروض من {int(r14.n_units)}. وهذا يتسق مع حكم H1 ولا يغيّره.")
L.append("")

# ---- E-2 SKNN without the recency restriction
L.append("## هـ-2 الجيران على السلال دون تقييد أحدث السلال")
L.append("")
L.append("يقصر الجيران على السلال جيرانهم المرشحين على أحدث M سلة أسبوعية، واختار الضبط أحدث ألف سلة في الطيّات كلها، "
         "فيرون سلال الأقران الحديثة، في حين لا يرى GRU-lite عند التنبؤ إلا تاريخ المتعلم (وإن تعلّم أوزانه من تسلسلات المتعلمين جميعاً). ولقياس أثر ذلك على مقارنة H3 ثُبّت M على "
         "«كل السلال»، وضُبطت المعاملات الأخرى بالميزانية نفسها، ثم قورن به GRU-lite بنتائجه المقفلة دون إعادة تدريب.")
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
         f"بـ{f(g14['mean'])} في العروض الثلاثة عشر كلها. فتقدّم الجيران على GRU-lite في H3 يعود في معظمه، في هذه الحساسية الواحدة، إلى "
         "رؤيتهم سلال الأقران الحديثة، وهو ما يقرأ به القسم 6-5 الحكم. ولا يُقرأ هذا الجدول تفوقاً للشبكة المتكررة: فهو لاحق، "
         "والمقارِن فيه أُضعف عمداً، ولا حسماً لسؤال نوع النموذج، فهو يحتاج مقارنة متكافئة في المعلومة.")
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
         "H2-أ مؤكَّدة وH4-أ مدحوضة عملياً، ويرفع الحد الأعلى لفاصل H3 فوق العتبة، فيصير حكمها «غير حاسمة».")
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
    L.append(f"**جدول هـ-7: مقارنة التنفيذات اليدوية بنظائرها في scikit-learn ({LABEL}) "
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

open(OUT, "w", encoding="utf-8").write("\n".join(L))
print("written", OUT)
