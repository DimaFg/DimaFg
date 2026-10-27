"""Структурированные JSON-логи с request_id. Персональные данные в логи не пишутся."""

import contextvars
import json
import logging
import sys
from datetime import UTC, datetime

request_id_var: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "request_id", default=None
)


# Поля заявки и секреты не должны попадать в логи даже по ошибке (ТЗ, раздел 14).
PERSONAL_KEYS = {
    "name",
    "contact",
    "contact_normalized",
    "message",
    "internal_note",
    "email",
    "phone",
    "text",
}
SECRET_KEY_PARTS = ("token", "password", "secret", "credential", "authorization", "cookie")


def redact(fields: dict) -> dict:
    clean = {}
    for key, value in fields.items():
        lowered = key.lower()
        if lowered in PERSONAL_KEYS or any(part in lowered for part in SECRET_KEY_PARTS):
            clean[key] = "[redacted]"
        elif isinstance(value, dict):
            clean[key] = redact(value)
        else:
            clean[key] = value
    return clean


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts": datetime.fromtimestamp(record.created, UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        if rid := request_id_var.get():
            payload["request_id"] = rid
        payload.update(redact(getattr(record, "extra_fields", {})))
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False, default=str)


def configure_logging(level: str = "INFO") -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers[:] = [handler]
    root.setLevel(level)
    # access-лог uvicorn дублирует наш middleware и содержит query string
    logging.getLogger("uvicorn.access").disabled = True


def log_event(logger: logging.Logger, msg: str, level: int = logging.INFO, **fields) -> None:
    logger.log(level, msg, extra={"extra_fields": fields})
