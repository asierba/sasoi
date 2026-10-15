import os
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Protocol

import httpx
from dotenv import load_dotenv

from sasoi.claude_client import ClaudeClient, ClaudeError, Reply
from sasoi.conversation import Conversation
from sasoi.open_meteo_client import OpenMeteoClient
from sasoi.tools.current_time import current_time
from sasoi.tools.geocode import geocode
from sasoi.tools.toolbox import Toolbox
from sasoi.tools.weather_history import weather_history

DEFAULT_MODEL = "claude-haiku-5-5"
RED = "\033[31m"
YELLOW = "\033[33m"
RESET = "\033[0m"


class ChatClient(Protocol):
    def send(self, messages: list[dict], tools: list[dict]) -> Reply: ...


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
        client = ClaudeClient(config.api_key, config.model, http)
        open_meteo = OpenMeteoClient(http)
        repl(Conversation(), client, Toolbox([current_time, geocode(open_meteo), weather_history(open_meteo)]))


def repl(
    conversation: Conversation,
    client: ChatClient,
    toolbox: Toolbox,
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
            reply = client.send(conversation.messages, toolbox.definitions)
            while reply.stop_reason == "tool_use":
                conversation.add_assistant_message(reply.content)
                conversation.add_tool_results([toolbox.run(call) for call in reply.tool_calls])
                reply = client.send(conversation.messages, toolbox.definitions)
        except ClaudeError as error:
            write(f"{RED}Error: {error}{RESET}")
            continue
        except KeyboardInterrupt:
            write(f"{YELLOW}Interrupted{RESET}")
            continue
        conversation.add_assistant_message(reply.content)
        write(reply.text)
