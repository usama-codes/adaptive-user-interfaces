import pytest
from fastapi.testclient import TestClient

from app.core.session import SessionStore, get_session_store
from app.main import app


@pytest.fixture
def client_and_store():
    store = SessionStore()
    app.dependency_overrides[get_session_store] = lambda: store
    try:
        with TestClient(app) as client:
            yield client, store
    finally:
        app.dependency_overrides.clear()


def test_valid_intent_returns_202(client_and_store) -> None:
    client, store = client_and_store
    session = store.create_session(user_id=42)

    response = client.post(
        "/intent",
        json={"session_id": session.session_id, "raw_text": "Create a project plan"},
    )

    assert response.status_code == 202
    assert response.json() == {
        "status": "received",
        "intent": None,
        "message": "normalization not yet implemented",
    }


def test_missing_session_id_returns_422(client_and_store) -> None:
    client, _store = client_and_store

    response = client.post("/intent", json={"raw_text": "Create a project plan"})

    assert response.status_code == 422


def test_empty_raw_text_returns_422(client_and_store) -> None:
    client, store = client_and_store
    session = store.create_session(user_id=42)

    response = client.post(
        "/intent",
        json={"session_id": session.session_id, "raw_text": ""},
    )

    assert response.status_code == 422


def test_unknown_session_returns_global_error_format(client_and_store) -> None:
    client, _store = client_and_store

    response = client.post(
        "/intent",
        json={"session_id": "missing-session", "raw_text": "Create a project plan"},
    )

    assert response.status_code == 401
    assert response.json() == {
        "error": {
            "code": "SESSION_NOT_FOUND",
            "message": "Session not found",
        }
    }