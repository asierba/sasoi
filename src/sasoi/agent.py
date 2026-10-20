from dataclasses import dataclass
from typing import Protocol

from sasoi.claude_client import ClaudeError, Reply, Request, Usage
from sasoi.conversation import Conversation


FINAL_STOP_REASONS = {"end_turn", "stop_sequence"}


class UnexpectedStopError(ClaudeError):
    def __init__(self, stop_reason: str):
        super().__init__(f"reply stopped with {stop_reason}")
        self.stop_reason = stop_reason


@dataclass(frozen=True)
class Answer:
    text: str
    usage: Usage


class ChatClient(Protocol):
    def send(self, request: Request) -> Reply: ...


class Tools(Protocol):
    @property
    def definitions(self) -> list[dict]: ...

    def run(self, call: dict) -> dict: ...


class Agent:
    def __init__(self, conversation: Conversation, client: ChatClient, toolbox: Tools, system_prompt: str):
        self._conversation = conversation
        self._client = client
        self._toolbox = toolbox
        self._system_prompt = system_prompt

    def ask(self, prompt: str) -> Answer:
        self._conversation.add_user_message(prompt)
        reply = self._send()
        usage = reply.usage
        while reply.stop_reason == "tool_use":
            self._conversation.add_assistant_message(reply.content)
            self._conversation.add_tool_results([self._toolbox.run(call) for call in reply.tool_calls])
            reply = self._send()
            usage += reply.usage
        if reply.stop_reason not in FINAL_STOP_REASONS:
            raise UnexpectedStopError(reply.stop_reason)
        self._conversation.add_assistant_message(reply.content)
        return Answer(reply.text, usage)

    def _send(self) -> Reply:
        return self._client.send(Request(self._system_prompt, self._conversation.messages, self._toolbox.definitions))
