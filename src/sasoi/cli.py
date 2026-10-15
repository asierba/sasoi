import os
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Protocol

import httpx
from dotenv import load_dotenv

from sasoi.claude_client import ClaudeClient, ClaudeError
from sasoi.conversation import Conversation

DEFAULT_MODEL = "claude-haiku-5-5"
RED = "\033[31m"
YELLOW = "\033[33m"
RESET = "\033[0m"


class ChatClient(Protocol):
    def send(self, messages: list[dict]) -> str: ...


@dataclass(frozen=True)
class Config:
    api_key: str
    model: str


def load_config(env: Mapping[str, str]) -> Config:
    api_key = env.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise SystemExit(f"{RED}Error: ANTHROPIC_API_KEY is not set{RESET}")
    return Config(api_key, env.get("SASOI_MODEL", DEFAULT_MODEL))


def main() -> None:
    load_dotenv(".env")
    config = load_config(os.environ)
    with httpx.Client(timeout=60, trust_env=False) as http:
        repl(Conversation(), ClaudeClient(config.api_key, config.model, http))


def repl(
    conversation: Conversation,
    client: ChatClient,
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
        try:
            reply = client.send(conversation.messages)
        except ClaudeError as error:
            write(f"{RED}Error: {error}{RESET}")
            continue
        except KeyboardInterrupt:
            write(f"{YELLOW}Interrupted{RESET}")
            continue
        conversation.add_assistant_message(reply)
        write(reply)
