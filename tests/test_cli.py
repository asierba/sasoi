from sasoi.cli import repl
from sasoi.conversation import Conversation


class FakeClient:
    def __init__(self, *replies: str):
        self._replies = list(replies)
        self.calls: list[list[dict]] = []

    def send(self, messages: list[dict]) -> str:
        self.calls.append(messages)
        return self._replies.pop(0)


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
