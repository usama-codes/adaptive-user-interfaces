import json
from io import StringIO

import pytest
from fastapi.testclient import TestClient
from loguru import logger

from adaptive_ui_service.app.core import exceptions
from adaptive_ui_service.app.main import create_app


@pytest.mark.parametrize(
    ("error", "status_code", "error_code", "message"),
    [
        (
            exceptions.OpenProjectAuthError(),
            401,
            "OPENPROJECT_AUTH_ERROR",
            "OpenProject authentication failed",
        ),
        (
            exceptions.SessionNotFoundError(),
            401,
            "SESSION_NOT_FOUND",
            "Session not found",
        ),
        (
            exceptions.IntentValidationError(),
            422,
            "INTENT_VALIDATION_ERROR",
            "Intent validation failed",
        ),
        (
            exceptions.OpenProjectAPIError(500, "private upstream response"),
            502,
            "OPENPROJECT_API_ERROR",
            "OpenProject API request failed",
        ),
    ],
)
def test_typed_errors_return_standardized_responses(
    error: exceptions.APIError,
    status_code: int,
    error_code: str,
    message: str,
) -> None:
    app = create_app()

    def raise_error() -> None:
        raise error

    app.add_api_route("/test-error", raise_error)
    with TestClient(app) as client:
        response = client.get("/test-error")

    assert response.status_code == status_code
    assert response.json() == {
        "error": {
            "code": error_code,
            "message": message,
        }
    }


def test_unhandled_error_returns_safe_standardized_response() -> None:
    app = create_app()
    stream = StringIO()
    sink_id = logger.add(stream, serialize=True, level="INFO")

    def raise_error() -> None:
        raise RuntimeError("private stack trace detail")

    app.add_api_route("/test-error", raise_error)
    try:
        with TestClient(app, raise_server_exceptions=False) as client:
            response = client.get(
                "/test-error",
                headers={"x-session-id": "session-500"},
            )
    finally:
        logger.remove(sink_id)

    assert response.status_code == 500
    assert response.json() == {
        "error": {
            "code": "INTERNAL_ERROR",
            "message": "An unexpected error occurred",
        }
    }
    assert "private stack trace detail" not in response.text
    assert "Traceback" not in response.text

    log_entries = [
        json.loads(line)["record"] for line in stream.getvalue().splitlines()
    ]
    request_log = next(
        entry for entry in log_entries if entry["message"] == "http_request"
    )
    assert request_log["extra"]["status_code"] == 500
    assert request_log["extra"]["session_id"] == "session-500"
