import pytest

from sasoi.agent import Agent, UnexpectedStopError
from sasoi.claude_client import Reply, Request, Usage
from sasoi.conversation import Conversation
from sasoi.tools.tool import Tool
from sasoi.tools.toolbox import Toolbox


def a_text_reply(text: str) -> Reply:
    return Reply([{"type": "text", "text": text}], "end_turn")


class FakeClient:
    def __init__(self, *replies: Reply):
        self._replies = list(replies)
        self.calls: list[list[dict]] = []

    def send(self, request: Request) -> Reply:
        self.calls.append(request.messages)
        return self._replies.pop(0)


A_DESCRIPTION = "Does something"
AN_INPUT_SCHEMA = {"type": "object"}
A_PROMPT = "a prompt"
A_TEXT_CONTENT = [{"type": "text", "text": "a reply"}]
A_TOOL = Tool("a_tool", A_DESCRIPTION, AN_INPUT_SCHEMA, lambda _: "a result")
A_TOOL_CALL = {"type": "tool_use", "id": "toolu_1", "name": "a_tool", "input": {}}


class TestAgent:
    def test_sends_history_with_each_prompt(self):
        client = FakeClient(a_text_reply("Hi!"), a_text_reply("You said hello"))
        agent = Agent(Conversation(), client, Toolbox([]))

        answers = [agent.ask("hello"), agent.ask("what did I say?")]

        assert client.calls == [
            [
                {"role": "user", "content": "hello"},
            ],
            [
                {"role": "user", "content": "hello"},
                {"role": "assistant", "content": [{"type": "text", "text": "Hi!"}]},
                {"role": "user", "content": "what did I say?"},
            ],
        ]
        assert [answer.text for answer in answers] == ["Hi!", "You said hello"]

    def test_runs_requested_tool_and_sends_result_back(self):
        tool_use = {"type": "tool_use", "id": "toolu_1", "name": "current_time", "input": {}}
        client = FakeClient(Reply([tool_use], "tool_use"), a_text_reply("It is 09:00"))
        clock = Tool("current_time", A_DESCRIPTION, AN_INPUT_SCHEMA, lambda _: "09:00")

        answer = Agent(Conversation(), client, Toolbox([clock])).ask("what time is it?")

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
        assert answer.text == "It is 09:00"

    def test_keeps_running_tools_until_claude_stops_asking(self):
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
            a_text_reply("45 minutes until 18:00"),
        )
        clock = Tool("current_time", A_DESCRIPTION, AN_INPUT_SCHEMA, lambda _: "17:15")
        calculator = Tool("calculator", A_DESCRIPTION, AN_INPUT_SCHEMA, lambda _: "45")

        agent = Agent(Conversation(), client, Toolbox([clock, calculator]))

        answer = agent.ask("how many minutes until 18:00?")

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
        assert answer.text == "45 minutes until 18:00"

    def test_returns_text_when_stopped_by_stop_sequence(self):
        client = FakeClient(Reply([{"type": "text", "text": "Done"}], "stop_sequence"))

        answer = Agent(Conversation(), client, Toolbox([])).ask(A_PROMPT)

        assert answer.text == "Done"

    @pytest.mark.parametrize("stop_reason", ["max_tokens", "refusal", "pause_turn"])
    def test_raises_when_reply_stops_unexpectedly(self, stop_reason):
        client = FakeClient(Reply(A_TEXT_CONTENT, stop_reason))

        with pytest.raises(UnexpectedStopError, match=f"reply stopped with {stop_reason}"):
            Agent(Conversation(), client, Toolbox([])).ask(A_PROMPT)

    def test_keeps_unexpected_reply_out_of_history(self):
        client = FakeClient(Reply(A_TEXT_CONTENT, "max_tokens"), Reply(A_TEXT_CONTENT, "end_turn"))
        agent = Agent(Conversation(), client, Toolbox([]))

        with pytest.raises(UnexpectedStopError):
            agent.ask("first")
        agent.ask("second")

        [_, second_call] = client.calls
        assert second_call == [
            {"role": "user", "content": "first"},
            {"role": "user", "content": "second"},
        ]

    def test_adds_up_usage_of_every_call_in_the_turn(self):
        client = FakeClient(
            Reply([A_TOOL_CALL], "tool_use", Usage(input_tokens=100, output_tokens=20)),
            Reply(A_TEXT_CONTENT, "end_turn", Usage(input_tokens=150, output_tokens=10)),
        )

        answer = Agent(Conversation(), client, Toolbox([A_TOOL])).ask(A_PROMPT)

        assert answer.usage == Usage(input_tokens=250, output_tokens=30)
