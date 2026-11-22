from datetime import datetime, timedelta, timezone

from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from adaptive_ui_service.app.core import session as session_module
from adaptive_ui_service.app.core.session import (
    SessionStore,
    get_session_store,
)


def test_create_and_get_session() -> None:
    store = SessionStore()

    created = store.create_session(user_id=14)
    retrieved = store.get_session(created.session_id)

    assert retrieved == created
    assert created.user_id == 14
    assert created.created_at.tzinfo == timezone.utc


def test_expired_session_is_removed(monkeypatch) -> None:
    class FixedDateTime(datetime):
        current = datetime(2026, 11, 22, 12, 0, tzinfo=timezone.utc)

        @classmethod
        def now(cls, tz=None):
            if tz is None:
                return cls.current.replace(tzinfo=None)
            return cls.current.astimezone(tz)

    monkeypatch.setattr(session_module, "datetime", FixedDateTime)

    store = SessionStore()
    created = store.create_session(user_id=14)

    FixedDateTime.current += timedelta(minutes=31)

    assert store.get_session(created.session_id) is None
    assert created.session_id not in store._sessions


def test_delete_session() -> None:
    store = SessionStore()

    created = store.create_session(user_id=14)
    store.delete_session(created.session_id)

    assert store.get_session(created.session_id) is None


def test_session_store_dependency_injection() -> None:
    app = FastAPI()

    @app.get("/test-session/{user_id}")
    def create_test_session(
        user_id: int,
        store: SessionStore = Depends(get_session_store),
    ) -> dict[str, str | int]:
        created = store.create_session(user_id)
        return {
            "session_id": created.session_id,
            "user_id": created.user_id,
        }

    client = TestClient(app)
    response = client.get("/test-session/14")

    assert response.status_code == 200
    assert response.json()["user_id"] == 14
    assert response.json()["session_id"]
