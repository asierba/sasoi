import json
from pathlib import Path

from sasoi.claude_client import Usage
from sasoi.evals.usage import usage_in_trace_files


def a_trace(path: Path, *events: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(event) + "\n" for event in events))


def a_claude_call(input_tokens: int, output_tokens: int) -> dict:
    return {"type": "claude_call", "usage": {"input_tokens": input_tokens, "output_tokens": output_tokens}}


class TestUsageInTraceFiles:
    def test_adds_the_usage_of_every_claude_call_in_every_attempt(self, tmp_path):
        a_trace(tmp_path / "1/a-case.jsonl", a_claude_call(100, 10), a_claude_call(200, 20))
        a_trace(tmp_path / "2/a-case.jsonl", a_claude_call(300, 30))

        assert usage_in_trace_files(tmp_path) == Usage(600, 60)

    def test_ignores_other_events_and_failed_calls(self, tmp_path):
        a_trace(
            tmp_path / "1/a-case.jsonl",
            {"type": "session", "model": "a model"},
            a_claude_call(100, 10),
            {"type": "claude_call", "error": "an error"},
            {"type": "tool_call", "name": "a_tool"},
        )

        assert usage_in_trace_files(tmp_path) == Usage(100, 10)

    def test_is_zero_for_a_run_without_traces(self, tmp_path):
        assert usage_in_trace_files(tmp_path) == Usage()
