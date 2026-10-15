import httpx

MESSAGES_URL = "https://api.anthropic.com/v1/messages"
API_VERSION = "2023-06-01"
MAX_TOKENS = 1024


class ClaudeError(Exception):
    pass


class ClaudeConnectionError(ClaudeError):
    pass


class ClaudeApiError(ClaudeError):
    def __init__(self, status_code: int, error_type: str | None, message: str):
        super().__init__(f"{status_code} {error_type or 'unknown_error'}: {message}")
        self.status_code = status_code
        self.error_type = error_type
        self.message = message

    @classmethod
    def from_response(cls, response: httpx.Response) -> "ClaudeApiError":
        try:
            error = response.json()["error"]
            return cls(response.status_code, error["type"], error["message"])
        except (ValueError, KeyError, TypeError):
            return cls(response.status_code, None, response.text)


class ClaudeClient:
    def __init__(self, api_key: str, model: str, http: httpx.Client):
        self._api_key = api_key
        self._model = model
        self._http = http

    def send(self, messages: list[dict]) -> str:
        try:
            response = self._http.post(
                MESSAGES_URL,
                headers={
                    "x-api-key": self._api_key,
                    "anthropic-version": API_VERSION,
                    "content-type": "application/json",
                },
                json={
                    "model": self._model,
                    "max_tokens": MAX_TOKENS,
                    "messages": messages,
                },
            )
        except httpx.TransportError as error:
            raise ClaudeConnectionError(f"connection failed: {error}") from error
        if response.is_error:
            raise ClaudeApiError.from_response(response)
        return "".join(
            block["text"] for block in response.json()["content"] if block["type"] == "text"
        )
