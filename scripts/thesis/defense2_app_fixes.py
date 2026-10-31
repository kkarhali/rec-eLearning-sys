#!/usr/bin/env python3
"""Apply the thesis-side edits of the app-impact review after the second mock-defense session
(docs/defense/session2/app-impact-review.md, section 4: items ت-1 and ت-3), and the service test count after ت-1…ت-5.

ت-1: the SKNN row of table 3-11 is separated from the Markov row and carries the served template
(`src.ml.serving.TEMPLATES["B5_SKNN"]`) and the evidence the app actually shows; the Markov row keeps its template.
ت-3: the C7 evidence line quoted in UC-03 (section 4) names its scope, as the explanation panel now shows it.
ب-1 (session-2 verdict, researcher item): section 2-1 points to the saved log of the post-hoc literature search,
docs/working/literature-search-log-session2.md (decision D-127, docs/meetings/2026-10-31-decision-final-phase-b-items.md).

Each edit is (file, old, new, item): `old` must occur exactly once; an edit whose `new` is already present is skipped.

Usage:  python3 scripts/thesis/defense2_app_fixes.py [--check]
"""
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
TH = "docs/working/06-thesis/"

EDITS = [
    # ت-1: table 3-11, SKNN row separated from Markov with the served template and evidence
    (TH + "ch3-methodology.md",
     "| (4) الجيران على السلال أو ماركوف | «يتبع غالباً ما زرتَه مؤخراً» | سلة الجار الأقرب أو أكبر احتمال انتقال |\n",
     "| (4) الجيران على السلال (SKNN) | «زاره مؤخراً زملاء زاروا ما زرتَه» | أحدث مورد في سلة المتعلم الأخيرة التي قورنت بها "
     "سلال الأقران الحديثة |\n"
     "| (4) ماركوف | «يتبع غالباً ما زرتَه مؤخراً» | أكبر احتمال انتقال |\n",
     "ت-1"),
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
]


def main(check=False):
    errors = 0
    for f, old, new, item in EDITS:
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
