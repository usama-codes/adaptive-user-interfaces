import pytest
from fastapi.testclient import TestClient

from adaptive_ui_service.app.core.session import SessionStore, get_session_store
from adaptive_ui_service.app.main import app


@pytest.fixture
def client_and_store():
    store = SessionStore()
    app.dependency_overrides[get_session_store] = lambda: store

    try:
        with TestClient(app) as client:
            yield client, store
    finally:
        app.dependency_overrides.clear()


def test_valid_intent_returns_202(client_and_store, monkeypatch) -> None:
    client, store = client_and_store
    session = store.create_session(user_id=42)

    updated = []
    monkeypatch.setattr(
        store,
        "update_last_accessed",
        lambda session_id: updated.append(session_id),
    )

    response = client.post(
        "/intent",
        json={
            "session_id": session.session_id,
            "raw_text": "Create a project plan",
        },
    )

    assert response.status_code == 202
    assert response.json() == {
        "status": "received",
        "intent": None,
        "message": "normalization not yet implemented",
    }
    assert updated == [session.session_id]


def test_missing_session_id_returns_422(client_and_store) -> None:
    client, _store = client_and_store

    response = client.post(
        "/intent",
        json={"raw_text": "Create a project plan"},
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_empty_raw_text_returns_422(client_and_store) -> None:
    client, store = client_and_store
    session = store.create_session(user_id=42)

    response = client.post(
        "/intent",
        json={
            "session_id": session.session_id,
            "raw_text": "",
        },
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_unknown_session_returns_401(client_and_store) -> None:
    client, _store = client_and_store

    response = client.post(
        "/intent",
        json={
            "session_id": "missing-session",
            "raw_text": "Create a project plan",
        },
    )

    assert response.status_code == 401
    assert response.json() == {
        "error": {
            "code": "SESSION_NOT_FOUND",
            "message": "Session not found",
        }
    }


def test_schema_file_is_loaded() -> None:
    from adaptive_ui_service.app.services import normalization_service

    schema = normalization_service.load_intent_schema()

    assert schema["title"] == "Intent"
    assert schema["properties"]["action"]["enum"] == [
        "move",
        "hide",
        "show",
        "reorder",
        "unsupported",
        "clarify",
    ]
