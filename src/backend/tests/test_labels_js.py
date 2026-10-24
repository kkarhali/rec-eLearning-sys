"""صيغ العدد والأرقام السالبة في ``labels.ts`` (مبنية إلى dist/js)؛ تُتخطّى إن غاب node أو الواجهة المبنية."""
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

LABELS = Path(__file__).resolve().parents[2] / "frontend" / "dist" / "js" / "labels.js"
CASES = [
    # (دالة، عدد، المتوقع)
    ("learnersAr", 0, "0 متعلمين"), ("learnersAr", 1, "متعلم واحد"), ("learnersAr", 2, "متعلمان"), ("learnersAr", 3, "3 متعلمين"),
    ("learnersAr", 10, "10 متعلمين"), ("learnersAr", 11, "11 متعلماً"), ("learnersAr", 57, "57 متعلماً"),
    ("learnersAr", 99, "99 متعلماً"), ("learnersAr", 100, "100 متعلم"), ("learnersAr", 200, "200 متعلم"),
    ("learnersAr", 1000, "1,000 متعلم"), ("learnersAr", 101, "101 متعلماً"), ("learnersAr", 103, "103 متعلمين"),
    ("learnersAr", 1872, "1,872 متعلماً"), ("daysAr", 100, "100 يوم"), ("daysAr", 11, "11 يوماً"), ("daysAr", 2, "يومان"),
    ("itemsAr", 254, "254 مورداً"), ("itemsAr", 300, "300 مورد"), ("registrationsAr", 2283, "2,283 تسجيلاً"),
]


@unittest.skipUnless(shutil.which("node") and LABELS.exists(), "node أو الواجهة المبنية غير متوفرة")
class TestLabelsJs(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        mjs = Path(cls.tmp.name) / "labels.mjs"
        mjs.write_text(LABELS.read_text(encoding="utf-8"), encoding="utf-8")
        cls.mjs = mjs

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def run_js(self, expr: str):
        code = f"import * as L from '{self.mjs.as_uri()}'; console.log(JSON.stringify({expr}));"
        out = subprocess.run(["node", "--input-type=module", "-e", code], capture_output=True, text=True, timeout=30)
        self.assertEqual(out.returncode, 0, out.stderr)
        return json.loads(out.stdout)

    def test_plural_forms(self):
        got = self.run_js("[" + ",".join(f"L.{f}({n})" for f, n, _ in CASES) + "]")
        for (f, n, want), g in zip(CASES, got):
            self.assertEqual(g, want, f"{f}({n})")

    def test_negative_numbers_use_real_minus_and_isolates(self):
        g = self.run_js("[L.fmt(-18,0), L.range(-18,-8,0), L.signed(0.6,1), L.signed(-0.8,1), L.fmt(-0.004,2), L.score2(0.5)]")
        self.assertEqual(g[0], "⁦−18⁩")
        self.assertEqual(g[1], "⁦−18 – −8⁩")
        self.assertEqual(g[2], "⁦+0.6⁩")
        self.assertEqual(g[3], "⁦−0.8⁩")
        self.assertEqual(g[4], "0")                       # لا «−0»
        self.assertEqual(g[5], "0.50")
        for s in g:
            self.assertNotIn("-", s)


if __name__ == "__main__":
    unittest.main()
