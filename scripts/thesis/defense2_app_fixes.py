#!/usr/bin/env python3
"""Apply the thesis-side edits of the app-impact review after the second mock-defense session
(docs/defense/session2/app-impact-review.md, section 4: items ت-1 and ت-3), and the service test count after ت-1…ت-5.

ت-1: the SKNN row of table 3-11 is separated from the Markov row and carries the served template
(`src.ml.serving.TEMPLATES["B5_SKNN"]`) and the evidence the app actually shows; the Markov row keeps its template.
ت-3: the C7 evidence line quoted in UC-03 (section 4) names its scope, as the explanation panel now shows it.
ب-1 (session-2 verdict, researcher item): section 2-1 points to the saved log of the post-hoc literature search,
docs/working/literature-search-log-session2.md (decision D-127, docs/meetings/2026-10-31-decision-final-phase-b-items.md).

Session 3, between rounds 1 and 2 (docs/defense/session3/r1-*.md; decisions D-128…D-135 in
docs/meetings/2026-10-31-decision-session3-between-rounds.md), items tagged «ج3-…»:
ج3-1 (ع-1): the first-gap sentence of 2-1 is limited to what the searches retrieved and read, and names the one
unverified candidate of the re-run (log ب-4/ب-5) without citing it.
ج3-2 (ع-2): the SKNN and Markov rows of table 3-11 state the evidence the code computes (src/ml/serving.py
`_last_basket`/`_evidence`, src/backend/services/explanation.py), the V-SKNN query of the frozen folds, and that the
SKNN template was revised after analysis هـ-7.
ج3-3 (ك-1): 5-7-3 quotes the corrected sign counts of the nominal-grid row of table هـ-1 (exact zeros).
ج3-5 (ك-10): 7-3 no longer states that the H4-ب effect is larger in the low-history quarter as a finding.
ج3-6 (ك-12): 3-5-12 states that the tag freeze-03 is local only.
ج3-8 (س، م-س-1): NFR-02 carries the criterion of the design document and the status «not measured».
Numbers in these edits are checked against their sources by verify_sources() before anything is written.

Each edit is (file, old, new, item): `old` must occur exactly once; an edit whose `new` is already present is skipped.

Usage:  python3 scripts/thesis/defense2_app_fixes.py [--check]
"""
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
TH = "docs/working/06-thesis/"

def obsolete(reason, edit):
    """An edit whose output was later replaced by another exact-once edit: reported as obsolete and skipped (as in
    defense2_round3_fixes.py), so that --check stays meaningful and the old text is never regenerated."""
    return (*edit, reason)


EDITS = [
    # ت-1: table 3-11, SKNN row separated from Markov with the served template and evidence
    obsolete("superseded by ج3-2 below (session 3: the SKNN and Markov evidence cells rewritten to match the code)",
    (TH + "ch3-methodology.md",
     "| (4) الجيران على السلال أو ماركوف | «يتبع غالباً ما زرتَه مؤخراً» | سلة الجار الأقرب أو أكبر احتمال انتقال |\n",
     "| (4) الجيران على السلال (SKNN) | «زاره مؤخراً زملاء زاروا ما زرتَه» | أحدث مورد في سلة المتعلم الأخيرة التي قورنت بها "
     "سلال الأقران الحديثة |\n"
     "| (4) ماركوف | «يتبع غالباً ما زرتَه مؤخراً» | أكبر احتمال انتقال |\n",
     "ت-1")),
    # ت-3: UC-03 quotes the C7 evidence line, which now names its scope (similar learners), as WhyPanel shows it
    (TH + "ch4-analysis-design.md",
     "(مثل: «استخدمه 70 متعلماً في آخر 3 أيام»،",
     "(مثل: «استخدمه 70 متعلماً بنمط مشابه لنمطك في آخر 3 أيام»،",
     "ت-3"),
    # ت-1…ت-5 added 10 service tests (63 -> 73; run 2026-10-29: `discover -s src/backend/tests -t .` Ran 73, OK).
    # The thesis states the current count as a claim about the delivered system (precedent: thesis README note 10),
    # so it is updated; decision in docs/meetings/2026-10-29-decision-post-session2-release.md. ML stays 131.
    (TH + "ch5-implementation-results.md",
     "قياس الأداء، و63 اختباراً (تشغيل 2026-10-27)",
     "قياس الأداء، و73 اختباراً (تشغيل 2026-10-29)",
     "ت-5، عدد الاختبارات"),
    (TH + "ch5-implementation-results.md",
     "ويتحقق 63 اختباراً من الخدمة (تشغيل 2026-10-27)",
     "ويتحقق 73 اختباراً من الخدمة (تشغيل 2026-10-29)",
     "ت-5، عدد الاختبارات"),
    (TH + "ch5-implementation-results.md",
     "وخدمة بثلاثة وستين اختباراً",
     "وخدمة بثلاثة وسبعين اختباراً",
     "ت-5، عدد الاختبارات"),
    (TH + "ch7-conclusion.md",
     "باختبار آلي (63 اختباراً)",
     "باختبار آلي (73 اختباراً)",
     "ت-5، عدد الاختبارات"),
    ("docs/working/06-thesis/README.md",
     "وحُدّث بهما الجدول 5-1 والأقسام 5-3 و5-6-1 و5-9 والفصل 7.",
     "وحُدّث بهما الجدول 5-1 والأقسام 5-3 و5-6-1 و5-9 والفصل 7. وبعد بنود أثر الجلسة الثانية على التطبيق (ت-1 إلى ت-5) "
     "صار عدد الخدمة 73 (تشغيل 2026-10-29)، وحُدّث به جدول بنية الشيفرة (5-2) والقسمان 5-6-1 و5-9 والفصل 7 بنص "
     "`scripts/thesis/defense2_app_fixes.py`، ويبقى عدد خط التجارب 131.",
     "ت-5، عدد الاختبارات"),
    # ب-1: pointer from 2-1 to the saved search log. The sentence that the raw result pages were not saved stays as is
    # (they were not, and the log says so); the log adds a dated re-run of the same strings, labelled as such (D-127).
    (TH + "ch2-background-literature.md",
     "ولم تُحفظ صفحات النتائج الخام في المستودع، وحُفظ عددها وما أُدخل منها في الجدول 2-1-أ.",
     "ولم تُحفظ صفحات النتائج الخام في المستودع، وحُفظ عددها وما أُدخل منها في الجدول 2-1-أ. ويحفظ المستودع سجل هذا "
     "البحث في `docs/working/literature-search-log-session2.md`: السلاسل وتاريخها وأعدادها وقرار كل سلسلة كما سُجّل، "
     "ومعه إعادة تشغيل للسلاسل نفسها في 2026-10-31 بقرار لكل نتيجة، موسومة بأنها إعادة لاحقة قد تختلف نتائجها، "
     "وليست الصفحات الأصلية.",
     "ب-1، سجل البحث اللاحق"),
    # ---------------- session 3, between rounds 1 and 2 ----------------
    # ج3-1 (د. العمر، المشكلة 1، س-ع-1): the first-gap sentence held only for what the searches retrieved and read; the
    # re-run of 2026-10-31 surfaced one education candidate (KU Leuven, UMAP '23; log ب-4 item 1, ب-5) that was not read.
    # Not cited (unverified venue and text, D-127 keeps the inclusion decision for the student and the real supervisor).
    (TH + "ch2-background-literature.md",
     "في الفجوة الأولى، لم يظهر عمل في التعليم يقارن الإشارة الضمنية الموزونة بالثنائية داخل النموذج نفسه.",
     "في الفجوة الأولى، لم يظهر في نتائج البحث الأصلي، بعناوينها ومقتطفاتها، عمل في التعليم يقارن الإشارة الضمنية "
     "الموزونة بالثنائية داخل النموذج نفسه. لكن إعادة التشغيل اللاحقة كشفت مرشحاً واحداً قد يمس هذه الجملة: عملاً في "
     "توصية المقررات المفتوحة يضيف إلى BPR زمن انسحاب يقدّره نموذج بقاء، ويقارنه بـBPR الذي يميز المرئي من غير المرئي "
     "وحده، بحسب مقتطفه. ولم يُقرأ نصه ولم يُتحقق من وعائه، فلا يُستشهد به هنا، وهو مسجل مرشحاً في السجل (القسمان ب-4 "
     "وب-5) حتى يقرأه الطالب والمشرف. فالجملة تصح لما استرجعه البحث وفُحص منه، ولا تمتد إلى ما لم يُقرأ.",
     "ج3-1، تقييد جملة الفجوة الأولى"),
    # ج3-2 (د. العمر، المشكلة 2، س-ع-3): table 3-11 against the code. Evidence of both rows = resources of the learner's
    # basket of the last active day <= day (serving._last_basket: last_days_query(view, 1, "binary"); explanation.py
    # shows one of them with its visit days and last day). The frozen SKNN query is the last 7 active days (V-SKNN, L = 7)
    # in 7 of the 27 folds of results/dev2013/hybrid_frozen.json["component_configs_by_fold"] (checked below).
    (TH + "ch3-methodology.md",
     "| (4) الجيران على السلال (SKNN) | «زاره مؤخراً زملاء زاروا ما زرتَه» | أحدث مورد في سلة المتعلم الأخيرة التي قورنت بها "
     "سلال الأقران الحديثة |\n"
     "| (4) ماركوف | «يتبع غالباً ما زرتَه مؤخراً» | أكبر احتمال انتقال |\n",
     "| (4) الجيران على السلال (SKNN) | «زاره مؤخراً زملاء زاروا ما زرتَه» | موارد سلة آخر يوم نشط للمتعلم، وهي مجموعة "
     "غير مرتبة (القسم 3-3-1)، ويُعرض منها مورد واحد بعدد أيام زيارته وآخرها. وهذه السلة استعلام الجيران في الطيّات التي "
     "ضُبط فيها L = 1؛ وفي 7 طيّات من 27 في الإعداد المجمَّد الاستعلام آخر سبعة أيام نشطة (V-SKNN)، فالدليل جزء منه |\n"
     "| (4) ماركوف | «يتبع غالباً ما زرتَه مؤخراً» | الدليل نفسه المعروض للجيران، أي موارد سلة آخر يوم نشط للمتعلم، لا احتمال "
     "الانتقال (وماركوف ليس في التركيبة المجمَّدة) |\n",
     "ج3-2، الجدول 3-11 مطابقاً للشيفرة"),
    (TH + "ch3-methodology.md",
     "ولا يُقيَّم التفسير بدراسة مستخدمين، فلا يُدّعى أثره في الثقة أو التعلم.",
     "وقالب الجيران في الجدول اختير بعد النتائج: كان حتى الجلسة الثانية من المناقشة التجريبية قالب ماركوف نفسه («يتبع "
     "غالباً ما زرتَه مؤخراً»)، ثم عُدّل بعد التحليل اللاحق في القسم هـ-7 من الملحق هـ ليصف إشارة الأقران الآنية التي يقرؤها "
     "ذلك التحليل، ولا يمس تعديله أي رقم تقييم. ولا يُقيَّم التفسير بدراسة مستخدمين، فلا يُدّعى أثره في الثقة أو التعلم.",
     "ج3-2، الجدول 3-11: القالب اختير بعد هـ-7"),
    # ج3-3 (د. الكنج، المشكلة 1، س-ك-1): nominal-grid row of table هـ-1 recomputed with exact zeros
    # (results/posthoc/a4_1_recentpop_sknn.csv after `a4_1_recentpop_sknn.py --from-csv`: 2013, presentation level,
    # n_pos 6, n_zero 2, n_neg 1, p 0.0625; checked below). Mean and interval unchanged.
    (TH + "ch5-implementation-results.md",
     "بحد أدنى للفاصل +0.0009 وموجباً في ثمانية عروض من تسعة، فكانوا سيجتازون قاعدة القبول",
     "بحد أدنى للفاصل +0.0009، وموجباً في ستة عروض من تسعة وصفراً في عرضين انحلّ فيهما الهجين إلى الشعبية الآنية، "
     "فكانوا سيجتازون قاعدة القبول",
     "ج3-3، أصفار الجدول هـ-1"),
    # ج3-5 (د. الكنج، المشكلة 10، س-ك-7): the difference between the two quarters was not estimated in the thesis
    (TH + "ch7-conclusion.md",
     "وجاء اتجاه H4-ب الاستكشافي على 2014 موجباً في الربعين، وأكبر لدى الأقل تاريخاً، فهو اتجاه يستحق اختباراً تأكيدياً "
     "لاحقاً، لا جواب.",
     "وجاء اتجاه H4-ب الاستكشافي على 2014 موجباً في الربعين، وبدا أكبر لدى الأقل تاريخاً، لكن الفرق بين الربعين لم "
     "يُقدَّر ولم يُختبر، فهو قراءة وصفية تستحق اختباراً تأكيدياً لاحقاً، لا جواب.",
     "ج3-5، H4-ب وصفية"),
    # ج3-6 (د. الكنج، المشكلة 12، س-ك-8): the tag is local (push of tags refused, 403); the frozen commit itself is in
    # the pushed branch history (`git branch -r --contains eb34d6a` → origin/kk_auto_/amazing-planck-wzsemh)
    (TH + "ch3-methodology.md",
     "وهذا انحراف عن الإجراء المسجل يعلنه القيد 25 (الفصل السادس، القسم 6-9).",
     "وهذا انحراف عن الإجراء المسجل يعلنه القيد 25 (الفصل السادس، القسم 6-9). ووسم نسخة الشيفرة `freeze-03` محلي في "
     "مستودع العمل وحده، لأن بيئة العمل رفضت دفع الوسوم إلى المستودع البعيد (خطأ 403). فلا يحمل التسجيل المسبق طابعاً "
     "زمنياً خارجياً إلا تاريخ الإيداعات المدفوعة إلى ذلك المستودع، ومنها إيداع التجميد نفسه، وسجل الوصول ملف متتبَّع في "
     "المستودع نفسه. فالتحقق من أن التجميد سبق قراءة 2014 يقوم على هذا التاريخ، لا على شاهد مستقل.",
     "ج3-6، الوسم محلي"),
    # ج3-8 (د. أبوطراب، م-س-1): «في حدود ثوانٍ» is not verifiable; the design document (docs/working/03-analysis-design.md,
    # NFR-02) states 15 s and 1.5 GB RSS (checked below). No boot or memory measurement is saved: status «planned».
    (TH + "appendix-C-requirements.md",
     "| NFR-02 | الأداء | إقلاع في حدود ثوانٍ، وذاكرة تشغيل لا تتجاوز 1.5 GB | ينبغي | آلة التشغيل | جزئي (الذاكرة لم تُلخَّص آلياً) |",
     "| NFR-02 | الأداء | إقلاع الخادم دون تسخين في 15 ثانية على الأكثر، وذاكرة تشغيل (RSS) لا تتجاوز 1.5 GB، وهما حدّا وثيقة "
     "التحليل والتصميم | ينبغي | آلة التشغيل | مخطط: لم يُقَس زمن الإقلاع ولا ذروة الذاكرة، ولا ملف قياس لهما في "
     "`results/`، فالمتطلب غير متحقَّق منه |",
     "ج3-8، NFR-02"),
    (TH + "appendix-C-requirements.md",
     "| NFR-02 | آلة التشغيل | src/backend/app.py | قياس الذاكرة (مخطط) |",
     "| NFR-02 | آلة التشغيل | src/backend/app.py | قياس زمن الإقلاع وذروة الذاكرة (مخطط، لم يُجرَ) |",
     "ج3-8، NFR-02"),
]


def verify_sources():
    """Check the numbers that the ج3 edits quote against their source files; return the number of mismatches."""
    import json
    import pandas as pd
    bad = 0
    cfg = json.load(open(os.path.join(ROOT, "results", "dev2013", "hybrid_frozen.json"), encoding="utf-8"))
    folds = cfg["component_configs_by_fold"]
    sk = [str(v.get("B5_SKNN", "")) for v in folds.values()]
    n_v7 = sum("variant=vsknn" in x and "L=7" in x for x in sk)
    if (n_v7, len(folds)) != (7, 27):
        print(f"FAIL [ج3-2] hybrid_frozen.json: V-SKNN (L = 7) in {n_v7} of {len(folds)} folds, edit says 7 of 27")
        bad += 1
    a = pd.read_csv(os.path.join(ROOT, "results", "posthoc", "a4_1_recentpop_sknn.csv"))
    r = a[(a.comparison == "HYB_B3+SKNN nominal grid − B3_RecentPop") & (a.year == 2013) & (a.unit == "presentation")]
    if r.empty or "n_zero" not in a.columns or tuple(int(r.iloc[0][k]) for k in ("n_pos", "n_zero", "n_units")) != (6, 2, 9):
        print("FAIL [ج3-3] a4_1_recentpop_sknn.csv: 2013 nominal row is not 6 positive, 2 zero of 9 "
              "(run scripts/posthoc/a4_1_recentpop_sknn.py --from-csv first)")
        bad += 1
    d03 = open(os.path.join(ROOT, "docs", "working", "03-analysis-design.md"), encoding="utf-8").read()
    if "| NFR-02 | الأداء | إقلاع حتى 15 ثانية، وذاكرة RSS حتى 1.5 GB" not in d03:
        print("FAIL [ج3-8] 03-analysis-design.md: NFR-02 no longer states 15 s and 1.5 GB")
        bad += 1
    return bad


def main(check=False):
    errors = verify_sources()
    if errors:
        print(f"errors={errors} (source check failed; nothing written)")
        return 1
    for e in EDITS:
        f, old, new, item = e[:4]
        if len(e) == 5:
            print(f"obsolete [{item}] {f}: {e[4]}")
            continue
        if old == new:
            continue
        p = os.path.join(ROOT, f)
        s = open(p, encoding="utf-8").read()
        if new in s:
            print(f"skip [{item}] {f}: already applied")
            continue
        n = s.count(old)
        if n != 1:
            print(f"FAIL [{item}] {f}: found {n}: {old[:70]}")
            errors += 1
            continue
        if not check:
            open(p, "w", encoding="utf-8").write(s.replace(old, new))
        print(f"ok   [{item}] {f}")
    print(f"errors={errors}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main("--check" in sys.argv))
