from sasoi.agent import Agent
from sasoi.claude_client import Reply
from sasoi.conversation import Conversation
from sasoi.tools.tool import Tool
from sasoi.tools.toolbox import Toolbox


def text_reply(text: str) -> Reply:
    return Reply([{"type": "text", "text": text}], "end_turn")


class FakeClient:
    def __init__(self, *replies: Reply):
        self._replies = list(replies)
        self.calls: list[list[dict]] = []

    def send(self, messages: list[dict], tools: list[dict]) -> Reply:
        self.calls.append(messages)
        return self._replies.pop(0)


A_DESCRIPTION = "Does something"
AN_INPUT_SCHEMA = {"type": "object"}


class TestAgent:
    def test_sends_history_with_each_prompt(self):
        client = FakeClient(text_reply("Hi!"), text_reply("You said hello"))
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
        assert answers == ["Hi!", "You said hello"]

    def test_runs_requested_tool_and_sends_result_back(self):
        tool_use = {"type": "tool_use", "id": "toolu_1", "name": "current_time", "input": {}}
        client = FakeClient(Reply([tool_use], "tool_use"), text_reply("It is 09:00"))
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
        assert answer == "It is 09:00"

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
            text_reply("45 minutes until 18:00"),
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
        assert answer == "45 minutes until 18:00"
