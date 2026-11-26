from fastapi import Request
from fastapi.responses import JSONResponse
from loguru import logger


class APIError(Exception):
    status_code = 500
    error_code = "INTERNAL_ERROR"
    default_message = "An unexpected error occurred"

    def __init__(self, message: str | None = None) -> None:
        super().__init__(message or self.default_message)


class OpenProjectAuthError(APIError):
    status_code = 401
    error_code = "OPENPROJECT_AUTH_ERROR"
    default_message = "OpenProject authentication failed"


class SessionNotFoundError(APIError):
    status_code = 401
    error_code = "SESSION_NOT_FOUND"
    default_message = "Session not found"


class IntentValidationError(APIError):
    status_code = 422
    error_code = "INTENT_VALIDATION_ERROR"
    default_message = "Intent validation failed"


class NormalizationError(APIError):
    status_code = 502
    error_code = "NORMALIZATION_ERROR"
    default_message = "Intent normalization failed"


class OpenProjectAPIError(APIError):
    status_code = 502
    error_code = "OPENPROJECT_API_ERROR"

    def __init__(
        self, status_code: int, response_body: str, message: str | None = None
    ) -> None:
        self.upstream_status_code = status_code
        self.response_body = response_body
        super().__init__(message or "OpenProject API request failed")


async def api_error_handler(_: Request, exc: APIError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.error_code,
                "message": str(exc),
            }
        },
    )


async def unhandled_exception_handler(_: Request, exc: Exception) -> JSONResponse:
    logger.opt(exception=exc).error("Unhandled exception")
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred",
            }
        },
    )
