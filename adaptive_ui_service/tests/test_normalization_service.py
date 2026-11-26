import json

import httpx
import pytest
import respx

from adaptive_ui_service.app.core import exceptions
from adaptive_ui_service.app.core.config import Settings
from adaptive_ui_service.app.services import normalization_service

GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"
USER_CONTEXT = {
    "capabilities": [{"id": "time_charts"}],
    "destinations": ["secondary_panel"],
}
INTENT = {
    "action": "move",
    "target_capability_id": "time_charts",
    "destination": "secondary_panel",
    "confidence": 0.95,
    "clarification_question": None,
}


@pytest.fixture
def gemini_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        normalization_service.config,
        "get_settings",
        lambda: Settings(
            gemini_api_key="test-key",
            gemini_model="gemini-test",
            gemini_base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
            gemini_timeout=12,
        ),
    )


@pytest.mark.asyncio
@pytest.mark.usefixtures("gemini_settings")
@respx.mock
async def test_normalize_intent_parses_tool_call() -> None:
    route = respx.post(GEMINI_URL).mock(
        return_value=httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "tool_calls": [
                                {
                                    "function": {
                                        "name": "normalize_intent",
                                        "arguments": json.dumps(INTENT),
                                    }
                                }
                            ]
                        }
                    }
                ]
            },
        )
    )

    result = await normalization_service.normalize_intent(
        "Move the time charts to a secondary location",
        USER_CONTEXT,
    )

    assert result == INTENT
    request = route.calls[0].request
    assert request.headers["Authorization"] == "Bearer test-key"
    request_body = json.loads(request.content)
    function = request_body["tools"][0]["function"]
    assert function["parameters"] == normalization_service.load_intent_schema()


@pytest.mark.asyncio
@pytest.mark.usefixtures("gemini_settings")
@respx.mock
async def test_normalize_intent_missing_tool_call_raises_typed_error() -> None:
    respx.post(GEMINI_URL).mock(
        return_value=httpx.Response(
            200,
            json={"choices": [{"message": {"content": "not a tool call"}}]},
        )
    )

    with pytest.raises(exceptions.NormalizationError):
        await normalization_service.normalize_intent("Move the charts", USER_CONTEXT)


@pytest.mark.asyncio
@pytest.mark.usefixtures("gemini_settings")
@respx.mock
async def test_normalize_intent_rejects_unknown_capability() -> None:
    unknown_intent = {**INTENT, "target_capability_id": "unknown"}
    respx.post(GEMINI_URL).mock(
        return_value=httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "tool_calls": [
                                {
                                    "function": {
                                        "name": "normalize_intent",
                                        "arguments": json.dumps(unknown_intent),
                                    }
                                }
                            ]
                        }
                    }
                ]
            },
        )
    )

    with pytest.raises(exceptions.NormalizationError):
        await normalization_service.normalize_intent("Move the charts", USER_CONTEXT)
