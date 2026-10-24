"""مصنع التطبيق ``create_app``: starlette + مسارات ``/api`` + ملفات الواجهة الثابتة من ``src/frontend/dist/``."""
from __future__ import annotations

import contextlib
import logging
import threading
import time

from starlette.applications import Starlette
from starlette.exceptions import HTTPException
from starlette.middleware import Middleware
from starlette.responses import HTMLResponse, Response
from starlette.routing import Mount, Route
from starlette.staticfiles import StaticFiles
from starlette.types import ASGIApp, Receive, Scope, Send

from .errors import api_error_handler, ApiError, error_response, http_handler, unhandled_handler
from .repository import Repository
from .routes import instructor as instructor_routes
from .routes import learner as learner_routes
from .routes import meta as meta_routes
from .services.explanation import ExplanationService
from .services.instructor import InstructorService
from .services.replay import ReplayService
from .settings import Settings

log = logging.getLogger("backend")


class Services:
    """حاوية الخدمات (حقن بسيط): كل مسار يأخذها بالإغلاق، فيمكن للاختبارات تركيب محرك مختلف."""

    def __init__(self, settings: Settings, engine=None):
        self.settings = settings
        self.repo = Repository(settings, engine)
        self.replay = ReplayService(self.repo, settings)
        self.explanation = ExplanationService(self.replay)
        self.instructor = InstructorService(self.repo, self.replay, settings)
        self.started = time.time()
        self.warm: dict = {"enabled": settings.warm, "state": "idle" if not settings.warm else "pending"}

    def run_warmup(self) -> None:
        """تسخين (بترتيب ما تستعمله الواجهة): قوائم العروض → أول تسجيل → توصية عند اليوم (+ لقطة المدرّس)."""
        st, s = self.warm, self.settings
        st.update(state="running", started=time.time(), done=[], total=len(s.warm_days))
        try:
            from src.ml import serving      # D-68: خطّاف التسخين/التحفيظ الدائم إن وفّره serving (يُستعمل حين يتوفر)
            hook = getattr(serving, "warm", None)
            if callable(hook):
                t = time.time()
                try:
                    hook(s.warm_presentation, list(s.warm_days))
                except TypeError:
                    hook(s.warm_presentation)
                st["serving_warm_seconds"] = round(time.time() - t, 2)
            self.replay.presentations()
            frame = self.replay._registration_frame(s.warm_presentation)
            sid = int(frame.iloc[0]["id_student"])
            for day in s.warm_days:
                t = time.time()
                self.replay.raw_recs(s.warm_presentation, sid, day, "A")
                if s.instructor_enabled and day >= 56:
                    self.instructor.snapshot(s.warm_presentation, day)
                st["done"].append({"presentation": s.warm_presentation, "day": day, "seconds": round(time.time() - t, 2)})
            st.update(state="done", seconds=round(time.time() - st["started"], 2))
        except Exception as e:           # التسخين تحسيني: فشله لا يوقف الخدمة
            log.exception("warm-up failed")
            st.update(state="failed", error=str(e))


class TimingMiddleware:
    """يضيف ``Server-Timing`` و``X-Response-Time-ms`` (للقياس في README و``bench.py``)."""

    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        t0 = time.perf_counter()

        async def wrapped(message):
            if message["type"] == "http.response.start":
                ms = (time.perf_counter() - t0) * 1000
                hdr = list(message.get("headers", []))
                hdr.append((b"server-timing", f"app;dur={ms:.1f}".encode()))
                hdr.append((b"x-response-time-ms", f"{ms:.1f}".encode()))
                message["headers"] = hdr
            await send(message)
        await self.app(scope, receive, wrapped)


_HIDE_INSTRUCTOR = b'<style>a[href*="instructor"]{display:none!important}</style>'


class FrontendFiles(StaticFiles):
    """ملفات الواجهة؛ مع ``--no-instructor``: صفحة المدرّس 404 وتُخفى روابطها بقاعدة CSS تُحقن في كل صفحة HTML."""

    def __init__(self, *a, instructor_enabled: bool = True, **kw):
        super().__init__(*a, **kw)
        self.instructor_enabled = instructor_enabled

    async def get_response(self, path: str, scope: Scope) -> Response:
        if not self.instructor_enabled and path.rstrip("/").split("/")[-1] in ("instructor.html", "instructor"):
            raise HTTPException(404)
        resp = await super().get_response(path, scope)
        if (not self.instructor_enabled and resp.status_code == 200
                and resp.headers.get("content-type", "").startswith("text/html") and hasattr(resp, "path")):
            with open(resp.path, "rb") as fh:
                body = fh.read().replace(b"</head>", _HIDE_INSTRUCTOR + b"</head>", 1)
            return HTMLResponse(body, headers={"Cache-Control": "no-cache"})
        return resp


def create_app(settings: Settings | None = None, engine=None) -> Starlette:
    settings = settings or Settings()
    sv = Services(settings, engine)
    if settings.host not in ("127.0.0.1", "localhost", "::1"):   # D-66: لا مصادقة؛ الربط الخارجي خارج التصميم
        log.warning("الربط على %s: الخدمة بلا مصادقة (عرض توضيحي بلا أمان وصول، D-66)", settings.host)

    routes: list = []
    routes += meta_routes.routes(sv)
    routes += learner_routes.routes(sv)
    routes += instructor_routes.routes(sv) if settings.instructor_enabled else instructor_routes.disabled_routes()

    async def api_not_found(request):
        return error_response(404, "not_found")
    routes.append(Route("/api/{path:path}", api_not_found))

    dist = settings.frontend_dist
    if dist.is_dir() and (dist / "index.html").exists():
        routes.append(Mount("/", app=FrontendFiles(directory=str(dist), html=True, instructor_enabled=settings.instructor_enabled), name="frontend"))
    else:
        async def no_frontend(request):
            return HTMLResponse("<meta charset=utf-8><p dir=rtl>الواجهة غير مبنية: شغّل <code>bash src/frontend/build.sh</code>. "
                                "مسارات <code>/api/*</code> تعمل.</p>", status_code=503)
        routes.append(Route("/", no_frontend))

    @contextlib.asynccontextmanager
    async def lifespan(app):
        if settings.warm:
            threading.Thread(target=sv.run_warmup, name="warmup", daemon=True).start()
        yield

    app = Starlette(routes=routes, lifespan=lifespan, middleware=[Middleware(TimingMiddleware)],
                    exception_handlers={ApiError: api_error_handler, HTTPException: http_handler, Exception: unhandled_handler})
    app.state.services = sv
    return app
