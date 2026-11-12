class OpenProjectAuthError(Exception):
    """Raised when the OpenProject API returns HTTP 401."""


class OpenProjectAPIError(Exception):
    """Raised for non-auth OpenProject API errors."""

    def __init__(self, status_code: int, response_body: str, message: str = "") -> None:
        self.status_code = status_code
        self.response_body = response_body
        super().__init__(
            message or f"OpenProject API error {status_code}: {response_body}"
        )
