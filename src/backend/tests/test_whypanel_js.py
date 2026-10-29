"""ت-3: دليل C7 في لوحة «لماذا؟» يذكر نطاقه (``scope = "similar"``) فلا يُقرأ عدّاً للفوج كله، ولا يذكر عنقوداً (D-70).

يستورد ``dist/js/components/WhyPanel.js`` المبني في node ويستدعي ``evidenceText``؛ ويُتخطّى إن غاب node أو الواجهة المبنية.
"""
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

DIST = Path(__file__).resolve().parents[2] / "frontend" / "dist" / "js"
WHY = DIST / "components" / "WhyPanel.js"


@unittest.skipUnless(shutil.which("node") and WHY.exists(), "node أو الواجهة المبنية غير متوفرة")
class TestWhyPanelJs(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        root = Path(cls.tmp.name) / "js"
        shutil.copytree(DIST, root)                      # الاستيرادات النسبية (../dom.js، ../labels.js) تبقى صحيحة
        (root / "package.json").write_text('{"type": "module"}', encoding="utf-8")
        cls.mod = (root / "components" / "WhyPanel.js").as_uri()

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def evidence_text(self, *evidence):
        code = (f"import {{ evidenceText }} from '{self.mod}';"
                f"console.log(JSON.stringify({json.dumps(list(evidence))}.map((e) => evidenceText(e))));")
        out = subprocess.run(["node", "--input-type=module", "-e", code], capture_output=True, text=True, timeout=30)
        self.assertEqual(out.returncode, 0, out.stderr)
        return json.loads(out.stdout)

    def test_count_evidence_names_its_scope(self):
        similar, plain, everyone = self.evidence_text({"type": "count", "n": 86, "window": 3, "scope": "similar"},
                                                      {"type": "count", "n": 86, "window": 3},
                                                      {"type": "count", "n": 86, "window": 3, "scope": "all"})
        self.assertEqual(similar, "استخدمه 86 متعلماً بنمط مشابه لنمطك في آخر 3 أيام.")
        self.assertIn("بنمط مشابه", similar)
        self.assertEqual(plain, "استخدمه 86 متعلماً في آخر 3 أيام.")
        self.assertNotIn("بنمط مشابه", plain)
        self.assertEqual(everyone, plain)
        for t in (similar, plain):
            self.assertNotIn("عنقود", t)
            self.assertNotIn("cluster", t)

    def test_other_evidence_unchanged(self):
        item, assess, none = self.evidence_text({"type": "item", "id_site": 546652, "activity_type": "oucontent", "days": 3, "last_day": 68},
                                                {"type": "assessment", "assessment_type": "TMA", "days_ahead": 14}, None)
        self.assertIn("#546652", item)
        self.assertIn("زرتَه في 3 أيام", item)
        self.assertEqual(assess, "TMA بعد 14 يوماً.")
        self.assertIsNone(none)


if __name__ == "__main__":
    unittest.main()
