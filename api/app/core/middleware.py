import logging
import re
import time
import uuid

from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.core.logging import log_event, request_id_var

log = logging.getLogger("app.http")
_VALID_REQUEST_ID = re.compile(r"^[A-Za-z0-9._-]{8,64}$")


class RequestContextMiddleware:
    """Присваивает request_id, ограничивает размер тела и пишет access-лог без query string."""

    def __init__(self, app: ASGIApp, max_body_bytes: int):
        self.app = app
        self.max_body_bytes = max_body_bytes

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers = dict(scope.get("headers") or [])
        incoming = headers.get(b"x-request-id", b"").decode("latin-1")
        request_id = incoming if _VALID_REQUEST_ID.match(incoming) else uuid.uuid4().hex
        scope.setdefault("state", {})["request_id"] = request_id
        token = request_id_var.set(request_id)
        started = time.perf_counter()
        status_holder = {"status": 500}

        async def send_wrapper(message: Message) -> None:
            if message["type"] == "http.response.start":
                status_holder["status"] = message["status"]
                message.setdefault("headers", []).append((b"x-request-id", request_id.encode()))
            await send(message)

        try:
            content_length = headers.get(b"content-length")
            if (
                content_length is not None
                and content_length.isdigit()
                and int(content_length) > self.max_body_bytes
            ):
                await self._too_large(scope, receive, send_wrapper)
                return
            received = 0

            async def limited_receive() -> Message:
                nonlocal received
                message = await receive()
                if message["type"] == "http.request":
                    received += len(message.get("body", b""))
                    if received > self.max_body_bytes:
                        raise _BodyTooLarge
                return message

            try:
                await self.app(scope, limited_receive, send_wrapper)
            except _BodyTooLarge:
                await self._too_large(scope, receive, send_wrapper)
        finally:
            log_event(
                log,
                "request",
                method=scope["method"],
                path=scope["path"],
                status=status_holder["status"],
                duration_ms=round((time.perf_counter() - started) * 1000, 1),
            )
            request_id_var.reset(token)

    @staticmethod
    async def _too_large(scope: Scope, receive: Receive, send: Send) -> None:
        from starlette.requests import Request

        from app.core.errors import error_response

        response = error_response(
            Request(scope, receive), 413, "payload_too_large", "Слишком большой запрос."
        )
        await response(scope, receive, send)


class _BodyTooLarge(Exception):
    pass
