import asyncio

import httpx

from adaptive_ui_service.app.core import exceptions
from adaptive_ui_service.app.core.config import settings


class OpenProjectClient:
    def __init__(
        self,
        base_url: str | None = None,
        api_token: str | None = None,
        timeout: float = 10.0,
        max_retries: int = 2,
    ) -> None:
        self._base_url = (base_url or settings.openproject_url).rstrip("/")
        self._api_token = api_token or settings.openproject_api_token
        self._timeout = timeout
        self._max_retries = max_retries
        self._client = httpx.AsyncClient(
            base_url=self._base_url,
            headers={"Authorization": f"Token {self._api_token}"},
            timeout=httpx.Timeout(self._timeout),
        )

    async def get(self, path: str, params: dict | None = None) -> dict:
        return await self._request("GET", path, params=params)

    async def post(self, path: str, body: dict) -> dict:
        return await self._request("POST", path, json=body)

    async def _request(self, method: str, path: str, **kwargs: object) -> dict:
        last_exception: exceptions.OpenProjectAPIError | None = None

        for attempt in range(self._max_retries + 1):
            try:
                response = await self._client.request(method, path, **kwargs)
            except httpx.TimeoutException as exc:
                raise exceptions.OpenProjectAPIError(
                    status_code=0,
                    response_body="",
                    message=f"Request to {path} timed out after {self._timeout}s",
                ) from exc

            if response.status_code == 401:
                raise exceptions.OpenProjectAuthError(
                    f"Authentication failed for {path}"
                )

            if response.status_code >= 500:
                last_exception = exceptions.OpenProjectAPIError(
                    status_code=response.status_code,
                    response_body=response.text,
                )
                if attempt < self._max_retries:
                    await asyncio.sleep(2**attempt)
                    continue
                raise last_exception

            if response.status_code >= 400:
                raise exceptions.OpenProjectAPIError(
                    status_code=response.status_code,
                    response_body=response.text,
                )

            return response.json()

        raise last_exception

    async def close(self) -> None:
        await self._client.aclose()
