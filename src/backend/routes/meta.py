"""/api/health و/api/meta و/api/presentations و/api/registrations."""
from __future__ import annotations

import time

from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import Route

from .. import SCHEMA_VERSION, __version__
from ..schemas import ComponentInfo, Health, Meta, PresentationList, RegistrationsIn, parse_in
from ..services.labels import comp_id, comp_label
from ..settings import MODEL_CUTS, RISK_CUTS, SNAPSHOT_GRID
from .common import json_response, respond


def routes(sv) -> list[Route]:
    async def health(request: Request) -> Response:
        return json_response(Health(status="ok", run_id=sv.repo.run_id, uptime_s=int(time.time() - sv.started),
                                    instructor_enabled=sv.settings.instructor_enabled, warm=dict(sv.warm)))

    async def meta(request: Request) -> Response:
        def work() -> Meta:
            sv.repo.require_artifacts()
            fz = sv.repo.engine.frozen
            modal = fz.get("initial_weights_modal", {})
            fp, files = sv.repo.data_fingerprint()
            g = sv.repo.git()
            return Meta(
                schema_version=SCHEMA_VERSION, version=__version__, run_id=sv.repo.run_id, git_commit=g["commit"],
                git_dirty=g["dirty"], freeze_tag=g["freeze_tag"], data_fingerprint=fp, data_files=files,
                components=[ComponentInfo(id=comp_id(m), label=comp_label(m), weight=round(float(modal.get(m, 0.0)), 4))
                            for m in fz["components"]],
                snapshot_grid=list(SNAPSHOT_GRID), cutoffs=list(MODEL_CUTS), risk_cutoffs=list(RISK_CUTS),
                presentations=[p.id for p in sv.replay.presentations() if p.status == "published"],
                instructor_enabled=sv.settings.instructor_enabled, frozen_at_commit=sv.repo.frozen_commit(),
                notes=["أوزان المكوّنات المعروضة هي الأوزان الأولية المجمَّدة (منوال)؛ لكل (عرض، قطع) أوزان خاصة تظهر في كل توصية.",
                       "إعادة تشغيل على بيانات تاريخية (OULAD 2013) بلا جمع حي؛ لا أرقام تقييم تُشتق من الخدمة (D-49)."])
        return await respond(work)

    async def presentations(request: Request) -> Response:
        return await respond(lambda: PresentationList(sv.replay.presentations()))

    async def registrations(request: Request) -> Response:
        def work():
            q = parse_in(RegistrationsIn, dict(request.query_params))
            return sv.replay.registrations(q.presentation, q.q, q.limit, q.offset)
        return await respond(work)

    return [Route("/api/health", health), Route("/api/meta", meta), Route("/api/presentations", presentations),
            Route("/api/registrations", registrations)]
