#!/usr/bin/env python3
"""Apply the thesis-side edits of the app-impact review after the second mock-defense session
(docs/defense/session2/app-impact-review.md, section 4: items ت-1 and ت-3).

ت-1: the SKNN row of table 3-11 is separated from the Markov row and carries the served template
(`src.ml.serving.TEMPLATES["B5_SKNN"]`) and the evidence the app actually shows; the Markov row keeps its template.
ت-3: the C7 evidence line quoted in UC-03 (section 4) names its scope, as the explanation panel now shows it.

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
