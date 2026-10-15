import pytest

from sasoi.claude_client import ClaudeApiError, Reply
from sasoi.cli import DEFAULT_MODEL, RED, RESET, YELLOW, Config, load_config, repl
from sasoi.conversation import Conversation
from sasoi.tools.tool import Tool
from sasoi.tools.toolbox import Toolbox


def text_reply(text: str) -> Reply:
    return Reply([{"type": "text", "text": text}], "end_turn")


class FakeClient:
    def __init__(self, *replies: Reply | BaseException):
        self._replies = list(replies)
        self.calls: list[list[dict]] = []

    def send(self, messages: list[dict], tools: list[dict]) -> Reply:
        self.calls.append(messages)
        reply = self._replies.pop(0)
        if isinstance(reply, BaseException):
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
    client = FakeClient(text_reply("Hi!"), text_reply("You said hello"))
    written: list[str] = []

    repl(Conversation(), client, Toolbox([]), read=typed("hello", "what did I say?"), write=written.append)

    assert client.calls[1] == [
        {"role": "user", "content": "hello"},
        {"role": "assistant", "content": [{"type": "text", "text": "Hi!"}]},
        {"role": "user", "content": "what did I say?"},
    ]
    assert written == ["Hi!", "You said hello"]


def test_repl_runs_requested_tool_and_sends_result_back():
    tool_use = {"type": "tool_use", "id": "toolu_1", "name": "current_time", "input": {}}
    client = FakeClient(Reply([tool_use], "tool_use"), text_reply("It is 09:00"))
    clock = Tool("current_time", "Now", {"type": "object", "properties": {}}, lambda _: "09:00")
    written: list[str] = []

    repl(Conversation(), client, Toolbox([clock]), read=typed("what time is it?"), write=written.append)

    assert client.calls == [
        [
            {"role": "user", "content": "what time is it?"},
        ],
        [
            {"role": "user", "content": "what time is it?"},
            {"role": "assistant", "content": [tool_use]},
            {
                "role": "user",
                "content": [{"type": "tool_result", "tool_use_id": "toolu_1", "content": "09:00"}],
            },
        ],
    ]
    assert written == ["It is 09:00"]


def test_repl_keeps_running_tools_until_claude_stops_asking():
    time_call = {"type": "tool_use", "id": "toolu_1", "name": "current_time", "input": {}}
    calculator_call = {
        "type": "tool_use",
        "id": "toolu_2",
        "name": "calculator",
        "input": {"expression": "18 * 60 - (17 * 60 + 15)"},
    }
    client = FakeClient(
        Reply([time_call], "tool_use"),
        Reply([calculator_call], "tool_use"),
        text_reply("45 minutes until 18:00"),
    )
    clock = Tool("current_time", "Now", {"type": "object", "properties": {}}, lambda _: "17:15")
    calculator = Tool(
        "calculator",
        "Evaluate an arithmetic expression",
        {"type": "object", "properties": {"expression": {"type": "string"}}, "required": ["expression"]},
        lambda _: "45",
    )
    written: list[str] = []

    repl(
        Conversation(),
        client,
        Toolbox([clock, calculator]),
        read=typed("how many minutes until 18:00?"),
        write=written.append,
    )

    question = {"role": "user", "content": "how many minutes until 18:00?"}
    time_result = {
        "role": "user",
        "content": [{"type": "tool_result", "tool_use_id": "toolu_1", "content": "17:15"}],
    }
    calculator_result = {
        "role": "user",
        "content": [{"type": "tool_result", "tool_use_id": "toolu_2", "content": "45"}],
    }
    assert client.calls == [
        [question],
        [question, {"role": "assistant", "content": [time_call]}, time_result],
        [
            question,
            {"role": "assistant", "content": [time_call]},
            time_result,
            {"role": "assistant", "content": [calculator_call]},
            calculator_result,
        ],
    ]
    assert written == ["45 minutes until 18:00"]


def test_repl_skips_empty_prompts():
    client = FakeClient()

    repl(Conversation(), client, Toolbox([]), read=typed("   ", ""), write=lambda text: None)

    assert client.calls == []


def test_repl_shows_api_error_in_red_and_keeps_going():
    client = FakeClient(ClaudeApiError(529, "overloaded_error", "Overloaded"), text_reply("second reply"))
    written: list[str] = []

    repl(Conversation(), client, Toolbox([]), read=typed("first", "second"), write=written.append)

    assert written == [f"{RED}Error: 529 overloaded_error: Overloaded{RESET}", "second reply"]


def test_repl_shows_interrupted_in_yellow_on_ctrl_c_and_keeps_going():
    client = FakeClient(KeyboardInterrupt(), text_reply("second reply"))
    written: list[str] = []

    repl(Conversation(), client, Toolbox([]), read=typed("first", "second"), write=written.append)

    assert written == [f"{YELLOW}Interrupted{RESET}", "second reply"]


def test_load_config_exits_with_message_when_api_key_missing():
    with pytest.raises(SystemExit) as raised:
        load_config({})

    assert raised.value.code == f"{RED}Error: ANTHROPIC_API_KEY is not set{RESET}"


def test_load_config_uses_default_model_when_not_set():
    assert load_config({"ANTHROPIC_API_KEY": "key"}) == Config("key", DEFAULT_MODEL)
