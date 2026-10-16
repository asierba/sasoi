import io
import json

import pytest

from sasoi.claude_client import ClaudeApiError, Reply
from sasoi.tools.tool import Tool, ToolError
from sasoi.tools.toolbox import Toolbox
from sasoi.tracing import TracedClient, TracedToolbox, Tracer


class FakeClient:
    def __init__(self, outcome: Reply | Exception):
        self._outcome = outcome

    def send(self, messages: list[dict], tools: list[dict]) -> Reply:
        if isinstance(self._outcome, Exception):
            raise self._outcome
        return self._outcome


def timer(*readings: float):
    return iter(readings).__next__


def recorded(sink: io.StringIO) -> list[dict]:
    return [json.loads(line) for line in sink.getvalue().splitlines()]


A_TIMER_READING = 0.0
A_DESCRIPTION = "Does something"
AN_INPUT_SCHEMA = {"type": "object"}


class TestTracer:
    def test_writes_one_json_line_per_event(self):
        sink = io.StringIO()
        tracer = Tracer(sink)

        tracer.record({"type": "first"})
        tracer.record({"type": "second"})

        assert sink.getvalue() == '{"type": "first"}\n{"type": "second"}\n'


class TestTracedClient:
    def test_records_request_reply_and_duration(self):
        sink = io.StringIO()
        reply = Reply([{"type": "text", "text": "Hi!"}], "end_turn")
        client = TracedClient(FakeClient(reply), Tracer(sink), timer(1.0, 1.25))

        returned = client.send([{"role": "user", "content": "hello"}], [{"name": "current_time"}])

        assert returned == reply
        assert recorded(sink) == [
            {
                "type": "claude_call",
                "messages": [{"role": "user", "content": "hello"}],
                "tools": [{"name": "current_time"}],
                "content": [{"type": "text", "text": "Hi!"}],
                "stop_reason": "end_turn",
                "duration_ms": 250.0,
            }
        ]

    def test_records_error_and_reraises(self):
        sink = io.StringIO()
        error = ClaudeApiError(529, "overloaded_error", "Overloaded")
        client = TracedClient(FakeClient(error), Tracer(sink), timer(A_TIMER_READING, A_TIMER_READING))

        with pytest.raises(ClaudeApiError):
            client.send([{"role": "user", "content": "hello"}], [])

        [event] = recorded(sink)
        assert event["error"] == "529 overloaded_error: Overloaded"


class TestTracedToolbox:
    def test_records_tool_call_and_returns_result(self):
        sink = io.StringIO()
        clock = Tool("current_time", A_DESCRIPTION, AN_INPUT_SCHEMA, lambda _: "09:00")
        toolbox = TracedToolbox(Toolbox([clock]), Tracer(sink), timer(2.0, 2.5))

        result = toolbox.run({"type": "tool_use", "id": "toolu_1", "name": "current_time", "input": {"tz": "UTC"}})

        assert result == {"type": "tool_result", "tool_use_id": "toolu_1", "content": "09:00"}
        assert recorded(sink) == [
            {
                "type": "tool_call",
                "name": "current_time",
                "input": {"tz": "UTC"},
                "result": "09:00",
                "is_error": False,
                "duration_ms": 500.0,
            }
        ]

    def test_records_tool_errors(self):
        sink = io.StringIO()

        def fail(_):
            raise ToolError("unknown place")

        geocode = Tool("geocode", A_DESCRIPTION, AN_INPUT_SCHEMA, fail)
        toolbox = TracedToolbox(Toolbox([geocode]), Tracer(sink), timer(A_TIMER_READING, A_TIMER_READING))

        toolbox.run({"type": "tool_use", "id": "toolu_1", "name": "geocode", "input": {}})

        [event] = recorded(sink)
        assert event["is_error"] is True

    def test_exposes_wrapped_definitions(self):
        clock = Tool("current_time", A_DESCRIPTION, AN_INPUT_SCHEMA, lambda _: "09:00")
        toolbox = Toolbox([clock])

        assert TracedToolbox(toolbox, Tracer(io.StringIO())).definitions == toolbox.definitions
