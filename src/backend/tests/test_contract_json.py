"""D-70: اختبار العقد على JSON المسلسَل فعلياً (مفاتيح وقيماً، تكرارياً) لطلبات عيّنة؛ يحتاج البيانات (يُتخطّى بدونها).

المتعلم: لا مفتاح ولا قيمة نصية تحوي {risk, probability, cluster, final_result, السمات الست}.
التسجيلات: لا ``date_unregistration`` ولا ``final_result``.  المدرّس: قائمة بيضاء للمفاتيح تكرارياً بلا سمات حساسة.
(المفتاح ``score`` مسموح في عناصر التوصية: هو درجة الهجين نفسها لا درجة الخطر.)
"""
import re
import unittest

from src.backend import schemas
from src.backend.app import create_app
from src.backend.settings import Settings

from .asgi_client import Client
from .test_api_live import HAVE, P
from .test_contract_no_risk import field_names

FORBIDDEN = ["risk", "probability", "cluster", "final_result", "gender", "disability", "imd_band", "age_band", "region",
             "highest_education"]
FORBIDDEN_RE = re.compile("|".join(FORBIDDEN), re.I)
SENSITIVE_RE = re.compile("final_result|gender|disability|imd_band|age_band|region|highest_education", re.I)


def walk(o, path=""):
    """يعيد (نوع، نص) لكل مفتاح وكل قيمة نصية."""
    if isinstance(o, dict):
        for k, v in o.items():
            yield "key", f"{path}/{k}", k
            yield from walk(v, f"{path}/{k}")
    elif isinstance(o, list):
        for v in o:
            yield from walk(v, path + "[]")
    elif isinstance(o, str):
        yield "value", path, o


@unittest.skipUnless(HAVE, "البيانات الخام/artifacts غير متوفرة")
class TestSerializedContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.c = Client(create_app(Settings()))
        cls.reg = cls.c.get(f"/api/registrations?presentation={P}&limit=1").json()["items"][0]["registration"]

    def js(self, url):
        r = self.c.get(url)
        self.assertEqual(r.status, 200, url + r.text[:200])
        return r.json()

    def learner_samples(self):
        yield self.js(f"/api/recommendations?registration={self.reg}&day=75&k=20")
        yield self.js(f"/api/recommendations?registration={self.reg}&day=40&k=5&task=B")
        top = self.js(f"/api/recommendations?registration={self.reg}&day=75&k=20")["items"]
        for it in top[:5]:
            yield self.js(f"/api/explanations/{self.reg}/{it['id_site']}?day=75")
        yield self.js(f"/api/learner/{self.reg}/history?day=75")
        yield self.js(f"/api/registrations?presentation={P}&limit=100")
        yield self.js(f"/api/registrations?presentation={P}&limit=100&day=268")
        yield self.js("/api/presentations")

    def test_learner_json_has_no_forbidden_key_or_value(self):
        n = 0
        for body in self.learner_samples():
            for kind, path, text in walk(body):
                n += 1
                self.assertIsNone(FORBIDDEN_RE.search(text), f"{kind} {path}: {text!r}")
        self.assertGreater(n, 500)

    def test_registrations_have_no_final_result_or_unregistration(self):
        for url in (f"/api/registrations?presentation={P}&limit=100", f"/api/registrations?presentation={P}&limit=100&day=268"):
            for x in self.js(url)["items"]:
                self.assertEqual(set(x), {"registration", "id_student", "date_registration", "status"})
            raw = self.c.get(url).text
            self.assertNotIn("date_unregistration", raw)
            self.assertNotIn("final_result", raw)

    def test_no_decision_ids_and_correct_plurals_in_any_text(self):
        urls = [f"/api/recommendations?registration={self.reg}&day=40&k=20", f"/api/recommendations?registration={self.reg}&day=75&k=20",
                f"/api/instructor/clusters?presentation={P}&day=75", f"/api/instructor/learner/{self.reg}?day=75", "/api/meta"]
        for it in self.js(f"/api/recommendations?registration={self.reg}&day=40&k=20")["items"][:3]:
            urls.append(f"/api/explanations/{self.reg}/{it['id_site']}?day=40")
        for u in urls:
            for kind, path, text in walk(self.js(u)):
                if kind == "value":
                    self.assertNotRegex(text, r"\bD-\d", f"{u} {path}")
                    self.assertNotRegex(text, r"(?<!\d)(?:[3-9]|10) يوماً|\b(?:1[1-9]|[2-9]\d) أيام", f"{u} {path}: {text}")

    def test_kpi_cohort_consistent_with_clusters_and_table(self):
        o = self.js(f"/api/instructor/overview?presentation={P}&day=75")["kpis"]
        c = self.js(f"/api/instructor/clusters?presentation={P}&day=75")
        t = self.js(f"/api/instructor/learners?presentation={P}&day=75&limit=1")["total"]
        self.assertEqual(o["cohort_size"], sum(x["size"] for x in c["clusters"]))
        self.assertEqual(o["cohort_size"], t)
        self.assertLessEqual(o["active_learners"], o["cohort_size"])

    def test_c7_evidence_key_renamed(self):
        top = self.js(f"/api/recommendations?registration={self.reg}&day=75&k=1")["items"][0]["id_site"]
        raw = self.c.get(f"/api/explanations/{self.reg}/{top}?day=75").text
        self.assertNotIn("cluster", raw.lower())
        self.assertIn('"scope":"similar"', raw)

    def test_instructor_json_keys_are_whitelisted_and_not_sensitive(self):
        allowed = set()
        for m in schemas.INSTRUCTOR_MODELS:
            allowed |= field_names(m)
        allowed |= {"items", "total", "limit", "offset"}   # غلاف Page العام
        urls = [f"/api/instructor/overview?presentation={P}&day=75", f"/api/instructor/clusters?presentation={P}&day=75",
                f"/api/instructor/learners?presentation={P}&day=75&limit=100", f"/api/instructor/learner/{self.reg}?day=75"]
        for u in urls:
            for kind, path, text in walk(self.js(u)):
                self.assertIsNone(SENSITIVE_RE.search(text), f"{u} {kind} {path}: {text!r}")
                if kind == "key":
                    self.assertIn(text, allowed, f"{u}: مفتاح خارج القائمة البيضاء {path}")


if __name__ == "__main__":
    unittest.main()
