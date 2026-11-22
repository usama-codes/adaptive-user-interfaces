from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from threading import Lock
from uuid import uuid4


SESSION_TTL = timedelta(minutes=30)


@dataclass
class Session:
    session_id: str
    user_id: int
    created_at: datetime
    last_accessed: datetime


class SessionStore:
    def __init__(self) -> None:
        self._sessions: dict[str, Session] = {}
        self._lock = Lock()

    def create_session(self, user_id: int) -> Session:
        now = datetime.now(timezone.utc)

        session = Session(
            session_id=str(uuid4()),
            user_id=user_id,
            created_at=now,
            last_accessed=now,
        )

        with self._lock:
            self._sessions[session.session_id] = session

        return session

    def get_session(self, session_id: str) -> Session | None:
        with self._lock:
            session = self._sessions.get(session_id)

            if session is None:
                return None

            if datetime.now(timezone.utc) - session.last_accessed >= SESSION_TTL:
                del self._sessions[session_id]
                return None

            return session

    def delete_session(self, session_id: str) -> None:
        with self._lock:
            self._sessions.pop(session_id, None)

    def update_last_accessed(self, session_id: str) -> None:
        with self._lock:
            session = self._sessions.get(session_id)

            if session is None:
                return

            now = datetime.now(timezone.utc)

            if now - session.last_accessed >= SESSION_TTL:
                del self._sessions[session_id]
                return

            session.last_accessed = now


_session_store = SessionStore()


def get_session_store() -> SessionStore:
    return _session_store
