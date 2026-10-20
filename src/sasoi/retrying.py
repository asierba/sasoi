import time
from collections.abc import Callable, Sequence

from sasoi.agent import ChatClient
from sasoi.claude_client import ClaudeApiError, ClaudeConnectionError, ClaudeError, Reply, Request

BACKOFF_SECONDS = (1, 2, 4)
MAX_WAIT_SECONDS = 60


def is_transient(error: ClaudeError) -> bool:
    if isinstance(error, ClaudeConnectionError):
        return True
    return isinstance(error, ClaudeApiError) and (error.status_code == 429 or error.status_code >= 500)


def wait_before_retry(error: ClaudeError, backoff: float) -> float:
    if isinstance(error, ClaudeApiError) and error.retry_after is not None:
        return error.retry_after
    return backoff


class RetryingClient:
    def __init__(
        self,
        client: ChatClient,
        backoff: Sequence[float] = BACKOFF_SECONDS,
        sleep: Callable[[float], None] = time.sleep,
        max_wait: float = MAX_WAIT_SECONDS,
    ):
        self._client = client
        self._backoff = backoff
        self._sleep = sleep
        self._max_wait = max_wait

    def send(self, request: Request) -> Reply:
        for delay in self._backoff:
            try:
                return self._client.send(request)
            except ClaudeError as error:
                wait = wait_before_retry(error, delay)
                if not is_transient(error) or wait > self._max_wait:
                    raise
                self._sleep(wait)
        return self._client.send(request)
