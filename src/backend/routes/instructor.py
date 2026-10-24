"""مسارات المدرّس (D-22): نظرة عامة وعناقيد وجدول متعلمين وملف متعلم. تُسجَّل فقط إن لم يُمرَّر ``--no-instructor``."""
from __future__ import annotations

from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import Route

from ..errors import error_response
from ..schemas import LearnerIn, LearnersIn, OverviewIn, parse_in, parse_registration
from .common import respond


def routes(sv) -> list[Route]:
    async def overview(request: Request) -> Response:
        def work():
            q = parse_in(OverviewIn, dict(request.query_params))
            return sv.instructor.overview(q.presentation, q.day)
        return await respond(work)

    async def clusters(request: Request) -> Response:
        def work():
            q = parse_in(OverviewIn, dict(request.query_params))
            return sv.instructor.clusters(q.presentation, q.day)
        return await respond(work)

    async def learners(request: Request) -> Response:
        def work():
            q = parse_in(LearnersIn, dict(request.query_params))
            return sv.instructor.learners(q.presentation, q.day, q.cluster, q.risk, q.sort, q.limit, q.offset)
        return await respond(work)

    async def learner(request: Request) -> Response:
        def work():
            pres, sid = parse_registration(request.path_params["registration"])
            q = parse_in(LearnerIn, dict(request.query_params))
            sv.instructor.gate(pres, q.day)
            return sv.instructor.learner(pres, sid, q.day)
        return await respond(work)

    return [Route("/api/instructor/overview", overview), Route("/api/instructor/clusters", clusters),
            Route("/api/instructor/learners", learners), Route("/api/instructor/learner/{registration}", learner)]


def disabled_routes() -> list[Route]:
    async def disabled(request: Request) -> Response:
        return error_response(404, "instructor_disabled")
    return [Route("/api/instructor/{path:path}", disabled)]
