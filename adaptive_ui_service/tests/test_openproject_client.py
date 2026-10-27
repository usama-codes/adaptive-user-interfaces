import httpx
import pytest
import respx

from adaptive_ui_service.app.core import exceptions
from adaptive_ui_service.app.core.openproject_client import OpenProjectClient


@pytest.mark.asyncio
@respx.mock
async def test_get_success() -> None:
    route = respx.get("http://testserver/api/v3/users/me").mock(
        return_value=httpx.Response(200, json={"id": 1, "name": "Ada"})
    )
    client = OpenProjectClient(base_url="http://testserver", api_token="test-token")

    try:
        result = await client.get("/api/v3/users/me")
    finally:
        await client.close()

    assert result == {"id": 1, "name": "Ada"}
    assert route.calls[0].request.headers["Authorization"] == "Token test-token"


@pytest.mark.asyncio
@respx.mock
async def test_auth_error_raises_openproject_auth_error() -> None:
    respx.get("http://testserver/api/v3/users/me").mock(
        return_value=httpx.Response(401)
    )
    client = OpenProjectClient(base_url="http://testserver", api_token="invalid-token")

    try:
        with pytest.raises(exceptions.OpenProjectAuthError):
            await client.get("/api/v3/users/me")
    finally:
        await client.close()


@pytest.mark.asyncio
@respx.mock
async def test_server_error_retries_then_raises() -> None:
    route = respx.get("http://testserver/api/v3/status").mock(
        return_value=httpx.Response(500, text="server error")
    )
    client = OpenProjectClient(base_url="http://testserver", api_token="test-token")

    try:
        with pytest.raises(exceptions.OpenProjectAPIError) as error:
            await client.get("/api/v3/status")
    finally:
        await client.close()

    assert error.value.status_code == 500
    assert route.call_count == 3


@pytest.mark.asyncio
@respx.mock
async def test_timeout_raises_openproject_api_error() -> None:
    respx.get("http://testserver/api/v3/users/me").mock(
        side_effect=httpx.ReadTimeout("request timed out")
    )
    client = OpenProjectClient(base_url="http://testserver", api_token="test-token")

    try:
        with pytest.raises(exceptions.OpenProjectAPIError) as error:
            await client.get("/api/v3/users/me")
    finally:
        await client.close()

    assert error.value.status_code == 0
