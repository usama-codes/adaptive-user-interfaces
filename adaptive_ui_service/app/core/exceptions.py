class OpenProjectAuthError(Exception):
    """Raised when the OpenProject API rejects authentication."""


class OpenProjectAPIError(Exception):
    """Raised for non-authentication OpenProject API errors."""

    def __init__(self, status_code: int, response_body: str, message: str = ""):
        self.status_code = status_code
        self.response_body = response_body
        super().__init__(
            message or f"OpenProject API error {status_code}: {response_body}"
        )
