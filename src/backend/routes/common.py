"""مساعدات المسارات: تشغيل العمل المتزامن في خيط، وتحويل الأخطاء إلى الصيغة الموحدة."""
from __future__ import annotations

import logging
from typing import Callable

from pydantic import BaseModel, ValidationError
from starlette.concurrency import run_in_threadpool
from starlette.responses import Response

from ..errors import ApiError, error_response, validation_details, MESSAGES_AR

log = logging.getLogger("backend")


def json_response(model: BaseModel) -> Response:
    return Response(model.model_dump_json(), media_type="application/json", headers={"Cache-Control": "no-store"})


async def respond(work: Callable[[], BaseModel]) -> Response:
    """يشغّل ``work`` في خيط (الحساب الأول ≈10 ث لا يحجب /api/health) ويحوّل الأخطاء المعروفة."""
    from src.ml.data import ConfirmatoryAccessError
    try:
        return json_response(await run_in_threadpool(work))
    except ApiError as e:
        return error_response(e.status, e.code, e.message, e.details)
    except ValidationError as e:
        return error_response(422, "validation_error", MESSAGES_AR["validation_error"], validation_details(e))
    except ConfirmatoryAccessError:
        return error_response(409, "confirmatory_locked")
    except FileNotFoundError as e:
        return error_response(503, "artifacts_missing", details={"missing": str(e)})
    except Exception:
        log.exception("unhandled error")
        return error_response(500, "internal_error")
