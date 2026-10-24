"""قياس الأزمنة على خادم يعمل: ``python3 -m src.backend.bench [base_url] [--day 75] [--presentation FFF_2013J] [--n 20]``.

يطبع لكل مسار: زمن الطلب الأول (يشمل أي حساب بارد) ووسيط/أقصى n طلباً لاحقاً. شغّله على خادم بلا ``--warm`` ثم على خادم
بتسخين لتسجيل الفرق (انظر README).
"""
from __future__ import annotations

import argparse
import json
import statistics
import time
import urllib.request


def get(base: str, path: str):
    t = time.perf_counter()
    with urllib.request.urlopen(base + path, timeout=300) as r:
        body = r.read()
    return (time.perf_counter() - t) * 1000, json.loads(body)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("base", nargs="?", default="http://127.0.0.1:8000")
    ap.add_argument("--day", type=int, default=75)
    ap.add_argument("--presentation", default="FFF_2013J")
    ap.add_argument("--n", type=int, default=20)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    P, D = a.presentation, a.day
    reg = get(a.base, f"/api/registrations?presentation={P}&limit=1")[1]["items"][0]["registration"]
    paths = [("health", "/api/health"), ("meta", "/api/meta"), ("presentations", "/api/presentations"),
             ("registrations", f"/api/registrations?presentation={P}&limit=100"),
             ("recommendations", f"/api/recommendations?registration={reg}&day={D}&k=10"),
             ("history", f"/api/learner/{reg}/history?day={D}"),
             ("instructor/overview", f"/api/instructor/overview?presentation={P}&day={D}"),
             ("instructor/clusters", f"/api/instructor/clusters?presentation={P}&day={D}"),
             ("instructor/learners", f"/api/instructor/learners?presentation={P}&day={D}&limit=100&sort=-risk"),
             ("instructor/learner", f"/api/instructor/learner/{reg}?day={D}")]
    rows = []
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
        if name == "recommendations":
            f2, _ = get(a.base, paths_extra[1])
            ts = [get(a.base, paths_extra[1])[0] for _ in range(a.n)]
            rows.append(("explanations", f2, statistics.median(ts), max(ts), ""))
    if a.json:
        print(json.dumps([dict(zip(("endpoint", "first_ms", "median_ms", "max_ms", "note"), r)) for r in rows], ensure_ascii=False))
        return
    print(f"{'endpoint':22}{'first(ms)':>12}{'median(ms)':>12}{'max(ms)':>10}")
    for n, f, m, x, note in rows:
        print(f"{n:22}{(f'{f:.1f}' if f is not None else '-'):>12}{(f'{m:.1f}' if m is not None else '-'):>12}{(f'{x:.1f}' if x is not None else '-'):>10} {note}")


if __name__ == "__main__":
    main()
