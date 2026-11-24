import sys
import time

from loguru import logger
from starlette.types import ASGIApp, Message, Receive, Scope, Send


def configure_logging() -> None:
    logger.remove()
    logger.add(sys.stdout, serialize=True, level="INFO")


class RequestLoggingMiddleware:
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

        start_time = time.perf_counter()
        status_code = 500

        async def send_with_status(message: Message) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
            await send(message)

        try:
            await self.app(scope, receive, send_with_status)
        finally:
            elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
            fields = {
                "method": scope["method"],
                "path": scope["path"],
                "status_code": status_code,
                "response_time_ms": elapsed_ms,
            }
            session_id = scope.get("state", {}).get("session_id")
            if session_id is None:
                session_id = next(
                    (
                        value.decode("latin-1")
                        for key, value in scope["headers"]
                        if key.lower() == b"x-session-id"
                    ),
                    None,
                )
            if session_id is not None:
                fields["session_id"] = session_id
            logger.bind(**fields).info("http_request")
