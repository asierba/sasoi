import json
import time
from collections.abc import Callable
from typing import TextIO

from sasoi.agent import ChatClient, Tools
from sasoi.claude_client import ClaudeApiError, ClaudeError, Reply

Timer = Callable[[], float]


class Tracer:
    def __init__(self, sink: TextIO):
        self._sink = sink

    def record(self, event: dict) -> None:
        self._sink.write(json.dumps(event, ensure_ascii=False) + "\n")
        self._sink.flush()


def error_outcome(error: ClaudeError) -> dict:
    if isinstance(error, ClaudeApiError) and error.retry_after is not None:
        return {"error": str(error), "retry_after": error.retry_after}
    return {"error": str(error)}


class TracedClient:
    def __init__(self, client: ChatClient, tracer: Tracer, timer: Timer = time.perf_counter):
        self._client = client
        self._tracer = tracer
        self._timer = timer

    def send(self, messages: list[dict], tools: list[dict]) -> Reply:
        start = self._timer()
        try:
            reply = self._client.send(messages, tools)
        except ClaudeError as error:
            self._record(messages, tools, start, error_outcome(error))
            raise
        self._record(messages, tools, start, {"content": reply.content, "stop_reason": reply.stop_reason})
        return reply

    def _record(self, messages: list[dict], tools: list[dict], start: float, outcome: dict) -> None:
        duration_ms = (self._timer() - start) * 1000
        self._tracer.record(
            {"type": "claude_call", "messages": messages, "tools": tools, **outcome, "duration_ms": duration_ms}
        )


class TracedSleep:
    def __init__(self, sleep: Callable[[float], None], tracer: Tracer):
        self._sleep = sleep
        self._tracer = tracer

    def __call__(self, seconds: float) -> None:
        self._tracer.record({"type": "retry_wait", "seconds": seconds})
        self._sleep(seconds)


class TracedToolbox:
    def __init__(self, toolbox: Tools, tracer: Tracer, timer: Timer = time.perf_counter):
        self._toolbox = toolbox
        self._tracer = tracer
        self._timer = timer

    @property
    def definitions(self) -> list[dict]:
        return self._toolbox.definitions

    def run(self, call: dict) -> dict:
        start = self._timer()
        result = self._toolbox.run(call)
        self._tracer.record(
            {
                "type": "tool_call",
                "name": call["name"],
                "input": call["input"],
                "result": result["content"],
                "is_error": result.get("is_error", False),
                "duration_ms": (self._timer() - start) * 1000,
            }
        )
        return result
