"""نصوص عربية سليمة العدد، وحذف أرقام القرارات الداخلية من كل نص يصل إلى المستخدم (بلا بيانات)."""
import re
import unittest
from pathlib import Path

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

    def test_risk_label_is_relative_everywhere(self):
        """NFR-18: كل تسمية ظاهرة لدرجة الخطر في الواجهة نسبية: «درجة الخطر النسبية» (ومنها عنوان عمود الجدول)
        أو «درجة خطر نسبية»؛ ولا تبقى «درجة الخطر» وحدها في نص يصل إلى المستخدم."""
        from pathlib import Path
        root = Path(__file__).resolve().parents[2] / "frontend"
        bad = []
        for f in list(root.glob("*.html")) + list((root / "src").rglob("*.ts")):
            txt = f.read_text(encoding="utf-8")
            if f.suffix == ".ts":
                txt = re.sub(r"//.*", "", txt)
                txt = re.sub(r"/\*.*?\*/", "", txt, flags=re.S)
            bad += [f"{f.name}: …{txt[max(0, m.start() - 20):m.end() + 12]}…" for m in re.finditer(r"درجة الخطر(?! النسبية)", txt)]
        self.assertFalse(bad, "\n".join(bad))
        ins = (root / "src" / "instructor.ts").read_text(encoding="utf-8")
        self.assertIn("header: 'درجة الخطر النسبية'", ins)


class TestClusterQualityNull(unittest.TestCase):
    """D-71: ARI الغائب null لا 0.0، ولا يُستشهد به في سبب عدم الاستقرار."""

    def test_ari_missing_is_none(self):
        from src.backend.services.instructor import InstructorService
        from src.backend.repository import Repository
        from src.backend.settings import Settings
        svc = InstructorService(Repository(Settings()), None, Settings())
        self.assertIsNone(svc._ari("ZZZ_2099J"))
        self.assertIsNone(svc._ari("BBB_2014J"))

    def test_unstable_reason_without_ari(self):
        from types import SimpleNamespace
        from src.backend.services.instructor import InstructorService
        cm = SimpleNamespace(quality=(0.2, 2.0, None), k=3)
        r = InstructorService._unstable_reason(cm)
        self.assertNotIn("0.00", r)
        self.assertNotIn("ضعيف", r)
        self.assertIn("غير متاح", r)
        self.assertIn("ثبات البذور ضعيف", InstructorService._unstable_reason(SimpleNamespace(quality=(0.2, 2.0, 0.5), k=3)))

    def test_schema_serialises_null_ari(self):
        import json
        from src.backend.schemas import ClusterQuality
        self.assertIsNone(json.loads(ClusterQuality(silhouette=0.1, dbi=1.0, ari=None).model_dump_json())["ari"])



REPO = Path(__file__).resolve().parents[3]
FRONT = REPO / "src" / "frontend"
OLD_SKNN = re.compile(r"يتبع (?:غالباً )?ما زرت[َُ]?ه مؤخراً")      # القالب القديم وصيغه المقتبسة (بلا «غالباً» أو بضمة)


def _frozen():
    import json
    return json.loads((REPO / "results" / "dev2013" / "hybrid_frozen.json").read_text(encoding="utf-8"))


class TestServedTemplatesAfterSession2(unittest.TestCase):
    """تصويبات الجلسة الثانية على التطبيق (docs/defense/session2/app-impact-review.md، ت-1 وت-2 وت-4)."""

    def test_sknn_template_names_recent_peers(self):
        """ت-1: قالب SKNN يصف سلال الأقران الحديثة لا تتابعاً؛ وقالب ماركوف بلا تغيير؛ ولا «مخصص لك» ولا «شخصي» في أي قالب."""
        from src.ml import serving
        t = serving.TEMPLATES["B5_SKNN"]
        self.assertEqual(t, "زاره مؤخراً زملاء زاروا ما زرتَه")
        self.assertIn("زملاء", t)
        self.assertIn("مؤخراً", t)
        self.assertNotIn("يتبع", t)
        self.assertEqual(serving.TEMPLATES["B6_Markov"], "يتبع غالباً ما زرتَه مؤخراً")
        for m, tpl in serving.TEMPLATES.items():
            self.assertNotIn("مخصص لك", tpl, m)
            self.assertNotIn("شخصي", tpl, m)

    def test_docs_quote_served_templates(self):
        """ت-1: قالب كل مكوّن مجمَّد يظهر حرفياً في الجدول 3-11 وفي دليل المستخدم 05، ولا يظهر القالب القديم إلا في سطر ماركوف
        في ch3 و03 و05. والوثيقة 02 مستثناة بالاسم: وثيقة تصميم تاريخية سابقة للتجميد (ر-6، قياساً على D-112)."""
        from src.ml import serving
        work = REPO / "docs" / "working"
        ch3 = (work / "06-thesis" / "ch3-methodology.md").read_text(encoding="utf-8")
        start = ch3.index("**جدول 3-11")
        table = ch3[start:ch3.index("\n\n", ch3.index("\n|", start))]
        guide = (work / "05-user-guide.md").read_text(encoding="utf-8")
        for m in _frozen()["components"]:
            self.assertIn(f"«{serving.TEMPLATES[m]}»", table, m)
            self.assertIn(f"«{serving.TEMPLATES[m]}»", guide, m)
        docs = {"ch3": work / "06-thesis" / "ch3-methodology.md", "03": work / "03-analysis-design.md", "05": work / "05-user-guide.md"}
        self.assertNotIn("02", docs)
        for name, f in docs.items():
            for line in f.read_text(encoding="utf-8").splitlines():
                if OLD_SKNN.search(line):
                    self.assertTrue("Markov" in line or "ماركوف" in line, f"{name}: {line[:120]}")

    def _about(self):
        return (FRONT / "about.html").read_text(encoding="utf-8")

    def test_about_describes_frozen_composition(self):
        """ت-2: فقرة «المنهجية باختصار» تسمّي مكوّني التركيبة المجمَّدة وحدهما، وقسم القيود يقول «غير حاسم» حرفياً (D-98)."""
        from src.backend.services.labels import COMPONENT_LABELS
        html = self._about()
        i = html.index("المنهجية باختصار")
        para = html[i:html.index("</section>", i)]
        for m in _frozen()["components"]:
            label = re.sub(r"\s*\(\d+\)$", "", COMPONENT_LABELS[m])
            self.assertIn(label, para, m)
        for other in ("WRMF", "Recent-Pop", "قرب التقييم", "GRU"):
            self.assertNotIn(other, para)
        self.assertIn("غير حاسم", html)
        self.assertNotIn("سلبية", html)

    def test_about_has_no_evaluation_numbers(self):
        """ت-2 (D-67/D-71): لا عدد عشري ولا نسبة مئوية ولا اسم مقياس تقييم في «عن النظام». رقم إصدار الترخيص ليس رقم تقييم."""
        txt = self._about().replace("CC BY 4.0", "CC BY")
        self.assertNotRegex(txt, r"\d\s*[.,٫]\s*\d")
        self.assertNotIn("%", txt)
        for metric in (r"NDCG", r"\bHR\b", r"AUC", r"\bROC\b", r"\bMRR\b", r"MDE", r"Holm", r"Recall", r"Precision"):
            self.assertNotRegex(txt, metric)

    def test_mock_matches_frozen_composition(self):
        """ت-4: المحاكاة تعرض النموذج المجمَّد: مكوّناه بالأوزان الأولية المجمَّدة، وقطوع النموذج، والحساب عند t، وجمل قالبيه وحدهما؛
        والملفات المحفوظة هي ناتج scripts/align_mock.py نفسه (لا تحرير يدوي)."""
        import importlib.util
        import io
        import json
        from contextlib import redirect_stdout
        from src.backend.services.labels import comp_id
        from src.backend.settings import MODEL_CUTS
        from src.ml import serving

        fz = _frozen()
        ids = [comp_id(m) for m in fz["components"]]
        weights = {comp_id(m): w for m, w in fz["initial_weights_modal"].items()}
        sentences = {serving.TEMPLATES[m] for m in fz["components"]}
        cut = lambda d: max([c for c in MODEL_CUTS if c <= d], default=None)      # noqa: E731
        mock = lambda n: json.loads((FRONT / "mock" / n).read_text(encoding="utf-8"))  # noqa: E731

        meta = mock("meta.json")
        self.assertEqual([c["id"] for c in meta["components"]], ids)
        for c in meta["components"]:
            self.assertAlmostEqual(c["weight"], weights[c["id"]], places=4)
        self.assertEqual(meta["cutoffs"], list(MODEL_CUTS))
        for p in mock("presentations.json"):
            self.assertEqual(p["cutoffs"], list(MODEL_CUTS), p["id"])
        recs, expl = mock("recommendations.json"), mock("explanations.json")
        for reg, r in recs.items():
            self.assertEqual([c["id"] for c in r["components"]], ids, reg)
            self.assertEqual(r["snapshot_day"], r["requested_day"], reg)
            self.assertEqual(r["provenance"]["model_cut"], cut(r["requested_day"]), reg)
            self.assertEqual([i["rank"] for i in r["items"]], list(range(1, len(r["items"]) + 1)), reg)
            for it in r["items"]:
                self.assertEqual(list(it["contributions"]), ids, reg)
                self.assertIn(it["reason"], sentences, reg)
                self.assertIn(it["reason_secondary"], sentences | {None}, reg)
        for key, e in expl.items():
            self.assertEqual(sorted(c["id"] for c in e["components"]), sorted(ids), key)
            self.assertEqual(e["snapshot_day"], e["day"], key)
            for c in e["components"]:
                self.assertIn(c["sentence"], sentences, key)
                self.assertAlmostEqual(c["weight"] * c["r_tilde"], c["contribution"], places=3)
        for reg, d in mock("learner-details.json").items():
            for t in d["top_recs"]:
                self.assertIn(t["reason"], sentences, reg)
        learner_text = json.dumps([recs, expl], ensure_ascii=False)
        self.assertNotIn("cluster", learner_text)                               # D-70
        self.assertNotIn("عنقود", learner_text)
        api = (FRONT / "src" / "api.ts").read_text(encoding="utf-8")
        got = re.search(r"MODEL_CUTS = \[([^\]]*)\]", api)
        self.assertIsNotNone(got)
        self.assertEqual([int(x) for x in got.group(1).split(",")], list(MODEL_CUTS))
        spec = importlib.util.spec_from_file_location("align_mock", REPO / "scripts" / "align_mock.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        with redirect_stdout(io.StringIO()) as out:
            rc = mod.main(check=True)
        self.assertEqual(rc, 0, out.getvalue())


if __name__ == "__main__":
    unittest.main()
