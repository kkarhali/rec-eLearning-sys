"""اختبارات تكاملية على البيانات الفعلية وartifacts (تُتخطّى إن لم تتوفر): العقود مقابل mock، المنطق، الأداء بعد التسخين.

أول اختبار يسخّن (عرض، يوم) ≈ 10-12 ثانية؛ والباقي من الذاكرة.
"""
import json
import time
import unittest
from pathlib import Path

import numpy as np

from src.backend.app import create_app
from src.backend.settings import REPO_ROOT, Settings

from .asgi_client import Client

MOCK = REPO_ROOT / "src" / "frontend" / "mock"
HAVE = (REPO_ROOT / "data" / "raw" / "oulad" / "studentVle.csv").exists() and (REPO_ROOT / "artifacts" / "FFF_2013J").exists()
P, DAY = "FFF_2013J", 75
SENSITIVE_KEYS = {"gender", "disability", "imd_band", "age_band", "region", "highest_education", "final_result"}


def mock(name):
    return json.loads((MOCK / name).read_text(encoding="utf-8"))


def keys_of(o, path=""):
    """مجموعة مسارات المفاتيح (القوائم: عنصرها الأول)."""
    out = set()
    if isinstance(o, dict):
        for k, v in o.items():
            out.add(path + "/" + k)
            out |= keys_of(v, path + "/" + k)
    elif isinstance(o, list) and o:
        out |= keys_of(o[0], path + "[]")
    return out


def all_keys(o):
    s = set()
    if isinstance(o, dict):
        for k, v in o.items():
            s.add(k)
            s |= all_keys(v)
    elif isinstance(o, list):
        for v in o:
            s |= all_keys(v)
    return s


@unittest.skipUnless(HAVE, "البيانات الخام/artifacts غير متوفرة")
class TestApi(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app(Settings())
        cls.c = Client(cls.app)
        cls.sv = cls.app.state.services
        cls.reg = cls.c.get(f"/api/registrations?presentation={P}&limit=5").json()["items"][0]["registration"]
        cls.sid = int(cls.reg.split("-")[1])
        t = time.time()
        r = cls.c.get(f"/api/recommendations?registration={cls.reg}&day={DAY}&k=10")
        assert r.status == 200, r.text
        cls.cold = time.time() - t

    def get(self, url, status=200):
        r = self.c.get(url)
        self.assertEqual(r.status, status, r.text[:300])
        return r.json()

    def assertCovers(self, ref, got, label):
        ignore = lambda k: k in ("/mock", "/items[]/date_unregistration") or "/contributions/" in k      # علَم المحاكاة؛ وD-70 يحذف date_unregistration؛ ومفاتيح المكوّنات ديناميكية  # noqa: E731
        missing = {k for k in keys_of(ref) - keys_of(got) if not ignore(k)}
        self.assertFalse(missing, f"{label}: مفاتيح mock غائبة {sorted(missing)[:8]}")

    # ------------------------------------------------------------ عقود مقابل mock
    def test_meta_contract(self):
        m = self.get("/api/meta")
        self.assertCovers(mock("meta.json"), m, "meta")
        self.assertTrue(m["data_fingerprint"].startswith("md5:"))
        self.assertEqual(len(m["git_commit"]), 12)
        self.assertEqual(m["cutoffs"], [70, 126, 182])
        self.assertIn(P, m["presentations"])
        self.assertEqual(m["data_files"]["studentVle.csv"], "b8aae6f4ffd1523319aeb56d66b17f72")
        self.assertFalse([p for p in m["presentations"] if "2014" in p])
        # ج-13: إصدارات بيئة التشغيل الفعلية (ومنها starlette وuvicorn وpydantic)
        from importlib import metadata
        self.assertEqual(set(m["runtime"]), {"python", "numpy", "pandas", "starlette", "uvicorn", "pydantic", "anyio"})
        for pkg in ("numpy", "pandas", "starlette", "uvicorn", "pydantic", "anyio"):
            self.assertEqual(m["runtime"][pkg], metadata.version(pkg), pkg)
        self.assertEqual(m["risk_score"]["display_from_day"], 56)       # ج-14: القطع 28 مبني ولا يُعرض

    def test_health_and_presentations(self):
        self.assertCovers(mock("health.json"), self.get("/api/health"), "health")
        ps = self.get("/api/presentations")
        self.assertCovers(mock("presentations.json")[0], ps[0], "presentation")
        self.assertEqual(ps[0]["id"], P)
        locked = [p for p in ps if p["status"] == "locked"]
        self.assertTrue(locked and all(p["role"] == "confirm" and p["snapshots"] == [] for p in locked))
        self.assertEqual(sum(p["status"] == "published" for p in ps), 9)

    def test_registrations_paging_and_search(self):
        a = self.get(f"/api/registrations?presentation={P}&limit=10&offset=0")
        self.assertCovers(mock("registrations.json"), a, "registrations")
        self.assertEqual(a["total"], 2283)
        b = self.get(f"/api/registrations?presentation={P}&limit=10&offset=10")
        self.assertFalse({x["registration"] for x in a["items"]} & {x["registration"] for x in b["items"]})
        q = self.get(f"/api/registrations?presentation={P}&q={self.sid}")
        self.assertIn(self.reg, [x["registration"] for x in q["items"]])
        self.assertTrue(all(str(self.sid) in x["registration"] for x in q["items"]))
        self.assertTrue(all(set(x) == {"registration", "id_student", "date_registration", "status"} for x in a["items"]))  # D-70
        self.assertEqual({x["status"] for x in a["items"]}, {"ok"})        # بلا day لا حالة مشتقة من المستقبل

    def test_recommendation_contract(self):
        r = self.get(f"/api/recommendations?registration={self.reg}&day={DAY}&k=10")
        ref = next(iter(mock("recommendations.json").values()))
        self.assertCovers(ref, r, "recommendation")
        self.assertEqual(len(r["items"]), 10)
        self.assertEqual([i["rank"] for i in r["items"]], list(range(1, 11)))
        scores = [i["relevance"] for i in r["items"]]
        self.assertEqual(scores, sorted(scores, reverse=True))
        self.assertEqual(r["provenance"]["model_cut"], 70)            # D-49: أقرب قطع ≤ 75
        self.assertEqual(r["snapshot_day"], DAY)
        self.assertEqual(r["context"]["week"], DAY // 7 + 1)
        cids = {c["id"] for c in r["components"]}
        for it in r["items"]:
            self.assertLessEqual(set(it["contributions"]), cids)
            self.assertAlmostEqual(sum(it["contributions"].values()), it["relevance"], places=2)
        self.assertAlmostEqual(sum(c["weight"] for c in r["components"]), 1.0, places=3)
        self.assertEqual(self.get(f"/api/recommendations?registration={self.reg}&day={DAY}&k=3")["items"], r["items"][:3])

    def test_model_cut_by_day(self):
        for day, cut in [(40, None), (69, None), (70, 70), (125, 70), (126, 126), (200, 182)]:
            r = self.get(f"/api/recommendations?registration={self.reg}&day={day}&k=3")
            self.assertIn("model_cut", r["provenance"])
            self.assertEqual(r["provenance"]["model_cut"], cut, day)
        r = self.get(f"/api/recommendations?registration={self.reg}&day=40&k=3")
        self.assertTrue(r["note"] and "قبل أول قطع" in r["note"])      # R-B2/FR-37

    def test_task_a_excludes_seen_task_b_may_include(self):
        a = self.get(f"/api/recommendations?registration={self.reg}&day={DAY}&k=20&task=A")
        b = self.get(f"/api/recommendations?registration={self.reg}&day={DAY}&k=20&task=B")
        ix = self.sv.repo.index(P)
        seen = set(ix.student_events(self.sid, DAY)["id_site"].astype(int))
        self.assertFalse({i["id_site"] for i in a["items"]} & seen)
        self.assertEqual(b["task"], "B")
        self.assertTrue({i["id_site"] for i in b["items"]} & seen)

    def test_explanation_contract_and_consistency(self):
        r = self.get(f"/api/recommendations?registration={self.reg}&day={DAY}&k=10")
        top = r["items"][0]
        e = self.get(f"/api/explanations/{self.reg}/{top['id_site']}?day={DAY}")
        ref = mock("explanations.json")
        self.assertCovers(next(iter(ref.values())), e, "explanation")
        self.assertAlmostEqual(sum(c["contribution"] for c in e["components"]), top["relevance"], places=2)
        for c in e["components"]:
            self.assertAlmostEqual(c["weight"] * c["r_tilde"], c["contribution"], places=2)
            self.assertTrue(c["sentence"])
            if c["evidence"]:
                self.assertIn(c["evidence"]["type"], ("count", "item", "assessment"))
        self.assertEqual([c["contribution"] for c in e["components"]], sorted((c["contribution"] for c in e["components"]), reverse=True))
        self.get(f"/api/explanations/{self.reg}/1?day={DAY}", status=404)

    def test_history_contract(self):
        h = self.get(f"/api/learner/{self.reg}/history?day={DAY}&window=28")
        self.assertCovers({"registration": 1, "day": 1, "window": 1, "active_days": 1, "daily": [{"day": 1, "clicks": 1}],
                           "recent": [{"day": 1, "id_site": 1, "activity_type": "x", "clicks": 1}]}, h, "history")
        self.assertEqual([d["day"] for d in h["daily"]], list(range(DAY - 27, DAY + 1)))
        self.assertTrue(all(e["day"] <= DAY for e in h["recent"]))
        self.assertLessEqual(len(h["recent"]), 3)
        h5 = self.get(f"/api/learner/{self.reg}/history?day=10&window=5")
        self.assertTrue(all(e["day"] <= 10 for e in h5["recent"]))
        self.get(f"/api/learner/{P}-99/history?day=10", status=404)

    def test_learner_responses_have_no_risk_or_sensitive(self):
        urls = [f"/api/recommendations?registration={self.reg}&day={DAY}&k=20", f"/api/learner/{self.reg}/history?day={DAY}",
                f"/api/registrations?presentation={P}&limit=100"]
        top = self.get(urls[0])["items"][0]["id_site"]
        urls.append(f"/api/explanations/{self.reg}/{top}?day={DAY}")
        bad = {"risk", "probability", "cluster", "threshold", "above_threshold", "outcome"} | SENSITIVE_KEYS
        for u in urls:
            self.assertFalse(all_keys(self.get(u)) & bad, u)

    def test_withdrawn_and_unknown_status(self):
        ix = self.sv.repo.index(P)
        wd = ix.reg[ix.reg["date_unregistration"].notna()]
        sid = int(wd.index[0])
        day = int(wd.iloc[0]["date_unregistration"])
        r = self.get(f"/api/recommendations?registration={P}-{sid}&day={max(day, 0)}&k=5")
        self.assertEqual(r["status"], "withdrawn")
        self.assertEqual(r["items"], [])
        self.assertIn("model_cut", r["provenance"])
        self.get(f"/api/explanations/{P}-{sid}/5?day={max(day, 0)}", status=404)
        reg = self.get(f"/api/registrations?presentation={P}&limit=100&offset=2200&day=268")
        self.assertIn("withdrawn", {x["status"] for x in reg["items"]})
        early = self.get(f"/api/registrations?presentation={P}&q={sid}&day=0")["items"]    # قبل الانسحاب لا يظهر منسحباً
        self.assertNotEqual(early[0]["status"], "withdrawn") if day > 0 else None

    def test_day_out_of_range(self):
        r = self.get(f"/api/recommendations?registration={self.reg}&day=300", status=422)
        self.assertEqual(r["error"]["code"], "day_out_of_range")
        self.assertEqual(r["error"]["details"]["max_day"], 268)

    def test_meta_declares_unsafe_demo_and_score(self):
        m = self.get("/api/meta")
        self.assertEqual(m["bind_host"], "127.0.0.1")
        self.assertIn("بلا أمان وصول", m["access_notice"])
        self.assertEqual(m["risk_score"]["field"], "score")
        self.assertIn("غير معايَرة", m["risk_score"]["label_ar"])
        self.assertFalse(m["risk_score"]["calibrated"])

    # ------------------------------------------------------------ المدرّس
    def test_overview_contract(self):
        o = self.get(f"/api/instructor/overview?presentation={P}&day={DAY}")
        self.assertCovers(mock("overview.json"), o, "overview")
        self.assertEqual(o["provenance"]["model_cut"], 70)
        self.assertEqual(o["risk"]["cut_day"], 56)
        self.assertEqual(sum(b["count"] for b in o["risk"]["histogram"]), self.get(
            f"/api/instructor/learners?presentation={P}&day={DAY}&limit=1")["total"] - self._no_risk_count())
        self.assertAlmostEqual(sum(t["catalogue_share"] for t in o["coverage"]["by_type"]), 1.0, places=1)
        self.assertLessEqual(o["coverage"]["covered_items"], o["coverage"]["catalogue_size"])

    def _no_risk_count(self):
        t = self.sv.instructor.snapshot(P, DAY).table
        return int(t["prob"].isna().sum())

    def test_clusters_contract(self):
        c = self.get(f"/api/instructor/clusters?presentation={P}&day={DAY}")
        self.assertCovers(mock("clusters.json"), c, "clusters")
        total = self.get(f"/api/instructor/learners?presentation={P}&day={DAY}&limit=1")["total"]
        self.assertEqual(sum(x["size"] for x in c["clusters"]), total)
        self.assertEqual(len(c["clusters"]), c["k"])
        self.assertEqual(len(c["points"]), total)
        self.assertEqual({p["cluster"] for p in c["points"]}, {x["id"] for x in c["clusters"] if x["size"]})
        self.assertEqual(len({x["label_ar"] for x in c["clusters"]}), c["k"])
        self.assertIsInstance(c["unstable"], bool)
        self.assertEqual(c["cluster_day"], 56)
        if c["unstable"]:                                   # شارة «غير مستقرة» تُفسَّر بالقاعدة التي حكمت بها (D-39-ب)
            self.assertTrue(c["unstable_reason"])
            if c["quality"]["ari"] >= 0.8:                 # ARI عالٍ + غير مستقر ⇒ السبب شرط أفضل اثنين، لا ثبات البذور
                self.assertIn("أفضل اثنين", c["unstable_reason"])
        else:
            self.assertIsNone(c["unstable_reason"])
        self.assertIsNotNone(c["quality"]["ari"])             # عروض 2013 كلها في learner_clusters.csv
        meta = self.get("/api/meta")["risk_score"]
        self.assertIn("رسوب", meta["target_ar"])

    def test_learners_contract_sort_page_filter(self):
        base = f"/api/instructor/learners?presentation={P}&day={DAY}"
        a = self.get(base + "&limit=50")
        self.assertCovers(mock("learners.json"), a, "learners")
        self.assertEqual((a["limit"], a["offset"]), (50, 0))
        probs = [r["risk"]["score"] for r in a["items"] if r["risk"]]
        self.assertEqual(probs, sorted(probs, reverse=True))               # الافتراضي -risk
        asc = self.get(base + "&limit=50&sort=risk")["items"]
        pa = [r["risk"]["score"] for r in asc if r["risk"]]
        self.assertEqual(pa, sorted(pa))
        for key, getter in [("active_days", lambda r: r["active_days"]), ("-active_days", lambda r: r["active_days"]),
                            ("last_access", lambda r: -1 if r["last_access_day"] is None else r["last_access_day"]),
                            ("reg", lambda r: int(r["registration"].split("-")[1]))]:
            rows = self.get(base + f"&limit=100&sort={key}")["items"]
            vals = [getter(r) for r in rows]
            self.assertEqual(vals, sorted(vals, reverse=key.startswith("-")), key)
        b = self.get(base + "&limit=50&offset=50")
        self.assertFalse({r["registration"] for r in a["items"]} & {r["registration"] for r in b["items"]})
        self.assertEqual(b["offset"], 50)
        ab = self.get(base + "&limit=500&risk=above")
        self.assertTrue(ab["items"] and all(r["risk"]["above_threshold"] for r in ab["items"]))
        self.assertLess(ab["total"], a["total"])
        cl = self.get(base + "&limit=500&cluster=1")
        self.assertTrue(cl["items"] and all(r["cluster"]["id"] == 1 for r in cl["items"]))
        row = a["items"][0]
        self.assertEqual(row["risk"]["provenance"], "lopo_2013")
        self.assertNotIn("probability", row["risk"])
        self.assertIn("غير معايَرة", self.get(f"/api/instructor/overview?presentation={P}&day={DAY}")["risk"]["label_ar"])
        self.assertEqual(row["risk"]["above_threshold"], row["risk"]["score"] >= row["risk"]["threshold"])
        # العتبة بدقتها المخزَّنة (0.4557…) لا 0.456، فلا يختلف حكم «فوق العتبة» بين الخادم والعارض
        self.assertAlmostEqual(row["risk"]["threshold"], self.sv.repo.engine._risk(P, 26247, DAY, "M1")["threshold"], places=5)
        self.assertNotEqual(row["risk"]["threshold"], round(row["risk"]["threshold"], 3))
        for r in a["items"]:
            if r["risk"]:
                self.assertEqual(r["risk"]["above_threshold"], r["risk"]["score"] >= r["risk"]["threshold"])

    def _all_rows(self, query, page=100):
        """كل صفوف الجدول بالترقيم (limit/offset) مع التحقق من ثبات total ومن عدم التداخل بين الصفحات."""
        rows, total, off = [], None, 0
        while True:
            pg = self.get(f"/api/instructor/learners?presentation={P}&day={DAY}{query}&limit={page}&offset={off}")
            total = pg["total"] if total is None else total
            self.assertEqual(pg["total"], total, f"total يتغير بين الصفحات ({query}, offset={off})")
            self.assertEqual((pg["limit"], pg["offset"]), (page, off))
            self.assertLessEqual(len(pg["items"]), page)
            rows += pg["items"]
            off += page
            if off >= total:
                break
        self.assertEqual(len(rows), total, query)
        self.assertEqual(len({r["registration"] for r in rows}), total, f"صفوف مكررة بين الصفحات ({query})")
        return rows, total

    def test_learners_idle_filter_server_side_and_paging(self):
        """ب-8 (FR-32): idle=1 يصفّي الفوج كله في الخادم قبل الترقيم بتعريف الواجهة نفسه (لا وصول ≤ t، أو t − آخر وصول ≥ 14)."""
        idle = lambda r: r["last_access_day"] is None or DAY - r["last_access_day"] >= 14   # noqa: E731
        rows, total = self._all_rows("&sort=reg")
        kpi = self.get(f"/api/instructor/overview?presentation={P}&day={DAY}")["kpis"]["cohort_size"]
        self.assertEqual(total, kpi)
        want = {r["registration"] for r in rows if idle(r)}
        self.assertTrue(0 < len(want) < total)
        self.assertGreater(len([r for r in rows[100:] if idle(r)]), 0)     # خاملون خارج أول 100 صف (ما كانت الواجهة تفوّته)
        got, n = self._all_rows("&sort=reg&idle=1")
        self.assertEqual(n, len(want))
        self.assertEqual({r["registration"] for r in got}, want)
        self.assertTrue(all(idle(r) for r in got))
        ids = [int(r["registration"].split("-")[1]) for r in got]
        self.assertEqual(ids, sorted(ids))                                   # الفرز محفوظ مع التصفية
        # التوافق: idle=0 وغياب المعامل سواء؛ والتصفية تُجمع مع risk وcluster
        self.assertEqual(self.get(f"/api/instructor/learners?presentation={P}&day={DAY}&idle=0&limit=1")["total"], total)
        self.assertEqual(self.get(f"/api/instructor/learners?presentation={P}&day={DAY}&idle=true&limit=1")["total"], len(want))
        above = {r["registration"] for r in rows if r["risk"] and r["risk"]["above_threshold"]}
        both, _ = self._all_rows("&idle=1&risk=above", page=500)
        self.assertEqual({r["registration"] for r in both}, want & above)
        c1 = {r["registration"] for r in rows if r["cluster"]["id"] == 1}
        ic, _ = self._all_rows("&idle=1&cluster=1", page=500)
        self.assertEqual({r["registration"] for r in ic}, want & c1)
        # إزاحة بعد آخر صف: صفحة فارغة وtotal نفسه (الواجهة تعود إلى آخر صفحة)
        far = self.get(f"/api/instructor/learners?presentation={P}&day={DAY}&idle=1&offset={n + 5}&limit=100")
        self.assertEqual((far["items"], far["total"]), ([], n))
        # الخمول يتبع اليوم المطلوب نفسه
        later = self.get(f"/api/instructor/learners?presentation={P}&day=126&idle=1&limit=500")
        self.assertTrue(all(r["last_access_day"] is None or 126 - r["last_access_day"] >= 14 for r in later["items"]))

    def test_learner_detail_contract(self):
        row = self.get(f"/api/instructor/learners?presentation={P}&day={DAY}&limit=1")["items"][0]
        d = self.get(f"/api/instructor/learner/{row['registration']}?day={DAY}")
        self.assertCovers(next(iter(mock("learner-details.json").values())), d, "learner detail")
        self.assertEqual(d["cluster"], row["cluster"])
        self.assertAlmostEqual(d["risk"]["score"], row["risk"]["score"], places=3)
        self.assertEqual(d["risk"]["top_factor"], row["risk"]["top_factor"])
        self.assertNotIn("outcome", d)
        for day, cut in ((DAY, 70), (130, 126)):                 # D-49 (6): provenance.model_cut في ملف المتعلم أيضاً
            dd = self.get(f"/api/instructor/learner/{row['registration']}?day={day}")
            self.assertEqual(set(dd["provenance"]), {"run_id", "role", "model_cut"})
            self.assertEqual(dd["provenance"]["model_cut"], cut)
        self.assertFalse(all_keys(d) & SENSITIVE_KEYS)
        self.get(f"/api/instructor/learner/{P}-99?day={DAY}", status=404)

    def test_provenance_model_cut_in_every_day_dependent_response(self):
        reg = self.reg
        for day, cut in ((DAY, 70), (130, 126)):
            urls = [f"/api/recommendations?registration={reg}&day={day}",
                    f"/api/learner/{reg}/history?day={day}",
                    f"/api/instructor/overview?presentation={P}&day={day}", f"/api/instructor/clusters?presentation={P}&day={day}",
                    f"/api/instructor/learners?presentation={P}&day={day}&limit=3", f"/api/instructor/learner/{reg}?day={day}"]
            top = self.get(urls[0])["items"][0]["id_site"]
            urls.append(f"/api/explanations/{reg}/{top}?day={day}")
            for u in urls:
                pv = self.get(u)["provenance"]
                self.assertEqual(set(pv), {"run_id", "role", "model_cut"}, u)
                self.assertEqual(pv["model_cut"], cut, u)

    def test_instructor_day_before_first_snapshot(self):
        for u in ["overview", "clusters", "learners"]:
            r = self.get(f"/api/instructor/{u}?presentation={P}&day=40", status=422)
            self.assertEqual(r["error"]["code"], "day_before_first_snapshot")
            self.assertEqual(r["error"]["details"]["first_day"], 56)

    # ------------------------------------------------------------ تطابق مع serving
    def test_risk_matches_engine_m1(self):
        eng = self.sv.repo.engine
        rows = self.get(f"/api/instructor/learners?presentation={P}&day={DAY}&limit=15&offset=300")["items"]
        n = 0
        for r in rows:
            if not r["risk"]:
                continue
            sid = int(r["registration"].split("-")[1])
            ref = eng._risk(P, sid, DAY, "M1")
            if ref and ref.get("score") is not None:
                n += 1
                self.assertAlmostEqual(r["risk"]["score"], ref["score"], places=3)
                self.assertAlmostEqual(r["risk"]["threshold"], ref["threshold"], places=3)
                self.assertEqual(r["risk"]["cut_day"], ref["risk_cut"])
        self.assertGreater(n, 5)

    def test_cluster_matches_engine(self):
        eng = self.sv.repo.engine
        rows = self.get(f"/api/instructor/learners?presentation={P}&day={DAY}&limit=15&offset=500")["items"]
        for r in rows:
            sid = int(r["registration"].split("-")[1])
            self.assertEqual(r["cluster"]["id"], eng._cluster(P, sid, DAY)["cluster"])

    def test_recommendation_matches_engine(self):
        eng = self.sv.repo.engine
        ref = eng.recommend(P, self.sid, DAY, k=10)
        r = self.get(f"/api/recommendations?registration={self.reg}&day={DAY}&k=10")
        self.assertEqual([i["id_site"] for i in r["items"]], [x["id_site"] for x in ref])

    # ------------------------------------------------------------ أداء بعد التسخين
    def test_latency_after_warmup(self):
        urls = [f"/api/health", "/api/meta", "/api/presentations", f"/api/registrations?presentation={P}&limit=100",
                f"/api/recommendations?registration={self.reg}&day={DAY}&k=10",
                f"/api/learner/{self.reg}/history?day={DAY}",
                f"/api/instructor/overview?presentation={P}&day={DAY}", f"/api/instructor/clusters?presentation={P}&day={DAY}",
                f"/api/instructor/learners?presentation={P}&day={DAY}&limit=100&sort=-risk",
                f"/api/instructor/learner/{self.reg}?day={DAY}"]
        top = self.get(urls[4])["items"][0]["id_site"]
        urls.append(f"/api/explanations/{self.reg}/{top}?day={DAY}")
        for u in urls:
            self.c.get(u)                                           # تسخين
            t = time.perf_counter()
            r = self.c.get(u)
            ms = (time.perf_counter() - t) * 1000
            self.assertEqual(r.status, 200, u)
            self.assertLess(ms, 300, f"{u}: {ms:.0f}ms")


if __name__ == "__main__":
    unittest.main()
