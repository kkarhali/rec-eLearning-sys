"""صيغة الخطأ الموحدة ``{"error": {"code", "message", "details"}}`` (الوثيقة 03 §8.2، جدول 15)."""
from __future__ import annotations

import logging

from pydantic import ValidationError
from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.responses import JSONResponse

log = logging.getLogger("backend")

MESSAGES_AR = {
    "validation_error": "مدخلات غير صالحة.",
    "day_out_of_range": "اليوم خارج مدى العرض.",
    "presentation_not_found": "العرض غير موجود.",
    "registration_not_found": "التسجيل غير موجود في هذا العرض.",
    "item_not_in_list": "التفسير غير متاح لهذا المورد: ليس ضمن أفضل 20 توصية لهذا التسجيل واليوم.",
    "confirmatory_locked": "عروض 2014 من مجموعة التأكيد؛ نتائجها في الرسالة ولا تُعرض في الواجهة.",
    "instructor_disabled": "لوحة المدرّس معطّلة في هذا التشغيل (--no-instructor).",
    "day_before_first_snapshot": "لا تقدير للوحة المدرّس قبل أول يوم متاح.",
    "not_found": "المسار غير موجود.",
    "method_not_allowed": "الطريقة غير مسموحة؛ كل مسارات الواجهة للقراءة (GET) فقط.",
    "artifacts_missing": "مخرجات القطوع أو التركيبة المجمَّدة غير موجودة؛ شغّل: python3 -m src.ml.experiments.build_artifacts",
    "internal_error": "حدث خطأ داخلي غير متوقع.",
}


class ApiError(Exception):
    def __init__(self, status: int, code: str, message: str | None = None, details: dict | None = None):
        super().__init__(code)
        self.status = status
        self.code = code
        self.message = message or MESSAGES_AR.get(code, code)
        self.details = details or {}


def error_response(status: int, code: str, message: str | None = None, details: dict | None = None) -> JSONResponse:
    body = {"error": {"code": code, "message": message or MESSAGES_AR.get(code, code), "details": details or {}}}
    return JSONResponse(body, status_code=status, headers={"Cache-Control": "no-store"})


def validation_details(exc: ValidationError) -> dict:
    errs = []
    for e in exc.errors():
        loc = ".".join(str(x) for x in e.get("loc", ()))
        errs.append({"field": loc, "reason": e.get("msg", ""), "type": e.get("type", "")})
    return {"errors": errs}


async def api_error_handler(request: Request, exc: ApiError) -> JSONResponse:
    return error_response(exc.status, exc.code, exc.message, exc.details)


async def validation_handler(request: Request, exc: ValidationError) -> JSONResponse:
    return error_response(422, "validation_error", MESSAGES_AR["validation_error"], validation_details(exc))


async def http_handler(request: Request, exc: HTTPException) -> JSONResponse:
    if exc.status_code == 404:
        return error_response(404, "not_found")
    if exc.status_code == 405:
        return error_response(405, "method_not_allowed")
    return error_response(exc.status_code, "http_error", str(exc.detail))


async def unhandled_handler(request: Request, exc: Exception) -> JSONResponse:
    # أخطاء الإتاحة تأتي من src.ml: 2014 محجوب (D-09)، ومخرجات القطوع مفقودة
    from src.ml.data import ConfirmatoryAccessError
    if isinstance(exc, ConfirmatoryAccessError):
        return error_response(409, "confirmatory_locked")
    if isinstance(exc, FileNotFoundError):
        return error_response(503, "artifacts_missing", details={"missing": str(exc)})
    log.exception("unhandled error on %s", request.url.path)
    return error_response(500, "internal_error")
