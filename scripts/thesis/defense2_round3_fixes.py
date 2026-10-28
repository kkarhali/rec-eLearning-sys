#!/usr/bin/env python3
"""Apply the corrections that remained after round 3 of the second mock-defense session
(docs/defense/session2/r3-*-verification.md).

Each edit is (file, old, new, item): `old` must occur exactly once; an edit whose `new` is already present is skipped.

Usage:  python3 scripts/thesis/defense2_round3_fixes.py [--check]
"""
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
TH = "docs/working/06-thesis/"
B6 = "scripts/thesis/build_ch6.py"

EDITS = [
    # 6-3 contradicted 6-8-1 on selection optimism (ع، ك)
    (B6,
     "وهذا يتسق مع تفاؤل الانتقاء في التطوير، إذ اختيرت شعبية العنقود قاعدةً بقيمتها النقطية وقُدّر الفرق من النوافذ نفسها "
     "(القسم 6-8-1).",
     "وتفاؤل الانتقاء لا يفسر إلا جزءاً صغيراً من هذا التقلص، فتقدير الإجراء بترك عرض خارجاً قريب من تقدير التطوير "
     "(القسم 6-8-1، والملحق هـ، القسم هـ-8).",
     "ع، ك"),
    # 6-8-1: the rest of the drop may be sampling variation (ع، ك)
    (B6,
     "والباقي فرق بين السنتين، ومنه صعود الشعبية الآنية من 0.5412 إلى 0.5698.",
     "والباقي قد يكون تغيّراً بين السنتين، ومنه صعود الشعبية الآنية من 0.5412 إلى 0.5698 (الجدول هـ-3)، وقد يكون تبايناً "
     "بين العروض، فالفاصل [−0.0094، +0.0372] يشمل −0.0006.",
     "ع، ك، س"),
    # the comparison in E-10 is the closest available to symmetry (ك)
    (B6,
     "وحين يرى الطرفان الإشارة نفسها، أي GRU-lite بمدخل الشعبية مقابل هجين الشعبية الآنية والجيران، يصير الفرق +0.0074",
     "وفي أقرب مقارنة متاحة إلى التماثل، يرى فيها الطرفان إشارة الشعبية الآنية، أي GRU-lite بمدخلها مقابل هجين الشعبية الآنية "
     "والجيران (وفيه يبقى الجيران مقصورين على الأسابيع الأخيرة)، يصير الفرق +0.0074",
     "ك"),
    (TH + "ch7-conclusion.md",
     "وحين رأى الطرفان الإشارة نفسها صار الفرق +0.0074 بفاصل يشمل الصفر",
     "وفي أقرب مقارنة متاحة إلى التماثل، يرى فيها الطرفان إشارة الشعبية الآنية، صار الفرق +0.0074 بفاصل يشمل الصفر",
     "ك"),
    # 3-5-4: pointer after the recorded sentence on the floor (ع)
    (TH + "ch3-methodology.md",
     "فإن خسر الهجين، فالجواب «الشخصنة لا تضيف فوق الجدول الدراسي»، وهو نتيجة رئيسية.",
     "فإن خسر الهجين، فالجواب «الشخصنة لا تضيف فوق الجدول الدراسي»، وهو نتيجة رئيسية. وبعد النتيجة تبيّن أن الأرضية تضمن "
     "مكوّناً شخصياً بالاسم، وأن مكسبه في هذه البيانات يعتمد على قصر مجمّع جيرانه على الأسابيع الأخيرة، أي على إشارة "
     "جماعية آنية (الملحق هـ، القسم هـ-7).",
     "ع"),
    # 5-6-3: bench.py sends HTTP requests (س)
    (TH + "ch5-implementation-results.md",
     "بطلبات HTTP في ثلاثة أيام (والجدول 5-6 يقيس يوماً واحداً بأداة القياس مباشرة على المحرّك، ولم يُحفظ ناتج تلك الأداة "
     "ملفاً في `results/`)،",
     "بطلبات HTTP في ثلاثة أيام غير مسخَّنة (والجدول 5-6 يقيس اليوم 75 وحده بأداة القياس، وهي ترسل طلبات HTTP أيضاً، فالفرق "
     "بين الرقمين فرق بين الأيام؛ ولم يُحفظ ناتج تلك الأداة ملفاً في `results/`)،",
     "س"),
    (TH + "ch5-implementation-results.md",
     "**جدول 5-6: زمن الاستجابة المقاس للخدمة (حاسوب بأربع أنوية؛ مولَّد من أداة القياس)**",
     "**جدول 5-6: زمن الاستجابة المقاس للخدمة (حاسوب بأربع أنوية؛ المصدر: ناتج أداة القياس في 2026-10-24، ولم يُحفظ ملفاً)**",
     "س"),
    # NFR-01 wording (س)
    (TH + "appendix-C-requirements.md",
     "ويقيس اختبار اليوم المسخَّن أفضل ثلاث محاولات بعد طلب تسخين لا كل طلب.",
     "ويأخذ اختبار اليوم المسخَّن أدنى زمن من ثلاث محاولات بعد طلب تسخين، فلا يفحص كل طلب.",
     "س"),
    # DELICATE item name (س)
    (B6, "| Determine: تحديد الغاية |", "| Determination: تحديد الغاية |", "س"),
    # protocol tie-break (س)
    ("docs/defense/human-evaluation-protocol.md",
     "يحدده الميسّر قبل الجلسة،",
     "يحدده الميسّر قبل الجلسة، وعند التعادل يُختار أصغر رقم تسجيل،",
     "س"),
    # thesis README note 10 (س)
    (TH + "README.md",
     "وبعد تصويبات الجلسة الثانية (2026-10-27) صار العدد 131 في `src/ml` و63 في الخدمة (منها فحص التباين واختبار الطلب "
     "البارد)، ويلزم تحديث الجدول 5-1 والقسمين 5-3 و5-6-1 بهما.",
     "وبعد تصويبات الجلسة الثانية (2026-10-27) صار العدد 131 في `src/ml` و63 في الخدمة (منها فحص التباين واختبار الطلب "
     "البارد)، وحُدّث بهما الجدول 5-1 والأقسام 5-3 و5-6-1 و5-9 والفصل 7.",
     "س"),
    # 2-1: the raw search results were not saved (ع)
    (TH + "ch2-background-literature.md",
     "والمفحوص هنا العنوان والمقتطف لكل نتيجة معروضة،",
     "ولم تُحفظ صفحات النتائج الخام في المستودع، وحُفظ عددها وما أُدخل منها في الجدول 2-1-أ. والمفحوص هنا العنوان والمقتطف "
     "لكل نتيجة معروضة،",
     "ع"),
]


def main(check=False):
    errors = 0
    for f, old, new, item in EDITS:
        if old == new:
            continue
        p = os.path.join(ROOT, f)
        s = open(p, encoding="utf-8").read()
        if new in s:
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
