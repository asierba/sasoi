from typing import Protocol

from sasoi.claude_client import Reply
from sasoi.conversation import Conversation
from sasoi.tools.toolbox import Toolbox


class ChatClient(Protocol):
    def send(self, messages: list[dict], tools: list[dict]) -> Reply: ...


class Agent:
    def __init__(self, conversation: Conversation, client: ChatClient, toolbox: Toolbox):
        self._conversation = conversation
        self._client = client
        self._toolbox = toolbox

    def ask(self, prompt: str) -> str:
        self._conversation.add_user_message(prompt)
        reply = self._send()
        while reply.stop_reason == "tool_use":
            self._conversation.add_assistant_message(reply.content)
            self._conversation.add_tool_results([self._toolbox.run(call) for call in reply.tool_calls])
            reply = self._send()
        self._conversation.add_assistant_message(reply.content)
        return reply.text

    def _send(self) -> Reply:
        return self._client.send(self._conversation.messages, self._toolbox.definitions)
