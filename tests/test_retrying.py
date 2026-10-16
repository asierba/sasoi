import pytest

from sasoi.claude_client import ClaudeApiError, ClaudeConnectionError, Reply
from sasoi.retrying import RetryingClient

A_REPLY = Reply([{"type": "text", "text": "Hi!"}], "end_turn")
A_MESSAGES = [{"role": "user", "content": "hello"}]


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
            ClaudeConnectionError("connection failed"),
            ClaudeApiError(429, "rate_limit_error", "Too many requests"),
            ClaudeApiError(500, "api_error", "Internal error"),
            ClaudeApiError(529, "overloaded_error", "Overloaded"),
        ],
    )
    def test_retries_transient_error_and_returns_reply(self, error):
        client = FakeClient(error, A_REPLY)

        reply = RetryingClient(client, backoff=(1,), sleep=lambda _: None).send(A_MESSAGES, [])

        assert reply == A_REPLY

    def test_waits_longer_before_each_retry(self):
        overloaded = ClaudeApiError(529, "overloaded_error", "Overloaded")
        client = FakeClient(overloaded, overloaded, overloaded, A_REPLY)
        waits: list[float] = []

        RetryingClient(client, backoff=(1, 2, 4), sleep=waits.append).send(A_MESSAGES, [])

        assert waits == [1, 2, 4]

    def test_waits_as_long_as_retry_after_says(self):
        rate_limited = ClaudeApiError(429, "rate_limit_error", "Too many requests", retry_after=30)
        client = FakeClient(rate_limited, A_REPLY)
        waits: list[float] = []

        RetryingClient(client, backoff=(1,), sleep=waits.append).send(A_MESSAGES, [])

        assert waits == [30]

    def test_raises_last_error_when_retries_run_out(self):
        first = ClaudeApiError(529, "overloaded_error", "first")
        last = ClaudeApiError(529, "overloaded_error", "last")
        client = FakeClient(first, last)

        with pytest.raises(ClaudeApiError) as raised:
            RetryingClient(client, backoff=(1,), sleep=lambda _: None).send(A_MESSAGES, [])

        assert raised.value is last

    def test_raises_client_error_without_retrying(self):
        client = FakeClient(ClaudeApiError(400, "invalid_request_error", "Bad request"))

        with pytest.raises(ClaudeApiError):
            RetryingClient(client, backoff=(1,), sleep=lambda _: None).send(A_MESSAGES, [])

        assert client.attempts == 1
