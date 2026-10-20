import os
import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Protocol, TextIO

import httpx
import psycopg
from dotenv import load_dotenv

from sasoi.agent import Agent, Answer
from sasoi.claude_client import MAX_TOKENS, ClaudeClient, ClaudeError
from sasoi.conversation import Conversation
from sasoi.open_meteo_client import OpenMeteoClient
from sasoi.pricing import PRICES, Price
from sasoi.retrying import RetryingClient
from sasoi.settings import SettingError, required
from sasoi.system_prompt import system_prompt
from sasoi.tools.current_time import current_time
from sasoi.tools.geocode import geocode
from sasoi.tools.run_sql import run_sql
from sasoi.tools.schema_description import schema_description
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
    reader_database_url: str


def load_config(env: Mapping[str, str]) -> Config:
    return Config(
        required(env, "ANTHROPIC_API_KEY"), required(env, "SASOI_MODEL"), required(env, "READER_DATABASE_URL")
    )


def main() -> None:
    load_dotenv(".env")
    config = _config()
    with (
        httpx.Client(timeout=60, trust_env=False) as http,
        psycopg.connect(config.reader_database_url, autocommit=True) as db,
        _trace_file() as trace_file,
    ):
        tracer = Tracer(trace_file)
        tracer.record({"type": "session", "model": config.model, "max_tokens": MAX_TOKENS})
        repl(_agent(config, http, db, tracer), PRICES.get(config.model))


def _config() -> Config:
    try:
        return load_config(os.environ)
    except SettingError as error:
        raise SystemExit(f"{RED}Error: {error}{RESET}") from error


def _trace_file() -> TextIO:
    TRACES_DIR.mkdir(exist_ok=True)
    return (TRACES_DIR / f"{datetime.now():%Y%m%d-%H%M%S}.jsonl").open("w")


def _agent(config: Config, http: httpx.Client, db: psycopg.Connection, tracer: Tracer) -> Agent:
    client = RetryingClient(
        TracedClient(ClaudeClient(config.api_key, config.model, http), tracer),
        sleep=TracedSleep(time.sleep, tracer),
    )
    toolbox = TracedToolbox(_toolbox(http, db), tracer)
    return Agent(Conversation(), client, toolbox, system_prompt())


def _toolbox(http: httpx.Client, db: psycopg.Connection) -> Toolbox:
    open_meteo = OpenMeteoClient(http)
    return Toolbox(
        [current_time, geocode(open_meteo), weather_history(open_meteo), run_sql(db, schema_description(db))]
    )


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
