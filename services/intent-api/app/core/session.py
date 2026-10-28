from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from threading import RLock
from uuid import uuid4


@dataclass
class Session:
    session_id: str
    user_id: int
    created_at: datetime
    last_accessed: datetime


class SessionStore:
    TTL = timedelta(minutes=30)

    def __init__(self) -> None:
        self._sessions: dict[str, Session] = {}
        self._lock = RLock()

    def create_session(self, user_id: int) -> Session:
        with self._lock:
            now = datetime.now(timezone.utc)
            session = Session(
                session_id=str(uuid4()),
                user_id=user_id,
                created_at=now,
                last_accessed=now,
            )
            self._sessions[session.session_id] = session
            return session

    def get_session(self, session_id: str) -> Session | None:
        with self._lock:
            return self._get_valid_session(session_id, datetime.now(timezone.utc))

    def delete_session(self, session_id: str) -> None:
        with self._lock:
            self._sessions.pop(session_id, None)

    def update_last_accessed(self, session_id: str) -> None:
        with self._lock:
            session = self._get_valid_session(session_id, datetime.now(timezone.utc))
            if session is not None:
                session.last_accessed = datetime.now(timezone.utc)

    def _get_valid_session(self, session_id: str, now: datetime) -> Session | None:
        session = self._sessions.get(session_id)
        if session is None:
            return None
        if now - session.last_accessed >= self.TTL:
            del self._sessions[session_id]
            return None
        return session


session_store = SessionStore()


def get_session_store() -> SessionStore:
    return session_store