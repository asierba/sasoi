import time
from collections.abc import Callable, Sequence

from sasoi.agent import ChatClient
from sasoi.claude_client import ClaudeApiError, ClaudeConnectionError, ClaudeError, Reply

BACKOFF_SECONDS = (1, 2, 4)


def is_transient(error: ClaudeError) -> bool:
    if isinstance(error, ClaudeConnectionError):
        return True
    return isinstance(error, ClaudeApiError) and (error.status_code == 429 or error.status_code >= 500)


class RetryingClient:
    def __init__(
        self,
        client: ChatClient,
        backoff: Sequence[float] = BACKOFF_SECONDS,
        sleep: Callable[[float], None] = time.sleep,
    ):
        self._client = client
        self._backoff = backoff
        self._sleep = sleep

    def send(self, messages: list[dict], tools: list[dict]) -> Reply:
        for delay in self._backoff:
            try:
                return self._client.send(messages, tools)
            except ClaudeError as error:
                if not is_transient(error):
                    raise
            self._sleep(delay)
        return self._client.send(messages, tools)
