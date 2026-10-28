from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.core.session import SessionStore, get_session_store


router = APIRouter()


class IntentRequest(BaseModel):
    session_id: str
    raw_text: str = Field(min_length=1, max_length=2000)


@router.post("/intent", status_code=status.HTTP_202_ACCEPTED)
def receive_intent(
    request: IntentRequest,
    session_store: SessionStore = Depends(get_session_store),
) -> dict[str, str | None]:
    if session_store.get_session(request.session_id) is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": {
                    "code": "SESSION_NOT_FOUND",
                    "message": "Session not found",
                }
            },
        )

    session_store.update_last_accessed(request.session_id)
    return {
        "status": "received",
        "intent": None,
        "message": "normalization not yet implemented",
    }