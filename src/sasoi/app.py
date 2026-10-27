import time
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

import httpx
import psycopg

from sasoi.agent import Agent
from sasoi.claude_client import ClaudeClient
from sasoi.commands import COMMANDS
from sasoi.conversation import Conversation
from sasoi.open_meteo_client import OpenMeteoClient
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


@dataclass(frozen=True)
class Config:
    api_key: str
    model: str
    reader_database_url: str
    athlete_profile: str


_ATHLETE_PROFILE_PATH = Path("data/athlete_profile.md")


def load_config(env: Mapping[str, str]) -> Config:
    return Config(
        required(env, "ANTHROPIC_API_KEY"),
        required(env, "SASOI_MODEL"),
        required(env, "READER_DATABASE_URL"),
        _athlete_profile(_ATHLETE_PROFILE_PATH),
    )


def _athlete_profile(path: Path) -> str:
    try:
        return path.read_text()
    except FileNotFoundError as error:
        raise SettingError(f"Missing {path}") from error


def build_agent(config: Config, http: httpx.Client, db: psycopg.Connection, tracer: Tracer) -> Agent:
    client = RetryingClient(
        TracedClient(ClaudeClient(config.api_key, config.model, http), tracer),
        sleep=TracedSleep(time.sleep, tracer),
    )
    toolbox = TracedToolbox(_toolbox(http, db), tracer)
    return Agent(Conversation(), client, toolbox, system_prompt(config.athlete_profile), COMMANDS)


def _toolbox(http: httpx.Client, db: psycopg.Connection) -> Toolbox:
    open_meteo = OpenMeteoClient(http)
    return Toolbox(
        [current_time, geocode(open_meteo), weather_history(open_meteo), run_sql(db, schema_description(db))]
    )
