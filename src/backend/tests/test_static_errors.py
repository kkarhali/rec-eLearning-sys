"""أخطاء موحدة، 409 لعروض 2014، --no-instructor، والملفات الثابتة؛ بلا حساب توصية (لا تحتاج البيانات الخام)."""
import tempfile
import unittest
from pathlib import Path

from src.backend.app import create_app
from src.backend.settings import Settings

from .asgi_client import Client


def _dist():
    d = tempfile.TemporaryDirectory()
    p = Path(d.name)
    (p / "index.html").write_text("<html><head></head><body><a href='instructor.html'>x</a></body></html>", encoding="utf-8")
    (p / "instructor.html").write_text("<html><head></head><body>inst</body></html>", encoding="utf-8")
    (p / "learner.html").write_text("<html><head></head><body>learner</body></html>", encoding="utf-8")
    return d


class TestErrorsAndStatic(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = _dist()
        cls.on = Client(create_app(Settings(frontend_dist=Path(cls.tmp.name))))
        cls.off = Client(create_app(Settings(frontend_dist=Path(cls.tmp.name), instructor_enabled=False)))

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def assertError(self, r, status, code):
        self.assertEqual(r.status, status, r.text)
        e = r.json()["error"]
        self.assertEqual(e["code"], code)
        self.assertTrue(e["message"])
        self.assertIsInstance(e["details"], dict)

    def test_health(self):
        r = self.on.get("/api/health")
        self.assertEqual(r.status, 200)
        j = r.json()
        self.assertEqual(j["status"], "ok")
        self.assertIn("run_id", j)
        self.assertIn("uptime_s", j)
        self.assertIn("server-timing", r.headers)

    def test_unknown_api_path_404(self):
        self.assertError(self.on.get("/api/nope"), 404, "not_found")

    def test_post_405(self):
        self.assertError(self.on.request("POST", "/api/health"), 405, "method_not_allowed")

    def test_confirmatory_locked_409_everywhere(self):
        for u in ["/api/recommendations?registration=BBB_2014J-1&day=75",
                  "/api/explanations/BBB_2014J-1/5?day=75",
                  "/api/learner/BBB_2014J-1/history?day=75",
                  "/api/registrations?presentation=FFF_2014B",
                  "/api/instructor/overview?presentation=BBB_2014J&day=75",
                  "/api/instructor/learners?presentation=DDD_2014J&day=75",
                  "/api/instructor/learner/GGG_2014J-1?day=75"]:
            self.assertError(self.on.get(u), 409, "confirmatory_locked")

    def test_unknown_presentation_404(self):
        self.assertError(self.on.get("/api/registrations?presentation=ZZZ_2013J"), 422, "validation_error")
        self.assertError(self.on.get("/api/registrations?presentation=AAA_2013B"), 404, "presentation_not_found")

    def test_validation_422(self):
        for u in ["/api/recommendations?registration=bad&day=75", "/api/recommendations?registration=FFF_2013J-1",
                  "/api/recommendations?registration=FFF_2013J-1&day=x", "/api/recommendations?registration=FFF_2013J-1&day=5&k=0",
                  "/api/recommendations?registration=FFF_2013J-1&day=5&k=21",
                  "/api/recommendations?registration=FFF_2013J-1&day=5&task=C",
                  "/api/learner/bad/history?day=5", "/api/explanations/bad/5?day=5",
                  "/api/instructor/learners?presentation=FFF_2013J&day=75&sort=nope",
                  "/api/instructor/learners?presentation=FFF_2013J&day=75&limit=0",
                  "/api/instructor/learners?presentation=FFF_2013J&day=75&idle=maybe",
                  "/api/registrations?presentation=FFF_2013J&limit=101"]:
            r = self.on.get(u)
            self.assertError(r, 422, "validation_error")
            self.assertTrue(r.json()["error"]["details"]["errors"])

    def test_learners_idle_param(self):
        """ب-8: idle اختياري (الافتراضي false، فلا يتغير سلوك الطلبات القديمة) ويقبل 1/0 وtrue/false."""
        from src.backend.schemas import LearnersIn
        base = {"presentation": "FFF_2013J", "day": 75}
        self.assertFalse(LearnersIn.model_validate(base).idle)
        for v, want in (("1", True), ("true", True), ("0", False), ("false", False)):
            self.assertIs(LearnersIn.model_validate({**base, "idle": v}).idle, want, v)

    def test_requirements_pin_runtime_packages(self):
        """ج-13: requirements.txt يثبّت (==) كل حزمة تبلّغ /api/meta عن إصدارها."""
        from src.backend.routes.meta import RUNTIME_PACKAGES
        from src.backend.settings import REPO_ROOT
        pins = {}
        for line in (REPO_ROOT / "requirements.txt").read_text(encoding="utf-8").splitlines():
            line = line.split("#")[0].strip()
            if line:
                name, _, ver = line.partition("==")
                self.assertTrue(ver, f"إصدار غير مثبَّت: {line}")
                pins[name.strip().lower()] = ver.strip()
        self.assertEqual(set(pins), set(RUNTIME_PACKAGES))

    def test_instructor_disabled(self):
        for u in ["/api/instructor/overview?presentation=FFF_2013J&day=75", "/api/instructor/learner/FFF_2013J-1?day=75",
                  "/api/instructor/anything"]:
            self.assertError(self.off.get(u), 404, "instructor_disabled")
        self.assertEqual(self.off.get("/api/health").json()["instructor_enabled"], False)

    def test_instructor_page_hidden_when_disabled(self):
        self.assertEqual(self.on.get("/instructor.html").status, 200)
        self.assertEqual(self.off.get("/instructor.html").status, 404)
        idx = self.off.get("/index.html")
        self.assertEqual(idx.status, 200)
        self.assertIn('a[href*="instructor"]', idx.text)
        self.assertNotIn('a[href*="instructor"]', self.on.get("/index.html").text)

    def test_root_serves_index(self):
        r = self.on.get("/")
        self.assertEqual(r.status, 200)
        self.assertIn("<html", r.text)


if __name__ == "__main__":
    unittest.main()
