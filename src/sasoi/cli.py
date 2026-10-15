import os
from collections.abc import Callable

import httpx
from dotenv import load_dotenv

from sasoi.claude_client import ClaudeClient
from sasoi.conversation import Conversation

DEFAULT_MODEL = "claude-haiku-5-5"


def main() -> None:
    load_dotenv(".env")
    api_key = os.environ["ANTHROPIC_API_KEY"]
    model = os.environ.get("SASOI_MODEL", DEFAULT_MODEL)
    with httpx.Client(timeout=60, trust_env=False) as http:
        repl(Conversation(), ClaudeClient(api_key, model, http))


def repl(
    conversation: Conversation,
    client: ClaudeClient,
    read: Callable[[str], str] = input,
    write: Callable[[str], None] = print,
) -> None:
    while True:
        try:
            prompt = read("> ").strip()
        except (EOFError, KeyboardInterrupt):
            # Ctrl-D or Ctrl-C exits
            return
        if not prompt:
            continue
        conversation.add_user_message(prompt)
        reply = client.send(conversation.messages)
        conversation.add_assistant_message(reply)
        write(reply)
