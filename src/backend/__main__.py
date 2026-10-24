"""``python3 -m src.backend [--host H] [--port P] [--no-instructor] [--warm]``"""
from __future__ import annotations

import argparse

from .settings import DEFAULT_DAY, DEFAULT_PRESENTATION, Settings


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(prog="python3 -m src.backend", description="خدمة API لنظام التوصية (إعادة تشغيل بيانات OULAD 2013)")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8000)
    ap.add_argument("--no-instructor", action="store_true", help="يعطّل مسارات /api/instructor/* وصفحة المدرّس (R-C5)")
    ap.add_argument("--warm", action="store_true", help="تسخين في خيط خلفي: توصية (+لقطة المدرّس) للعرض الافتراضي والأيام --warm-days")
    ap.add_argument("--warm-presentation", default=DEFAULT_PRESENTATION)
    ap.add_argument("--warm-days", default=str(DEFAULT_DAY), help="أيام مفصولة بفواصل (الافتراضي 75 ⇒ قطع النموذج 70)")
    ap.add_argument("--log-level", default="info")
    a = ap.parse_args(argv)
    import uvicorn
    from .app import create_app
    s = Settings(host=a.host, port=a.port, instructor_enabled=not a.no_instructor, warm=a.warm,
                 warm_presentation=a.warm_presentation, warm_days=tuple(int(x) for x in a.warm_days.split(",") if x),
                 log_level=a.log_level)
    uvicorn.run(create_app(s), host=s.host, port=s.port, log_level=s.log_level)


if __name__ == "__main__":
    main()
