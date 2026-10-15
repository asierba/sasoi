from sasoi.claude_client import ClaudeApiError
from sasoi.cli import RED, RESET, repl
from sasoi.conversation import Conversation


class FakeClient:
    def __init__(self, *replies: str | Exception):
        self._replies = list(replies)
        self.calls: list[list[dict]] = []

    def send(self, messages: list[dict]) -> str:
        self.calls.append(messages)
        reply = self._replies.pop(0)
        if isinstance(reply, Exception):
            raise reply
        return reply


def typed(*lines: str):
    pending = list(lines)

    def read(prompt: str) -> str:
        if not pending:
            raise EOFError
        return pending.pop(0)

    return read


def test_repl_sends_history_with_each_prompt():
    client = FakeClient("Hi!", "You said hello")
    written: list[str] = []

    repl(Conversation(), client, read=typed("hello", "what did I say?"), write=written.append)

    assert client.calls[1] == [
        {"role": "user", "content": "hello"},
        {"role": "assistant", "content": "Hi!"},
        {"role": "user", "content": "what did I say?"},
    ]
    assert written == ["Hi!", "You said hello"]


def test_repl_skips_empty_prompts():
    client = FakeClient()

    repl(Conversation(), client, read=typed("   ", ""), write=lambda text: None)

    assert client.calls == []


def test_repl_shows_api_error_in_red_and_keeps_going():
    client = FakeClient(ClaudeApiError(529, "overloaded_error", "Overloaded"), "Hi!")
    written: list[str] = []

    repl(Conversation(), client, read=typed("hello", "again"), write=written.append)

    assert written == [f"{RED}Error: 529 overloaded_error: Overloaded{RESET}", "Hi!"]
