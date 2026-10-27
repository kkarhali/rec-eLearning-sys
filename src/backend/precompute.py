"""الحساب المسبق لاختيار العناقيد لكل أيام العرض (NFR-01):

    python3 -m src.backend.precompute [--presentation FFF_2013J ...] [--all] [--jobs 4] [--days 0-268]

يملأ الذاكرة الدائمة ``data/cache/serving_clusters`` (خارج git) باختيار العناقيد عند كل يوم t من 0 إلى طول العرض، بالحساب
نفسه الذي يجريه الطلب عند ذلك اليوم (``serving.Engine.precompute_clusters``؛ D-68). بعده لا يحسب الطلب البارد لأي يوم
اختيار العناقيد، فيقرؤه من الملف. والأيام المحسوبة سابقاً ببصمة مطابقة تُتخطّى، فإعادة الأمر بعد اكتماله تكاد لا تكلف شيئاً.
لا يمس الأمر عروض 2014 (يرفضها الحاجز) ولا أي ملف في ``results/``.
"""
from __future__ import annotations

import argparse
import sys
import time

from .settings import DEFAULT_PRESENTATION


def parse_days(spec: str | None):
    if not spec:
        return None
    out = set()
    for part in spec.split(","):
        if "-" in part:
            a, b = part.split("-")
            out |= set(range(int(a), int(b) + 1))
        elif part:
            out.add(int(part))
    return sorted(out)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="python3 -m src.backend.precompute",
                                 description="حساب مسبق لاختيار العناقيد لكل أيام العرض (NFR-01)")
    ap.add_argument("--presentation", action="append", help=f"يتكرر؛ الافتراضي {DEFAULT_PRESENTATION}")
    ap.add_argument("--all", action="store_true", help="كل عروض التطوير التسعة (2013)")
    ap.add_argument("--jobs", type=int, default=4, help="عدد العمليات المتوازية (الافتراضي 4)")
    ap.add_argument("--days", default=None, help="أيام أو مجالات مثل 0-90,120؛ الافتراضي من 0 إلى طول العرض")
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args(argv)
    from src.ml import data, serving
    names = list(data.DEV_PRESENTATIONS) if a.all else (a.presentation or [DEFAULT_PRESENTATION])
    bad = [n for n in names if n not in data.DEV_PRESENTATIONS]
    if bad:
        print(f"عروض غير مسموحة أو غير معروفة: {bad} (عروض 2014 مقفلة، D-09)", file=sys.stderr)
        return 2
    eng = serving.engine()
    for n in names:
        t = time.time()

        def progress(i, total, day, sec, n=n):
            if not a.quiet and (i == total or i % 10 == 0):
                print(f"{n}: {i}/{total} (اليوم {day}، {sec:.1f} ث)", flush=True)
        r = eng.precompute_clusters(n, parse_days(a.days), jobs=a.jobs, progress=progress)
        print(f"{n}: {r['days']} يوماً؛ حُسب {r['computed']} وكان {r['already_cached']} محسوباً؛ "
              f"{r['jobs']} عمليات؛ {time.time() - t:.0f} ث", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
