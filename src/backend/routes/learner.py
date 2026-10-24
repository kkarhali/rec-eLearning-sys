"""مسارات المتعلم: /api/recommendations و/api/explanations و/api/learner/{reg}/history.

لا خطر ولا عنقود ولا سمات حساسة في أي استجابة هنا (D-22، D-21، NFR-09)؛ يفحصه ``test_contract_no_risk``.
"""
from __future__ import annotations

from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import Route

from ..schemas import ExplanationIn, HistoryIn, RecommendationsIn, parse_in, parse_registration
from .common import respond


def routes(sv) -> list[Route]:
    async def recommendations(request: Request) -> Response:
        def work():
            q = parse_in(RecommendationsIn, dict(request.query_params))
            pres, sid = parse_registration(q.registration)
            return sv.replay.recommendation(pres, sid, q.day, q.k, q.task)
        return await respond(work)

    async def explanations(request: Request) -> Response:
        def work():
            pres, sid = parse_registration(request.path_params["registration"])
            q = parse_in(ExplanationIn, dict(request.query_params))
            return sv.explanation.explain(pres, sid, int(request.path_params["id_site"]), q.day, q.task)
        return await respond(work)

    async def history(request: Request) -> Response:
        def work():
            pres, sid = parse_registration(request.path_params["registration"])
            q = parse_in(HistoryIn, dict(request.query_params))
            return sv.replay.history(pres, sid, q.day, q.window)
        return await respond(work)

    return [Route("/api/recommendations", recommendations),
            Route("/api/explanations/{registration}/{id_site:int}", explanations),
            Route("/api/learner/{registration}/history", history)]
