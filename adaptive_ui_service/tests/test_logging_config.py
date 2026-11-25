import json
from io import StringIO

from fastapi.testclient import TestClient
from loguru import logger

from adaptive_ui_service.app.main import create_app


def test_request_logs_are_json_and_include_request_details() -> None:
    app = create_app()
    stream = StringIO()
    sink_id = logger.add(stream, serialize=True, level="INFO")

    try:
        with TestClient(app) as client:
            response = client.get(
                "/health",
                headers={"x-session-id": "session-123"},
            )
    finally:
        logger.remove(sink_id)

    log_entry = json.loads(stream.getvalue().splitlines()[-1])
    record = log_entry["record"]

    assert response.status_code == 200
    assert record["message"] == "http_request"
    assert record["extra"]["method"] == "GET"
    assert record["extra"]["path"] == "/health"
    assert record["extra"]["status_code"] == 200
    assert isinstance(record["extra"]["response_time_ms"], (int, float))
    assert record["extra"]["session_id"] == "session-123"
