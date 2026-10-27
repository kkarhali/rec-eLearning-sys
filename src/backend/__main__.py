"""``python3 -m src.backend [--host H] [--port P] [--no-instructor] [--warm] [--precompute-clusters]``"""
from __future__ import annotations

import argparse

from .settings import DEFAULT_PRESENTATION, WARM_DAYS, Settings


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(prog="python3 -m src.backend", description="خدمة API لنظام التوصية (إعادة تشغيل بيانات OULAD 2013)")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8000)
    ap.add_argument("--no-instructor", action="store_true", help="يعطّل مسارات /api/instructor/* وصفحة المدرّس (R-C5)")
    ap.add_argument("--warm", action="store_true", help="تسخين في خيط خلفي: توصية (+لقطة المدرّس) للعرض الافتراضي والأيام --warm-days")
    ap.add_argument("--warm-presentation", default=DEFAULT_PRESENTATION)
    ap.add_argument("--warm-days", default=",".join(map(str, WARM_DAYS)), help="أيام مفصولة بفواصل؛ الافتراضي: 75 و56 والقطوع 70/126/182 و112")
    ap.add_argument("--warm-weekly", action="store_true", help="يضيف شبكة أسبوعية (7، 14، … ≤ 266)؛ ≈ 10 ث لكل يوم، فتستغرق عدة دقائق")
    ap.add_argument("--precompute-clusters", action="store_true",
                    help="بعد التسخين: حساب اختيار العناقيد لكل أيام العرض في عمليات خلفية وحفظه (NFR-01)؛ "
                         "يمكن تشغيله مسبقاً بالأمر python3 -m src.backend.precompute")
    ap.add_argument("--precompute-jobs", type=int, default=2)
    ap.add_argument("--log-level", default="info")
    a = ap.parse_args(argv)
    import uvicorn
    days = [int(x) for x in a.warm_days.split(",") if x]
    if a.warm_weekly:
        days += [d for d in range(56, 267, 7) if d not in days]
    from .app import create_app
    s = Settings(host=a.host, port=a.port, instructor_enabled=not a.no_instructor, warm=a.warm or a.precompute_clusters,
                 warm_presentation=a.warm_presentation, warm_days=tuple(days),
                 precompute_clusters=a.precompute_clusters, precompute_jobs=a.precompute_jobs,
                 log_level=a.log_level)
    uvicorn.run(create_app(s), host=s.host, port=s.port, log_level=s.log_level)


if __name__ == "__main__":
    main()
