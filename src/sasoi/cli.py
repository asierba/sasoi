import os
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import Protocol, TextIO

import httpx
import psycopg
from dotenv import load_dotenv

from sasoi.agent import Answer
from sasoi.app import Config, build_agent, load_config
from sasoi.claude_client import MAX_TOKENS, ClaudeError
from sasoi.pricing import PRICES, Price
from sasoi.settings import SettingError
from sasoi.tracing import Tracer

TRACES_DIR = Path("traces")
RED = "\033[31m"
YELLOW = "\033[33m"
DIM = "\033[2m"
GREY = "\033[90m"
RESET = "\033[0m"


class ChatAgent(Protocol):
    def ask(self, prompt: str) -> Answer: ...


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
        repl(build_agent(config, http, db, tracer), PRICES.get(config.model))


def _config() -> Config:
    try:
        return load_config(os.environ)
    except SettingError as error:
        raise SystemExit(f"{RED}Error: {error}{RESET}") from error


def _trace_file() -> TextIO:
    TRACES_DIR.mkdir(exist_ok=True)
    return (TRACES_DIR / f"{datetime.now():%Y%m%d-%H%M%S}.jsonl").open("w")


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
        write(f"{GREY}working…{RESET}")
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
