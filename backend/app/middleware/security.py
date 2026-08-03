from starlette.datastructures import Headers, MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.config import settings


class PayloadTooLarge(Exception):
    pass


async def _send_json_error(
    send: Send,
    status_code: int,
    body: bytes,
) -> None:
    await send({
        "type": "http.response.start",
        "status": status_code,
        "headers": [
            (b"content-type", b"application/json; charset=utf-8"),
            (b"content-length", str(len(body)).encode("ascii")),
        ],
    })
    await send({"type": "http.response.body", "body": body})


class RequestBodyLimitMiddleware:
    """Bound JSON bodies before Starlette/FastAPI materializes them in memory."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(
        self,
        scope: Scope,
        receive: Receive,
        send: Send,
    ) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers = Headers(scope=scope)
        content_type = headers.get("content-type", "").split(";", 1)[0].strip().lower()
        is_firmware_upload = (
            scope["path"] == "/api/v1/ota/firmware"
            and content_type == "multipart/form-data"
        )
        if is_firmware_upload:
            await self.app(scope, receive, send)
            return

        limit = settings.JSON_MAX_REQUEST_BYTES
        content_length = headers.get("content-length")
        if content_length is not None:
            try:
                declared_size = int(content_length)
            except ValueError:
                await _send_json_error(send, 400, b'{"detail":"Content-Length invalid"}')
                return
            if declared_size < 0:
                await _send_json_error(send, 400, b'{"detail":"Content-Length invalid"}')
                return
            if declared_size > limit:
                await _send_json_error(send, 413, b'{"detail":"Request body too large"}')
                return

        received = 0
        response_started = False

        async def limited_receive() -> Message:
            nonlocal received
            message = await receive()
            if message["type"] == "http.request":
                received += len(message.get("body", b""))
                if received > limit:
                    raise PayloadTooLarge
            return message

        async def tracked_send(message: Message) -> None:
            nonlocal response_started
            if message["type"] == "http.response.start":
                response_started = True
            await send(message)

        try:
            await self.app(scope, limited_receive, tracked_send)
        except PayloadTooLarge:
            if response_started:
                raise
            await _send_json_error(send, 413, b'{"detail":"Request body too large"}')


class SecurityHeadersMiddleware:
    """Apply API-safe response headers without imposing a brittle global CSP."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(
        self,
        scope: Scope,
        receive: Receive,
        send: Send,
    ) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def send_with_headers(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = MutableHeaders(scope=message)
                headers["X-Content-Type-Options"] = "nosniff"
                headers["X-Frame-Options"] = "DENY"
                headers["Referrer-Policy"] = "no-referrer"
                headers["Permissions-Policy"] = (
                    "camera=(), microphone=(), geolocation=()"
                )
                if not settings.DEBUG:
                    headers["Strict-Transport-Security"] = (
                        "max-age=31536000; includeSubDomains"
                    )
            await send(message)

        await self.app(scope, receive, send_with_headers)
