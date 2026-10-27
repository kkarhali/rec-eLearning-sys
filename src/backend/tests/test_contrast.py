"""NFR-22: فحص آلي لنسب التباين (WCAG 2.2: 1.4.3 و1.4.11) لكل أزواج الألوان المستعملة في الواجهة.

يقرأ رموز الألوان من ``src/frontend/styles/tokens.css`` ويحسب نسبة التباين بصيغة WCAG لكل زوج مستعمل في ``base.css``
و``components.css``. الحد 4.5:1 للنص العادي، و3:1 للنص الكبير ولحدود عناصر التحكم والأشكال اللازمة للفهم. ويفشل الاختبار
أيضاً إن ظهر رمز لون أو لون حرفي في الأنماط دون أن يُصنَّف هنا (زوجاً مفحوصاً أو استثناءً مسبَّباً)، فلا يدخل لون جديد بلا فحص.
ويكمّله فحص النص المرسوم فعلاً في الاختبار الطرفي (``src/backend/e2e/live-screenshots.js``).

تشغيله وحده مع جدول النسب: ``python3 -m src.backend.tests.test_contrast``
"""
import re
import unittest
from pathlib import Path

STYLES = Path(__file__).resolve().parents[2] / "frontend" / "styles"
LABELS_TS = STYLES.parent / "src" / "labels.ts"
TEXT, LARGE, UI = 4.5, 3.0, 3.0

# (اللون الأمامي، الخلفية، الحد، الموضع). الرمز يبدأ بـ--، واللون الحرفي بـ#، والخلفية الشفافة «rgba(...)/خلفيتها».
PAIRS = [
    # النص الأساسي والثانوي على كل خلفيات الصفحة
    ("--color-fg", "--color-bg", TEXT, "نص الصفحة"),
    ("--color-fg", "--color-card", TEXT, "نص البطاقات والجداول"),
    ("--color-fg", "#F1F5F9", TEXT, "شريط التحكم ورأس الجدول والرقاقة"),
    ("--color-fg", "#F0FDFA", TEXT, "شريط السياق وتظليل الصف وبطاقة العنقود المختارة والدليل"),
    ("--color-fg", "--color-primary-soft", TEXT, "رتبة التوصية"),
    ("--color-fg", "--color-accent-soft", TEXT, "الصف المختار في جدول المدرّس"),
    ("--color-muted-fg", "--color-bg", TEXT, "النص الثانوي على الصفحة"),
    ("--color-muted-fg", "--color-card", TEXT, "النص الثانوي في البطاقات"),
    ("--color-muted-fg", "#F1F5F9", TEXT, "تلميحات شريط التحكم ومحاور الرسوم"),
    ("--color-muted-fg", "#F0FDFA", TEXT, "النص الثانوي في شريط السياق"),
    # اللون الأساسي
    ("--color-primary", "--color-card", TEXT, "الروابط والأزرار الثانوية وأزرار التصفية"),
    ("--color-primary", "--color-bg", TEXT, "الروابط على الصفحة"),
    ("--color-primary", "#F1F5F9", TEXT, "الروابط داخل شريط التحكم"),
    ("--color-on-primary", "--color-primary", TEXT, "الزر الأساسي وشارة اليوم وزر التصفية النشط"),
    ("--color-on-primary", "--color-primary-dark", TEXT, "الرأس ورابط التخطي والإشعار وحالة hover للزر الأساسي"),
    ("#FFFFFF", "rgba(255,255,255,.14)/--color-primary-dark", TEXT, "رابط التنقل عند المرور"),
    ("--color-primary-dark", "#FFFFFF", TEXT, "رابط الصفحة الحالية في التنقل"),
    ("--color-primary-dark", "--color-primary-soft", TEXT, "الشارات وحالة hover للزر الثانوي"),
    # الكهرماني والخطر
    ("--color-accent-text", "--color-accent-soft", TEXT, "شارة إعادة التشغيل والإشعارات"),
    ("--color-accent-text", "--color-card", TEXT, "الإشعار دون صندوق"),
    ("--color-accent-text", "--color-bg", TEXT, "الإشعار على الصفحة"),
    ("#FFFFFF", "--color-accent", TEXT, "أرقام الخطوات في الصفحة الرئيسية"),
    ("#7F1D1D", "--color-danger-soft", TEXT, "شريط «للمدرّس فقط» وصندوق الخطأ"),
    ("#FFFFFF", "#7F1D1D", TEXT, "إشعار الخطأ"),
    ("--color-danger", "--color-card", TEXT, "تسمية العتبة في المدرج"),
    ("--color-danger", "#F1F5F9", TEXT, "تسمية العتبة فوق خلفية الرسم"),
    # حدود عناصر التحكم والأشكال اللازمة للفهم (1.4.11)
    ("--color-border-strong", "--color-card", UI, "حدود الحقول والبطاقات التفاعلية"),
    ("--color-border-strong", "#F1F5F9", UI, "حدود الحقول في شريط التحكم ومسار شريط اليوم"),
    ("--color-border-strong", "--color-bg", UI, "حدود الحالة الفارغة"),
    ("--color-primary", "--color-card", UI, "حدود الأزرار وبطاقة التوصية النشطة"),
    ("--color-primary", "#F1F5F9", UI, "علامات نقاط القطع في شريط اليوم"),
    ("--color-accent", "--color-card", UI, "حد الدرج وحد شارة التنبيه"),
    ("--color-accent", "#F1F5F9", UI, "علامات مواعيد التقييم في شريط اليوم"),
    ("--color-danger", "--color-danger-soft", UI, "حد صندوق الخطأ والشريط"),
    ("--color-danger", "#F1F5F9", UI, "خط العتبة في المدرج"),
    ("#78350F", "#F1F5F9", UI, "إطار أعمدة المدرج فوق العتبة"),
    ("#78350F", "--color-card", UI, "إطار شريط الدرجة فوق العتبة"),
    ("#0F766E", "#F1F5F9", UI, "إطار أعمدة العوامل السالبة"),
    ("--color-primary-dark", "--color-primary-soft", UI, "علامة الوسيط في أشرطة الملامح"),
    ("--color-accent-text", "--color-accent-soft", UI, "مؤشر الصف المختار"),
    ("--color-focus", "--color-card", UI, "حلقة التركيز على البطاقات"),
    ("--color-focus", "--color-bg", UI, "حلقة التركيز على الصفحة"),
    ("--color-focus", "#F1F5F9", UI, "حلقة التركيز في شريط التحكم"),
    ("#FFFFFF", "--color-primary-dark", UI, "حلقة التركيز وحدود روابط التنقل في الرأس"),
    ("#FFFFFF", "#7F1D1D", UI, "حد زر الإغلاق في إشعار الخطأ"),
]

# ألوان مستعملة لا يشملها حد التباين، مع السبب. كل لون منها يحتاج سبباً مكتوباً.
EXEMPT = {
    "--color-border": "فواصل زخرفية بين الصفوف والبطاقات؛ حدود العناصر التفاعلية بـ--color-border-strong",
    "--color-primary-soft": "خلفية فقط؛ نصها مفحوص أعلاه",
    "--color-accent-soft": "خلفية فقط؛ نصها مفحوص أعلاه",
    "--color-danger-soft": "خلفية فقط؛ نصها مفحوص أعلاه",
    "--color-bg": "خلفية فقط",
    "--color-card": "خلفية فقط",
    "#F1F5F9": "خلفية فقط (شريط التحكم ورأس الجدول وخلفية الرسوم والمسارات)",
    "#F0FDFA": "خلفية فقط",
    "#FFFFFF": "خلفية الحقول والبطاقات ونص على الخلفيات الداكنة (مفحوص أعلاه)",
    "#7F1D1D": "نص الخطأ وخلفية إشعار الخطأ (مفحوصان أعلاه)",
    "#E2E8F0": "عمود ثانوي في الرسم ووميض التحميل؛ القيمة مكتوبة في الجدول البديل",
    "#CBD5E1": "تعبئة الأعمدة؛ الشكل يحدده إطار --color-border-strong المفحوص",
    "#FCD34D": "تعبئة ما فوق العتبة؛ يميّزه الإطار الداكن #78350F المفحوص، والقيمة مكتوبة نصاً",
    "#99F6E4": "تعبئة العوامل السالبة ومستوى في خريطة النشاط؛ يحدد الشكل إطار مفحوص، والقيم في الجدول البديل",
    "#14B8A6": "مستوى في خريطة النشاط؛ للخلايا إطار --color-border-strong، والقيم في الجدول البديل",
    "#0F766E": "مستوى في خريطة النشاط وإطار العوامل السالبة (مفحوص أعلاه)",
    "#134E4A": "إطار أعلى مستوى في خريطة النشاط (مساوٍ لـ--color-fg)",
    "#94A3B8": "تعبئة شريط الدرجة في الجدول؛ الدرجة نفسها مكتوبة رقماً بجانبه",
    "#78350F": "إطار ما فوق العتبة (مفحوص أعلاه)",
    "#FFF": "نص وحلقة تركيز على الخلفيات الداكنة (مفحوص أعلاه بصيغة #FFFFFF)",
}


def tokens() -> dict:
    css = (STYLES / "tokens.css").read_text(encoding="utf-8")
    return {m.group(1): m.group(2).upper() for m in re.finditer(r"(--color-[\w-]+):\s*(#[0-9A-Fa-f]{6})\b", css)}


def rgb(hexcode: str):
    h = hexcode.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def resolve(c: str, tok: dict):
    """(r, g, b) لرمز أو لون حرفي أو rgba فوق خلفية («rgba(r,g,b,a)/الخلفية»)."""
    if c.startswith("rgba("):
        over, under = c.split("/", 1)
        r, g, b, a = (float(x) for x in over[5:-1].split(","))
        u = resolve(under, tok)
        return tuple(round(a * x + (1 - a) * y) for x, y in zip((r, g, b), u))
    return rgb(tok[c] if c.startswith("--") else c)


def luminance(c) -> float:
    def ch(v):
        v /= 255
        return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4
    r, g, b = (ch(v) for v in c)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def ratio(a, b) -> float:
    la, lb = sorted((luminance(a), luminance(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def used_colors() -> set:
    """كل رمز لون وكل لون حرفي سداسي أو ثلاثي في أنماط الواجهة (عدا تعريفات tokens.css)."""
    out = set()
    for f in ("base.css", "components.css"):
        css = (STYLES / f).read_text(encoding="utf-8")
        out |= set(re.findall(r"var\((--color-[\w-]+)\)", css))
        out |= {c.upper() for c in re.findall(r"#[0-9A-Fa-f]{6}\b|#[0-9A-Fa-f]{3}\b", css)}
    return out


def report() -> list:
    tok = tokens()
    rows = []
    for fg, bg, need, where in PAIRS:
        rows.append((fg, bg, ratio(resolve(fg, tok), resolve(bg, tok)), need, where))
    return rows


class TestContrast(unittest.TestCase):
    def test_tokens_parsed(self):
        tok = tokens()
        for k in ("--color-fg", "--color-primary", "--color-border-strong", "--color-focus"):
            self.assertIn(k, tok)

    def test_wcag_formula(self):
        self.assertAlmostEqual(ratio(rgb("#000000"), rgb("#FFFFFF")), 21.0, places=6)
        self.assertAlmostEqual(ratio(rgb("#FFFFFF"), rgb("#FFFFFF")), 1.0, places=6)
        self.assertAlmostEqual(ratio(rgb("#767676"), rgb("#FFFFFF")), 4.54, places=2)   # الرمادي المرجعي عند حد AA

    def test_all_pairs_meet_aa(self):
        bad = [f"{fg} على {bg}: {r:.2f}:1 < {need}:1 ({where})" for fg, bg, r, need, where in report() if r < need]
        self.assertFalse(bad, "\n".join(bad))

    def test_series_palette_against_card_and_chart(self):
        """ألوان مكوّنات الهجين والعناقيد في labels.ts (أشكال لازمة للفهم، 1.4.11) على البطاقة وخلفية الرسم."""
        ts = LABELS_TS.read_text(encoding="utf-8")
        cols = sorted({c.upper() for c in re.findall(r"'(#[0-9A-Fa-f]{6})'", ts)})
        self.assertGreaterEqual(len(cols), 6)
        bad = [f"{c} على {bg}: {ratio(rgb(c), rgb(bg)):.2f}:1" for c in cols for bg in ("#FFFFFF", "#F1F5F9")
               if ratio(rgb(c), rgb(bg)) < UI]
        self.assertFalse(bad, "\n".join(bad))

    def test_every_used_color_is_classified(self):
        tok = tokens()
        named = {c for fg, bg, _, _ in PAIRS for c in (fg, bg.split("/")[-1])}
        named |= {c.upper() for c in named if c.startswith("#")}
        missing = sorted(c for c in used_colors() if c not in named and c not in EXEMPT)
        self.assertFalse(missing, f"ألوان مستعملة بلا زوج مفحوص ولا استثناء مسبَّب: {missing}")
        undefined = sorted(c for c in used_colors() if c.startswith("--") and c not in tok)
        self.assertFalse(undefined, f"رموز مستعملة غير معرّفة في tokens.css: {undefined}")


if __name__ == "__main__":
    for fg, bg, r, need, where in report():
        print(f"{'OK ' if r >= need else 'FAIL'} {r:5.2f}:1 (≥{need}) {fg} / {bg} · {where}")
    unittest.main()
