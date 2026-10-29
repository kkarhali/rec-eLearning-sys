"""قياس الأزمنة على خادم يعمل: ``python3 -m src.backend.bench [base_url] [--day 75] [--presentation FFF_2013J] [--n 20]``.

يطبع لكل مسار: زمن الطلب الأول (يشمل أي حساب بارد) ووسيط/أقصى n طلباً لاحقاً. شغّله على خادم بلا ``--warm`` ثم على خادم
بتسخين لتسجيل الفرق (انظر README).

ت-5 (شرط اللجنة ب-2): ``--out PATH --state {cold,warm,precomputed}`` يكتب الصفوف نفسها مع عيّناتها وبيانات وصفية (git_commit،
التاريخ، المنصة وعدد الأنوية، العرض واليوم وn، وحال الخادم كما يمررها المشغّل) ملفَّ JSON، ولا يكتب فوق ملف موجود (قياس واحد
لكل حال، بلا انتقاء). و``--cold-day D`` (يتكرر) يقيس أول طلب توصية في يوم بارد D، و``--cold-overview-day D`` (يتكرر) أول نظرة
عامة للمدرّس في يوم بارد D قبل أي طلب فيه (بروتوكول ``test_cold_day_bounded_after_cluster_precompute``). مثال:

    python3 -m src.backend.bench http://127.0.0.1:8100 --state warm --out results/serving_bench/warm.json

ويقرؤها ``scripts/thesis/make_tables.py`` لتوليد الجدول 5-6 وأرقام 5-6-3 وNFR-01.
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
import platform
import statistics
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CLUSTER_CACHE = ROOT / "data" / "cache" / "serving_clusters"   # serving.Engine.cluster_cache_dir الافتراضي (D-68)
STATES = ("cold", "warm", "precomputed")
ROW_KEYS = ("endpoint", "first_ms", "median_ms", "max_ms", "note")


def get(base: str, path: str):
    t = time.perf_counter()
    with urllib.request.urlopen(base + path, timeout=300) as r:
        body = r.read()
    return (time.perf_counter() - t) * 1000, json.loads(body)


def _git():
    def run(*args):
        try:
            return subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True, text=True, timeout=10).stdout
        except Exception:                                           # noqa: BLE001  (لا git في البيئة)
            return ""
    status = [l for l in run("status", "--porcelain").splitlines() if l.strip()]
    return {"git_commit": run("rev-parse", "HEAD").strip() or None, "git_dirty": bool(status),
            "git_dirty_paths": sorted(l[3:] for l in status)}


def _cached_days(presentation: str):
    """أيام العرض التي لها اختيار عناقيد محفوظ في الذاكرة الدائمة على هذه الآلة (None إن غاب المجلد)."""
    if not CLUSTER_CACHE.is_dir():
        return None
    out = []
    for p in CLUSTER_CACHE.glob(f"{presentation}_*.npz"):
        tail = p.stem[len(presentation) + 1:]
        if tail.isdigit():
            out.append(int(tail))
    return sorted(out)


def measure(a):
    """يشغّل القياس ويعيد (rows, cold, samples, reg, health_before)."""
    P, D = a.presentation, a.day
    health = None
    if a.out:                                                       # حال الخادم (التسخين) تُسجَّل مع الملف وحده
        try:
            health = get(a.base, "/api/health")[1]
        except Exception:                                           # noqa: BLE001
            pass
    reg = get(a.base, f"/api/registrations?presentation={P}&limit=1")[1]["items"][0]["registration"]
    paths = [("health", "/api/health"), ("meta", "/api/meta"), ("presentations", "/api/presentations"),
             ("registrations", f"/api/registrations?presentation={P}&limit=100"),
             ("recommendations", f"/api/recommendations?registration={reg}&day={D}&k=10"),
             ("history", f"/api/learner/{reg}/history?day={D}"),
             ("instructor/overview", f"/api/instructor/overview?presentation={P}&day={D}"),
             ("instructor/clusters", f"/api/instructor/clusters?presentation={P}&day={D}"),
             ("instructor/learners", f"/api/instructor/learners?presentation={P}&day={D}&limit=100&sort=-risk"),
             ("instructor/learner", f"/api/instructor/learner/{reg}?day={D}")]
    rows, samples = [], {}
    for name, path in paths:
        try:
            first, body = get(a.base, path)
        except Exception as e:                                  # noqa: BLE001  (مثلاً --no-instructor)
            rows.append((name, None, None, None, str(e)[:40]))
            continue
        if name == "recommendations":
            sid = body["items"][0]["id_site"]
            paths_extra = ("explanations", f"/api/explanations/{reg}/{sid}?day={D}")
        ts = [get(a.base, path)[0] for _ in range(a.n)]
        rows.append((name, first, statistics.median(ts), max(ts), ""))
        samples[name] = ts
        if name == "recommendations":
            f2, _ = get(a.base, paths_extra[1])
            ts = [get(a.base, paths_extra[1])[0] for _ in range(a.n)]
            rows.append(("explanations", f2, statistics.median(ts), max(ts), ""))
            samples["explanations"] = ts
    cold = []
    for endpoint, days in (("recommendations", a.cold_day), ("instructor/overview", a.cold_overview_day)):
        for d in days:
            path = (f"/api/recommendations?registration={reg}&day={d}&k=10" if endpoint == "recommendations"
                    else f"/api/instructor/overview?presentation={P}&day={d}")
            try:
                ms, _ = get(a.base, path)
                cold.append({"endpoint": endpoint, "day": d, "first_ms": ms, "note": ""})
            except Exception as e:                              # noqa: BLE001
                cold.append({"endpoint": endpoint, "day": d, "first_ms": None, "note": str(e)[:80]})
    return rows, cold, samples, reg, health


def result_doc(a, rows, cold, samples, reg, health, cached, started, git):
    meta = {"tool": "src/backend/bench.py", "state": a.state, "date": started.isoformat(timespec="seconds"),
            **git, "platform": platform.platform(), "machine": platform.machine(),
            "processor": platform.processor() or None, "python": platform.python_version(), "cpu_count": os.cpu_count(),
            "loadavg_at_start": list(os.getloadavg()) if hasattr(os, "getloadavg") else None,
            "base_url": a.base, "presentation": a.presentation, "day": a.day, "n": a.n, "registration": reg,
            "command": "python3 -m src.backend.bench " + " ".join(a.argv),
            "cluster_cache_days_at_start": None if cached is None else len(cached),
            "server_health_at_start": health}
    out_rows = []
    for r in rows:
        d = dict(zip(ROW_KEYS, r))
        d["samples_ms"] = samples.get(r[0])
        out_rows.append(d)
    cached_set = set(cached or [])
    for c in cold:
        c["cluster_cached_at_start"] = c["day"] in cached_set
    return {"schema": "serving_bench/1", "meta": meta, "rows": out_rows, "cold_days": cold}


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    ap = argparse.ArgumentParser()
    ap.add_argument("base", nargs="?", default="http://127.0.0.1:8000")
    ap.add_argument("--day", type=int, default=75)
    ap.add_argument("--presentation", default="FFF_2013J")
    ap.add_argument("--n", type=int, default=20)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--out", default=None, help="يكتب الناتج JSON في هذا المسار (لا يكتب فوق ملف موجود)")
    ap.add_argument("--state", choices=STATES, default=None, help="حال الخادم كما يعرفها المشغّل؛ لازم مع --out")
    ap.add_argument("--cold-day", type=int, action="append", default=[], help="يتكرر: أول طلب توصية في يوم بارد")
    ap.add_argument("--cold-overview-day", type=int, action="append", default=[],
                    help="يتكرر: أول نظرة عامة للمدرّس في يوم بارد قبل أي طلب فيه")
    a = ap.parse_args(argv)
    a.argv = argv
    if a.out:
        if a.state is None:
            ap.error("--out يتطلب --state {cold,warm,precomputed}")
        if os.path.exists(a.out):
            ap.error(f"{a.out} موجود: قياس واحد لكل حال، فلا يُكتب فوقه")
    started = datetime.datetime.now(datetime.timezone.utc)
    cached = _cached_days(a.presentation)
    git = _git() if a.out else None                                 # نسخة الشيفرة عند بدء القياس
    rows, cold, samples, reg, health = measure(a)
    if a.out:
        doc = result_doc(a, rows, cold, samples, reg, health, cached, started, git)
        os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
        with open(a.out, "x", encoding="utf-8") as f:
            json.dump(doc, f, ensure_ascii=False, indent=1)
            f.write("\n")
    if a.json:
        print(json.dumps([dict(zip(ROW_KEYS, r)) for r in rows], ensure_ascii=False))
        return
    print(f"{'endpoint':22}{'first(ms)':>12}{'median(ms)':>12}{'max(ms)':>10}")
    for n, f, m, x, note in rows:
        print(f"{n:22}{(f'{f:.1f}' if f is not None else '-'):>12}{(f'{m:.1f}' if m is not None else '-'):>12}{(f'{x:.1f}' if x is not None else '-'):>10} {note}")
    for c in cold:
        f = c["first_ms"]
        print(f"cold {c['endpoint']:17} day {c['day']:<4}{(f'{f:.1f}' if f is not None else '-'):>12} {c['note']}")
    if a.out:
        print(f"written: {a.out}")


if __name__ == "__main__":
    main()
