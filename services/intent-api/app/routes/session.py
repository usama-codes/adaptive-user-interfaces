from fastapi import APIRouter, Depends, status
from pydantic import BaseModel

from app.core.session import Session, SessionStore, get_session_store


router = APIRouter()


class SessionRequest(BaseModel):
    user_id: int


@router.post("/sessions", status_code=status.HTTP_201_CREATED)
def create_session(
    request: SessionRequest,
    session_store: SessionStore = Depends(get_session_store),
) -> Session:
    return session_store.create_session(request.user_id)
