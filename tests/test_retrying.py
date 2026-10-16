import pytest

from sasoi.claude_client import ClaudeApiError, ClaudeConnectionError, Reply
from sasoi.retrying import RetryingClient

A_REPLY = Reply([{"type": "text", "text": "Hi!"}], "end_turn")
A_MESSAGES = [{"role": "user", "content": "hello"}]
AN_ERROR_TYPE = "an_error"
AN_ERROR_MESSAGE = "Something went wrong"


def api_error(status_code: int, retry_after: float | None = None) -> ClaudeApiError:
    return ClaudeApiError(status_code, AN_ERROR_TYPE, AN_ERROR_MESSAGE, retry_after)


class FakeClient:
    def __init__(self, *outcomes: Reply | Exception):
        self._outcomes = list(outcomes)
        self.attempts = 0

    def send(self, messages: list[dict], tools: list[dict]) -> Reply:
        self.attempts += 1
        outcome = self._outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


class TestRetryingClient:
    @pytest.mark.parametrize(
        "error",
        [
            ClaudeConnectionError(AN_ERROR_MESSAGE),
            api_error(429),
            api_error(500),
            api_error(529),
        ],
    )
    def test_retries_transient_error_and_returns_reply(self, error):
        client = FakeClient(error, A_REPLY)

        reply = RetryingClient(client, backoff=(1,), sleep=lambda _: None).send(A_MESSAGES, [])

        assert reply == A_REPLY

    def test_waits_longer_before_each_retry(self):
        client = FakeClient(api_error(529), api_error(529), api_error(529), A_REPLY)
        waits: list[float] = []

        RetryingClient(client, backoff=(1, 2, 4), sleep=waits.append).send(A_MESSAGES, [])

        assert waits == [1, 2, 4]

    def test_waits_as_long_as_retry_after_says(self):
        client = FakeClient(api_error(429, retry_after=30), A_REPLY)
        waits: list[float] = []

        RetryingClient(client, backoff=(1,), sleep=waits.append).send(A_MESSAGES, [])

        assert waits == [30]

    def test_raises_without_waiting_when_retry_after_exceeds_max_wait(self):
        client = FakeClient(api_error(429, retry_after=45115))
        waits: list[float] = []

        with pytest.raises(ClaudeApiError):
            RetryingClient(client, backoff=(1,), sleep=waits.append, max_wait=60).send(A_MESSAGES, [])

        assert waits == []

    def test_raises_last_error_when_retries_run_out(self):
        first = api_error(529)
        last = api_error(529)
        client = FakeClient(first, last)

        with pytest.raises(ClaudeApiError) as raised:
            RetryingClient(client, backoff=(1,), sleep=lambda _: None).send(A_MESSAGES, [])

        assert raised.value is last

    def test_raises_client_error_without_retrying(self):
        client = FakeClient(api_error(400))

        with pytest.raises(ClaudeApiError):
            RetryingClient(client, backoff=(1,), sleep=lambda _: None).send(A_MESSAGES, [])

        assert client.attempts == 1
