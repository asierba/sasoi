import os
import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Protocol

import httpx
from dotenv import load_dotenv

from sasoi.agent import Agent, Answer
from sasoi.claude_client import MAX_TOKENS, ClaudeClient, ClaudeError
from sasoi.conversation import Conversation
from sasoi.open_meteo_client import OpenMeteoClient
from sasoi.pricing import PRICES, Price
from sasoi.retrying import RetryingClient
from sasoi.settings import SettingError, required
from sasoi.tools.current_time import current_time
from sasoi.tools.geocode import geocode
from sasoi.tools.toolbox import Toolbox
from sasoi.tools.weather_history import weather_history
from sasoi.tracing import TracedClient, TracedSleep, TracedToolbox, Tracer

TRACES_DIR = Path("traces")
RED = "\033[31m"
YELLOW = "\033[33m"
DIM = "\033[2m"
RESET = "\033[0m"


class ChatAgent(Protocol):
    def ask(self, prompt: str) -> Answer: ...


@dataclass(frozen=True)
class Config:
    api_key: str
    model: str


def load_config(env: Mapping[str, str]) -> Config:
    return Config(required(env, "ANTHROPIC_API_KEY"), required(env, "SASOI_MODEL"))


def main() -> None:
    load_dotenv(".env")
    try:
        config = load_config(os.environ)
    except SettingError as error:
        raise SystemExit(f"{RED}Error: {error}{RESET}") from error
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
        repl(Agent(Conversation(), client, toolbox), PRICES.get(config.model))


def usage_line(answer: Answer, price: Price | None) -> str:
    tokens = f"{answer.usage.input_tokens:,} in · {answer.usage.output_tokens:,} out"
    cost = f" · ${price.cost(answer.usage):.4f}" if price else ""
    return f"{DIM}{tokens}{cost}{RESET}"


def repl(
    agent: ChatAgent,
    price: Price | None = None,
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
        write(answer.text)
        write(usage_line(answer, price))
