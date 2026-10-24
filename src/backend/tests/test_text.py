"""نصوص عربية سليمة العدد، وحذف أرقام القرارات الداخلية من كل نص يصل إلى المستخدم (بلا بيانات)."""
import re
import unittest

from src.backend.services.labels import days_ar, fix_ar


class TestArabicText(unittest.TestCase):
    def test_days_plural(self):
        want = {0: "0 أيام", 1: "يوم واحد", 2: "يومان", 3: "3 أيام", 10: "10 أيام", 11: "11 يوماً", 57: "57 يوماً",
                100: "100 يوماً", 103: "103 أيام", 111: "111 يوماً"}
        for n, w in want.items():
            self.assertEqual(days_ar(n), w, n)

    def test_fix_after_days(self):
        self.assertEqual(fix_ar("مرتبط بالتقييم القادم بعد 57 أيام"), "مرتبط بالتقييم القادم بعد 57 يوماً")
        self.assertEqual(fix_ar("بعد 3 أيام"), "بعد 3 أيام")
        self.assertEqual(fix_ar("بعد 1 أيام"), "بعد يوم واحد")
        self.assertEqual(fix_ar("بعد 2 أيام"), "بعد يومان")
        self.assertIsNone(fix_ar(None))

    def test_strip_decision_ids(self):
        t = "اليوم 40 قبل أول قطع (70): لا مكوّن ثقيل؛ مُعاد تطبيعها (D-49 (5))، وإعداداتها من القطع 70."
        out = fix_ar(t)
        self.assertNotRegex(out, r"D-\d")
        self.assertIn("(70)", out)                       # الأقواس العادية تبقى
        self.assertNotRegex(fix_ar("الحالة الاحتياطية الرسمية (D-39-ب)."), r"D-\d")

    def test_static_ui_has_no_decision_ids(self):
        from pathlib import Path
        root = Path(__file__).resolve().parents[2] / "frontend"
        for f in list(root.glob("*.html")) + list((root / "src").rglob("*.ts")):
            txt = f.read_text(encoding="utf-8")
            if f.suffix == ".ts":                          # التعليقات مسموحة؛ النصوص لا
                txt = re.sub(r"//.*", "", txt)
                txt = re.sub(r"/\*.*?\*/", "", txt, flags=re.S)
            self.assertNotRegex(txt, r"\bD-\d+", f.name)


if __name__ == "__main__":
    unittest.main()
