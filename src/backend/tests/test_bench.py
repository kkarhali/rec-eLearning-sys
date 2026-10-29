"""ت-5 (شرط اللجنة ب-2): ``bench.py --out`` يكتب ملف نتائج بمخطط ثابت يقرؤه ``scripts/thesis/make_tables.py``.

يرقّع ``bench.get`` بأزمنة حتمية، فلا شبكة ولا خادم ولا بيانات.
"""
import json
import os
import statistics
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from unittest import mock

from src.backend import bench

N = 5
FIRST_MS = 1000.0
# لكل مسار عيّنات لاحقة حتمية بترتيب غير مرتب، فالوسيط والأقصى معروفان سلفاً
SEQ = [30.0, 10.0, 50.0, 20.0, 40.0]          # الوسيط 30، والأقصى 50


class FakeServer:
    def __init__(self):
        self.calls = {}

    def __call__(self, base, path):
        i = self.calls.get(path, 0)
        self.calls[path] = i + 1
        ms = FIRST_MS if i == 0 else SEQ[(i - 1) % len(SEQ)]
        if "day=63" in path:
            ms = 4321.0
        if "day=66" in path:
            ms = 6543.0
        body = {"status": "ok", "warm": {"enabled": True, "state": "done"}}
        if path.startswith("/api/registrations"):
            body = {"items": [{"registration": "FFF_2013J-1"}]}
        elif path.startswith("/api/recommendations"):
            body = {"items": [{"id_site": 7}]}
        return ms, body


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


class TestBench(unittest.TestCase):
    def test_bench_writes_results_file(self):
        with tempfile.TemporaryDirectory() as d:
            out = os.path.join(d, "sub", "warm.json")
            fake = FakeServer()
            argv = ["http://x", "--n", str(N), "--state", "warm", "--out", out, "--cold-day", "63",
                    "--cold-overview-day", "66"]
            with mock.patch.object(bench, "get", fake), redirect_stdout(StringIO()):
                bench.main(argv)
            doc = load(out)
            # المخطط
            self.assertEqual(doc["schema"], "serving_bench/1")
            self.assertEqual(set(doc), {"schema", "meta", "rows", "cold_days"})
            m = doc["meta"]
            for k in ("git_commit", "git_dirty", "date", "platform", "cpu_count", "presentation", "day", "n", "state",
                      "registration", "command", "cluster_cache_days_at_start", "server_health_at_start"):
                self.assertIn(k, m)
            self.assertEqual((m["state"], m["presentation"], m["day"], m["n"]), ("warm", "FFF_2013J", 75, N))
            self.assertEqual(m["cpu_count"], os.cpu_count())
            self.assertEqual(m["server_health_at_start"]["warm"]["state"], "done")
            names = [r["endpoint"] for r in doc["rows"]]
            self.assertEqual(names, ["health", "meta", "presentations", "registrations", "recommendations", "explanations",
                                     "history", "instructor/overview", "instructor/clusters", "instructor/learners",
                                     "instructor/learner"])
            # الوسيط والأقصى صحيحان ومطابقان للعيّنات المحفوظة
            for r in doc["rows"]:
                self.assertEqual(set(r), {"endpoint", "first_ms", "median_ms", "max_ms", "note", "samples_ms"})
                self.assertEqual(len(r["samples_ms"]), N)
                self.assertEqual(r["median_ms"], statistics.median(r["samples_ms"]))
                self.assertEqual(r["max_ms"], max(r["samples_ms"]))
                self.assertEqual((r["median_ms"], r["max_ms"]), (30.0, 50.0))
            rec = next(r for r in doc["rows"] if r["endpoint"] == "recommendations")
            self.assertEqual(rec["first_ms"], FIRST_MS)
            # الأيام الباردة: أول طلب وحده، لكل نقطة نهاية ويومها
            self.assertEqual([(c["endpoint"], c["day"], c["first_ms"]) for c in doc["cold_days"]],
                             [("recommendations", 63, 4321.0), ("instructor/overview", 66, 6543.0)])
            for c in doc["cold_days"]:
                self.assertIn("cluster_cached_at_start", c)
            self.assertFalse(any("day=63" in p or "day=66" in p for p, n in fake.calls.items() if n != 1))
            # قياس واحد لكل حال: لا يُكتب فوق ملف موجود
            with mock.patch.object(bench, "get", FakeServer()), redirect_stdout(StringIO()), \
                    mock.patch("sys.stderr", StringIO()), self.assertRaises(SystemExit):
                bench.main(argv)
            self.assertEqual(load(out), doc)

    def test_out_requires_state(self):
        with tempfile.TemporaryDirectory() as d, mock.patch.object(bench, "get", FakeServer()), \
                mock.patch("sys.stderr", StringIO()), self.assertRaises(SystemExit):
            bench.main(["http://x", "--out", os.path.join(d, "x.json")])

    def test_without_flags_prints_and_writes_nothing(self):
        buf = StringIO()
        with tempfile.TemporaryDirectory() as d:
            cwd = os.getcwd()
            os.chdir(d)
            try:
                with mock.patch.object(bench, "get", FakeServer()), redirect_stdout(buf):
                    bench.main(["http://x", "--n", "3", "--json"])
            finally:
                os.chdir(cwd)
            self.assertEqual(os.listdir(d), [])
        rows = json.loads(buf.getvalue())
        self.assertEqual(set(rows[0]), {"endpoint", "first_ms", "median_ms", "max_ms", "note"})


if __name__ == "__main__":
    unittest.main()
