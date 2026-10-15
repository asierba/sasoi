import json

import httpx
import pytest

from sasoi.claude_client import ClaudeApiError, ClaudeClient, ClaudeConnectionError


def test_send_returns_single_text_block_as_is():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"content": [{"type": "text", "text": "Hello there"}]})

    http = httpx.Client(transport=httpx.MockTransport(handler))

    reply = ClaudeClient("test-key", "test-model", http).send([{"role": "user", "content": "hi"}])

    assert reply == "Hello there"


def test_send_posts_prompt_and_returns_text():
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["request"] = request
        return httpx.Response(
            200,
            json={"content": [{"type": "text", "text": "Hello "}, {"type": "text", "text": "there"}]},
        )

    http = httpx.Client(transport=httpx.MockTransport(handler))

    reply = ClaudeClient("test-key", "test-model", http).send([{"role": "user", "content": "hi"}])

    request = captured["request"]
    assert str(request.url) == "https://api.anthropic.com/v1/messages"
    assert request.headers["x-api-key"] == "test-key"
    assert request.headers["anthropic-version"] == "2023-06-01"
    assert json.loads(request.content) == {
        "model": "test-model",
        "max_tokens": 1024,
        "messages": [{"role": "user", "content": "hi"}],
    }
    assert reply == "Hello there"


def test_send_raises_api_error_with_type_and_message():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            401,
            json={
                "type": "error",
                "error": {"type": "authentication_error", "message": "invalid x-api-key"},
            },
        )

    http = httpx.Client(transport=httpx.MockTransport(handler))

    with pytest.raises(ClaudeApiError) as raised:
        ClaudeClient("bad-key", "test-model", http).send([{"role": "user", "content": "hi"}])

    assert raised.value.status_code == 401
    assert raised.value.error_type == "authentication_error"
    assert raised.value.message == "invalid x-api-key"
    assert str(raised.value) == "401 authentication_error: invalid x-api-key"


def test_send_raises_api_error_with_raw_body_when_not_json():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(502, text="Bad Gateway")

    http = httpx.Client(transport=httpx.MockTransport(handler))

    with pytest.raises(ClaudeApiError) as raised:
        ClaudeClient("test-key", "test-model", http).send([{"role": "user", "content": "hi"}])

    assert raised.value.status_code == 502
    assert raised.value.error_type is None
    assert raised.value.message == "Bad Gateway"


def test_send_raises_connection_error_when_network_fails():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("nodename nor servname provided", request=request)

    http = httpx.Client(transport=httpx.MockTransport(handler))

    with pytest.raises(ClaudeConnectionError) as raised:
        ClaudeClient("test-key", "test-model", http).send([{"role": "user", "content": "hi"}])

    assert str(raised.value) == "connection failed: nodename nor servname provided"
