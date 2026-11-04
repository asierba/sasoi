import os
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import Protocol, TextIO

import httpx
import psycopg
import rich
from dotenv import load_dotenv
from prompt_toolkit import PromptSession
from prompt_toolkit.application import get_app
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.filters import Condition
from prompt_toolkit.key_binding import KeyBindings, KeyPressEvent
from prompt_toolkit.styles import Style
from rich.markdown import Markdown

from sasoi.agent import Answer
from sasoi.app import Config, build_agent, load_config
from sasoi.claude_client import ClaudeError
from sasoi.pricing import PRICES, Price, usage_summary
from sasoi.settings import SettingError
from sasoi.tracing import Tracer

TRACES_DIR = Path("traces")
RED = "\033[31m"
YELLOW = "\033[33m"
DIM = "\033[2m"
GREY = "\033[90m"
RESET = "\033[0m"
PROMPT_STYLE = Style.from_dict({"prompt": "ansicyan bold", "": "bold"})


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
        tracer.record_session(config.model)
        agent = build_agent(config, http, db, tracer)
        session = PromptSession(
            completer=WordCompleter(list(agent.commands), meta_dict=agent.commands, sentence=True),
            style=PROMPT_STYLE,
            key_bindings=line_break_bindings(),
        )
        repl(
            agent,
            config.model,
            PRICES.get(config.model),
            read=lambda message: session.prompt([("class:prompt", message)]),
        )


def _config() -> Config:
    try:
        return load_config(os.environ)
    except SettingError as error:
        raise SystemExit(f"{RED}Error: {error}{RESET}") from error


def _trace_file() -> TextIO:
    TRACES_DIR.mkdir(exist_ok=True)
    return (TRACES_DIR / f"{datetime.now():%Y%m%d-%H%M%S}.jsonl").open("w")


def line_break_bindings() -> KeyBindings:
    bindings = KeyBindings()
    bindings.add("enter", filter=_backslash_before_cursor)(_replace_backslash_with_line_break)
    # VS Code sends shift+enter as backslash, CR, LF: without this the LF would submit the prompt
    bindings.add("c-j")(lambda event: None)
    return bindings


@Condition
def _backslash_before_cursor() -> bool:
    return get_app().current_buffer.document.text_before_cursor.endswith("\\")


def _replace_backslash_with_line_break(event: KeyPressEvent) -> None:
    event.current_buffer.delete_before_cursor()
    event.current_buffer.insert_text("\n")


def usage_line(answer: Answer, model: str, price: Price | None) -> str:
    return f"{DIM}{usage_summary(model, answer.usage, price)}{RESET}"


def print_markdown(text: str) -> None:
    rich.print(Markdown(text))


def repl(
    agent: ChatAgent,
    model: str,
    price: Price | None = None,
    read: Callable[[str], str] = input,
    write: Callable[[str], None] = print,
    write_markdown: Callable[[str], None] = print_markdown,
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
        write_markdown(answer.text)
        write(usage_line(answer, model, price))
        write_markdown("---")
