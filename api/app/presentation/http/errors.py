"""Единый формат ошибок API:

{"error": {"code": "...", "message": "...", "fields": {"name": "..."}, "request_id": "..."}}
"""

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.application.leads.create import RateLimitError, UnknownServiceError

log = logging.getLogger("app.errors")


class ErrorBody(BaseModel):
    code: str
    message: str
    fields: dict[str, str] = {}
    request_id: str | None = None


class ErrorResponse(BaseModel):
    error: ErrorBody


class ApiError(Exception):
    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        fields: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
    ):
        self.status_code = status_code
        self.code = code
        self.message = message
        self.fields = fields or {}
        self.headers = headers


def error_response(
    request: Request,
    status_code: int,
    code: str,
    message: str,
    fields: dict[str, str] | None = None,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    body = ErrorResponse(
        error=ErrorBody(
            code=code,
            message=message,
            fields=fields or {},
            request_id=getattr(request.state, "request_id", None),
        )
    )
    return JSONResponse(body.model_dump(), status_code=status_code, headers=headers)


_HTTP_CODES = {
    400: ("bad_request", "Некорректный запрос."),
    401: ("unauthorized", "Требуется вход."),
    403: ("forbidden", "Недостаточно прав."),
    404: ("not_found", "Не найдено."),
    405: ("method_not_allowed", "Метод не поддерживается."),
    413: ("payload_too_large", "Слишком большой запрос."),
    429: ("rate_limited", "Слишком много запросов. Попробуйте позже."),
}


def _field_name(loc: tuple) -> str:
    # ("body", "contact") -> "contact"; ("query", "page") -> "page"
    parts = [str(p) for p in loc if p not in ("body", "query", "path", "header")]
    return ".".join(parts) or "__root__"


def _field_message(err: dict) -> str:
    ctx = err.get("ctx") or {}
    match err.get("type"):
        case "missing":
            return "Обязательное поле."
        case "string_too_short":
            return f"Минимум символов: {ctx.get('min_length')}."
        case "string_too_long":
            return f"Максимум символов: {ctx.get('max_length')}."
        case "extra_forbidden":
            return "Неизвестное поле."
        case "literal_error" | "enum":
            return "Недопустимое значение."
        case "value_error":
            return str(ctx.get("error") or err.get("msg"))
        case _:
            return "Некорректное значение."


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(UnknownServiceError)
    async def _unknown_service(request: Request, exc: UnknownServiceError):
        return error_response(
            request,
            422,
            "validation_error",
            "Проверьте правильность заполнения полей.",
            {"service": "Выберите услугу из списка."},
        )

    @app.exception_handler(RateLimitError)
    async def _rate_limit(request: Request, exc: RateLimitError):
        message = (
            "Мы уже получили ваши заявки и скоро ответим."
            if exc.per_contact
            else "Слишком много заявок за короткое время. Попробуйте позже или напишите в Telegram."
        )
        return error_response(
            request,
            429,
            "rate_limited",
            message,
            headers={"Retry-After": "86400" if exc.per_contact else "3600"},
        )

    @app.exception_handler(ApiError)
    async def _api_error(request: Request, exc: ApiError):
        return error_response(
            request, exc.status_code, exc.code, exc.message, exc.fields, exc.headers
        )

    @app.exception_handler(RequestValidationError)
    async def _validation(request: Request, exc: RequestValidationError):
        fields: dict[str, str] = {}
        for err in exc.errors():
            fields.setdefault(_field_name(tuple(err["loc"])), _field_message(err))
        return error_response(
            request, 422, "validation_error", "Проверьте правильность заполнения полей.", fields
        )

    @app.exception_handler(StarletteHTTPException)
    async def _http(request: Request, exc: StarletteHTTPException):
        code, message = _HTTP_CODES.get(exc.status_code, ("http_error", "Ошибка запроса."))
        return error_response(request, exc.status_code, code, message)

    @app.exception_handler(Exception)
    async def _unhandled(request: Request, exc: Exception):
        log.exception("unhandled error")
        return error_response(
            request, 500, "internal_error", "Внутренняя ошибка сервера. Попробуйте позже."
        )
