import json
from pathlib import Path
from typing import Literal

import httpx
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from adaptive_ui_service.app.core import config, exceptions
from adaptive_ui_service.app.prompts.intent_extraction import SYSTEM_PROMPT

SCHEMA_PATH = Path(__file__).resolve().parents[2] / "schemas" / "intent.json"
TOOL_NAME = "normalize_intent"


class Intent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    action: Literal["move", "hide", "show", "reorder", "unsupported", "clarify"]
    target_capability_id: str | None
    destination: str | None
    confidence: float = Field(ge=0, le=1)
    clarification_question: str | None


def load_intent_schema() -> dict:
    try:
        with SCHEMA_PATH.open(encoding="utf-8") as schema_file:
            return json.load(schema_file)
    except (OSError, json.JSONDecodeError) as error:
        raise exceptions.NormalizationError() from error


def _context_values(user_context: dict, key: str) -> set[str]:
    values = user_context.get(key, [])
    if not isinstance(values, list):
        raise exceptions.IntentValidationError(f"user_context.{key} must be a list")

    result: set[str] = set()
    for value in values:
        item = value.get("id") if isinstance(value, dict) else value
        if isinstance(item, str):
            result.add(item)
    return result


def _validate_context_references(intent: Intent, user_context: dict) -> None:
    capability_ids = _context_values(user_context, "capabilities")
    destinations = _context_values(user_context, "destinations")

    if (
        intent.target_capability_id is not None
        and intent.target_capability_id not in capability_ids
    ):
        raise exceptions.NormalizationError()

    if intent.destination is not None and intent.destination not in destinations:
        raise exceptions.NormalizationError()


async def normalize_intent(raw_text: str, user_context: dict) -> dict:
    if not raw_text.strip():
        raise exceptions.IntentValidationError("raw_text must not be empty")

    settings = config.get_settings()
    if not settings.gemini_api_key:
        raise exceptions.NormalizationError()

    try:
        user_content = json.dumps(
            {"raw_text": raw_text, "user_context": user_context},
            ensure_ascii=False,
        )
    except (TypeError, ValueError) as error:
        raise exceptions.IntentValidationError(
            "user_context must be JSON serializable"
        ) from error

    request_body = {
        "model": settings.gemini_model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
        "tools": [
            {
                "type": "function",
                "function": {
                    "name": TOOL_NAME,
                    "description": "Return the user's request as a canonical Intent.",
                    "parameters": load_intent_schema(),
                },
            }
        ],
        "tool_choice": {
            "type": "function",
            "function": {"name": TOOL_NAME},
        },
    }

    try:
        async with httpx.AsyncClient(timeout=settings.gemini_timeout) as client:
            response = await client.post(
                f"{settings.gemini_base_url.rstrip('/')}/chat/completions",
                headers={"Authorization": f"Bearer {settings.gemini_api_key}"},
                json=request_body,
            )
            response.raise_for_status()
            payload = response.json()
    except httpx.HTTPError as error:
        raise exceptions.NormalizationError() from error
    except ValueError as error:
        raise exceptions.NormalizationError() from error

    if not isinstance(payload, dict):
        raise exceptions.NormalizationError()
    choices = payload.get("choices")
    if not isinstance(choices, list) or not choices or not isinstance(choices[0], dict):
        raise exceptions.NormalizationError()

    message = choices[0].get("message")
    if not isinstance(message, dict):
        raise exceptions.NormalizationError()
    tool_calls = message.get("tool_calls")
    if not isinstance(tool_calls, list):
        raise exceptions.NormalizationError()

    tool_call = next(
        (
            call
            for call in tool_calls
            if isinstance(call, dict)
            and isinstance(call.get("function"), dict)
            and call["function"].get("name") == TOOL_NAME
        ),
        None,
    )
    if tool_call is None:
        raise exceptions.NormalizationError()

    arguments = tool_call["function"].get("arguments")
    if not isinstance(arguments, str):
        raise exceptions.NormalizationError()

    try:
        intent = Intent.model_validate_json(arguments)
    except ValidationError as error:
        raise exceptions.NormalizationError() from error

    _validate_context_references(intent, user_context)
    return intent.model_dump(mode="json")
