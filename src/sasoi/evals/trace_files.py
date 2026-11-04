import json
from pathlib import Path

from sasoi.claude_client import Usage


def usage_in_trace_files(traces_dir: Path) -> Usage:
    return sum((Usage(**event["usage"]) for event in _answered_claude_calls(traces_dir)), Usage())


def _answered_claude_calls(traces_dir: Path) -> list[dict]:
    return [event for event in _trace_events(traces_dir) if event["type"] == "claude_call" and "usage" in event]


def _trace_events(traces_dir: Path) -> list[dict]:
    return [json.loads(line) for trace in traces_dir.rglob("*.jsonl") for line in trace.read_text().splitlines()]
