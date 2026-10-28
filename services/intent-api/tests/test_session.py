from datetime import datetime, timedelta, timezone

from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from app.core import session as session_module
from app.core.session import SessionStore, get_session_store


def test_create_session_can_be_retrieved_immediately() -> None:
    store = SessionStore()

    created = store.create_session(user_id=42)

    assert store.get_session(created.session_id) == created
    assert created.user_id == 42


def test_get_removes_session_after_ttl(monkeypatch) -> None:
    current_time = datetime(2026, 10, 29, tzinfo=timezone.utc)

    class FrozenDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            if tz is None:
                return current_time.replace(tzinfo=None)
            return current_time.astimezone(tz)

    monkeypatch.setattr(session_module, "datetime", FrozenDateTime)
    store = SessionStore()
    created = store.create_session(user_id=42)
    current_time += timedelta(minutes=31)

    assert store.get_session(created.session_id) is None
    assert created.session_id not in store._sessions


def test_delete_then_get_returns_none() -> None:
    store = SessionStore()
    created = store.create_session(user_id=42)

    store.delete_session(created.session_id)

    assert store.get_session(created.session_id) is None


def test_session_store_can_be_injected_with_depends() -> None:
    store = SessionStore()
    created = store.create_session(user_id=42)
    app = FastAPI()

    @app.get("/session/{session_id}")
    def read_session(
        session_id: str,
        session_store: SessionStore = Depends(get_session_store),
    ) -> dict[str, str | None]:
        session = session_store.get_session(session_id)
        return {"session_id": session.session_id if session else None}

    app.dependency_overrides[get_session_store] = lambda: store
    try:
        response = TestClient(app).get(f"/session/{created.session_id}")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {"session_id": created.session_id}