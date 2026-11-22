import json
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field

from adaptive_ui_service.app.core.session import (
    SessionStore,
    get_session_store,
)

router = APIRouter()

SCHEMA_PATH = (
    Path(__file__).resolve().parents[2] / "schemas" / "intent.json"
)


class IntentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    session_id: str = Field(min_length=1)
    raw_text: str = Field(min_length=1, max_length=2000)


def load_intent_schema() -> dict:
    with SCHEMA_PATH.open(encoding="utf-8") as schema_file:
        return json.load(schema_file)


def validate_intent_payload(payload: dict) -> None:
    schema = load_intent_schema()

    for field in schema["required"]:
        if field not in payload:
            raise ValueError(f"Missing required field: {field}")

    properties = schema["properties"]

    for field, value in payload.items():
        if schema.get("additionalProperties") is False and field not in properties:
            raise ValueError(f"Unexpected field: {field}")

        rules = properties[field]

        if not isinstance(value, str):
            raise ValueError(f"{field} must be a string")

        if len(value) < rules.get("minLength", 0):
            raise ValueError(f"{field} is shorter than the minimum length")

        if "maxLength" in rules and len(value) > rules["maxLength"]:
            raise ValueError(f"{field} is longer than the maximum length")


@router.post("/intent", status_code=status.HTTP_202_ACCEPTED)
def receive_intent(
    request: IntentRequest,
    session_store: SessionStore = Depends(get_session_store),
) -> dict[str, str | None]:
    try:
        validate_intent_payload(request.model_dump())
    except (json.JSONDecodeError, ValueError, OSError) as exception:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error": {
                    "code": "INTENT_SCHEMA_VALIDATION_FAILED",
                    "message": str(exception),
                }
            },
        ) from exception

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
