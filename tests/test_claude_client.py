import json

import httpx
import pytest

from sasoi.claude_client import ClaudeApiError, ClaudeClient, ClaudeConnectionError, Reply, Request, Usage


A_KEY = "test-key"
A_MODEL = "test-model"
A_MESSAGES = [{"role": "user", "content": "hi"}]
A_REQUEST = Request(A_MESSAGES, [])
A_USAGE = {"input_tokens": 1, "output_tokens": 1}


class TestClaudeClient:
    def test_send_posts_prompt_and_returns_text_and_usage(self):
        captured = {}

        def handler(request: httpx.Request) -> httpx.Response:
            captured["request"] = request
            return httpx.Response(
                200,
                json={
                    "content": [{"type": "text", "text": "Hello there"}],
                    "stop_reason": "end_turn",
                    "usage": {"input_tokens": 12, "output_tokens": 5},
                },
            )

        http = httpx.Client(transport=httpx.MockTransport(handler))

        reply = ClaudeClient("test-key", "test-model", http).send(Request([{"role": "user", "content": "hi"}], []))

        request = captured["request"]
        assert str(request.url) == "https://api.anthropic.com/v1/messages"
        assert request.headers["x-api-key"] == "test-key"
        assert request.headers["anthropic-version"] == "2023-06-01"
        assert json.loads(request.content) == {
            "model": "test-model",
            "max_tokens": 1024,
            "messages": [{"role": "user", "content": "hi"}],
            "tools": [],
        }
        assert reply.text == "Hello there"
        assert reply.usage == Usage(input_tokens=12, output_tokens=5)

    def test_send_posts_tools_and_returns_tool_use_content_and_stop_reason(self):
        captured = {}
        tools = [{"name": "current_time", "description": "Now", "input_schema": {"type": "object"}}]
        tool_use = {"type": "tool_use", "id": "toolu_1", "name": "current_time", "input": {}}

        def handler(request: httpx.Request) -> httpx.Response:
            captured["request"] = request
            return httpx.Response(200, json={"content": [tool_use], "stop_reason": "tool_use", "usage": A_USAGE})

        http = httpx.Client(transport=httpx.MockTransport(handler))

        reply = ClaudeClient(A_KEY, A_MODEL, http).send(Request(A_MESSAGES, tools))

        assert json.loads(captured["request"].content)["tools"] == tools
        assert reply.content == [tool_use]
        assert reply.stop_reason == "tool_use"

    def test_send_raises_api_error_with_type_and_message(self):
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
            ClaudeClient(A_KEY, A_MODEL, http).send(A_REQUEST)

        assert raised.value.status_code == 401
        assert raised.value.error_type == "authentication_error"
        assert raised.value.message == "invalid x-api-key"
        assert str(raised.value) == "401 authentication_error: invalid x-api-key"

    def test_send_raises_api_error_with_raw_body_when_not_json(self):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(502, text="Bad Gateway")

        http = httpx.Client(transport=httpx.MockTransport(handler))

        with pytest.raises(ClaudeApiError) as raised:
            ClaudeClient(A_KEY, A_MODEL, http).send(A_REQUEST)

        assert raised.value.status_code == 502
        assert raised.value.error_type is None
        assert raised.value.message == "Bad Gateway"

    def test_send_raises_api_error_with_retry_after_seconds(self):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(429, headers={"retry-after": "30"})

        http = httpx.Client(transport=httpx.MockTransport(handler))

        with pytest.raises(ClaudeApiError) as raised:
            ClaudeClient(A_KEY, A_MODEL, http).send(A_REQUEST)

        assert raised.value.retry_after == 30.0

    def test_send_raises_connection_error_when_network_fails(self):
        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("nodename nor servname provided", request=request)

        http = httpx.Client(transport=httpx.MockTransport(handler))

        with pytest.raises(ClaudeConnectionError) as raised:
            ClaudeClient(A_KEY, A_MODEL, http).send(A_REQUEST)

        assert str(raised.value) == "connection failed: nodename nor servname provided"


A_STOP_REASON = "end_turn"


class TestReply:
    def test_returns_text(self):
        reply = Reply([{"type": "text", "text": "Hello"}], A_STOP_REASON)

        assert reply.text == "Hello"

    def test_joins_text_blocks(self):
        reply = Reply([{"type": "text", "text": "Hello "}, {"type": "text", "text": "there"}], A_STOP_REASON)

        assert reply.text == "Hello there"

    def test_returns_tool_calls(self):
        tool_use = {"type": "tool_use", "id": "toolu_1", "name": "current_time", "input": {}}
        reply = Reply([tool_use], A_STOP_REASON)

        assert reply.tool_calls == [tool_use]

    def test_text_ignores_non_text_blocks(self):
        reply = Reply([{"type": "text", "text": "Let me check"}, {"type": "tool_use"}], A_STOP_REASON)

        assert reply.text == "Let me check"

    def test_tool_calls_ignores_text_blocks(self):
        tool_use = {"type": "tool_use", "id": "toolu_1", "name": "current_time", "input": {}}
        reply = Reply([{"type": "text"}, tool_use], A_STOP_REASON)

        assert reply.tool_calls == [tool_use]
