import os
import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Protocol

import httpx
from dotenv import load_dotenv

from sasoi.agent import Agent
from sasoi.claude_client import MAX_TOKENS, ClaudeClient, ClaudeError
from sasoi.conversation import Conversation
from sasoi.open_meteo_client import OpenMeteoClient
from sasoi.retrying import RetryingClient
from sasoi.tools.current_time import current_time
from sasoi.tools.geocode import geocode
from sasoi.tools.toolbox import Toolbox
from sasoi.tools.weather_history import weather_history
from sasoi.tracing import TracedClient, TracedSleep, TracedToolbox, Tracer

DEFAULT_MODEL = "claude-haiku-5-5"
TRACES_DIR = Path("traces")
RED = "\033[31m"
YELLOW = "\033[33m"
RESET = "\033[0m"


class ChatAgent(Protocol):
    def ask(self, prompt: str) -> str: ...


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
    TRACES_DIR.mkdir(exist_ok=True)
    trace_path = TRACES_DIR / f"{datetime.now():%Y%m%d-%H%M%S}.jsonl"
    with httpx.Client(timeout=60, trust_env=False) as http, trace_path.open("w") as trace_file:
        tracer = Tracer(trace_file)
        tracer.record({"type": "session", "model": config.model, "max_tokens": MAX_TOKENS})
        client = RetryingClient(
            TracedClient(ClaudeClient(config.api_key, config.model, http), tracer),
            sleep=TracedSleep(time.sleep, tracer),
        )
        open_meteo = OpenMeteoClient(http)
        toolbox = TracedToolbox(Toolbox([current_time, geocode(open_meteo), weather_history(open_meteo)]), tracer)
        repl(Agent(Conversation(), client, toolbox))


def repl(
    agent: ChatAgent,
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
        try:
            answer = agent.ask(prompt)
        except ClaudeError as error:
            write(f"{RED}Error: {error}{RESET}")
            continue
        except KeyboardInterrupt:
            write(f"{YELLOW}Interrupted{RESET}")
            continue
        write(answer)
