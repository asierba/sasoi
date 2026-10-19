import logging
import os
import sys
import time
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

import psycopg
from dotenv import load_dotenv
from yoyo import get_backend, read_migrations

from sasoi.cli import RED, RESET
from sasoi.ingest.garmin_login import login as garmin_login
from sasoi.ingest.garmin_source import MAX_RECENT_RUNS, GarminSource
from sasoi.ingest.raw_store import RawStore
from sasoi.ingest.sync import sync_garmin

MIGRATIONS_DIR = Path("migrations")
LOG_FORMAT = "%(asctime)s %(levelname)s %(name)s: %(message)s"

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class SyncConfig:
    database_url: str
    garmin_limit: int
    log_level: str


def load_config(env: Mapping[str, str]) -> SyncConfig:
    return SyncConfig(_required(env, "DATABASE_URL"), _garmin_limit(env), _log_level(env))


def _garmin_limit(env: Mapping[str, str]) -> int:
    limit = int(_required(env, "SASOI_GARMIN_LIMIT"))
    if limit > MAX_RECENT_RUNS:
        raise SystemExit(f"{RED}Error: SASOI_GARMIN_LIMIT cannot exceed {MAX_RECENT_RUNS}{RESET}")
    return limit


def _log_level(env: Mapping[str, str]) -> str:
    level = _required(env, "SASOI_LOG_LEVEL")
    if level not in logging.getLevelNamesMapping():
        raise SystemExit(f"{RED}Error: SASOI_LOG_LEVEL {level} is not a logging level{RESET}")
    return level


def configure_logging(level: str) -> None:
    logging.basicConfig(level=logging.WARNING, format=LOG_FORMAT, stream=sys.stdout)
    logging.getLogger("sasoi").setLevel(level)


def _required(env: Mapping[str, str], name: str) -> str:
    value = env.get(name)
    if not value:
        raise SystemExit(f"{RED}Error: {name} is not set{RESET}")
    return value


def migrate(database_url: str) -> None:
    backend = get_backend(database_url.replace("postgresql://", "postgresql+psycopg://", 1))
    with backend.lock():
        backend.apply_migrations(backend.to_apply(read_migrations(str(MIGRATIONS_DIR))))


def main() -> None:
    load_dotenv(".env")
    config = load_config(os.environ)
    configure_logging(config.log_level)
    started = time.monotonic()
    log.info("garmin sync started, limit %d", config.garmin_limit)
    migrate(config.database_url)
    with psycopg.connect(config.database_url, autocommit=True) as conn:
        new_runs = sync_garmin(GarminSource(garmin_login()), RawStore(conn), config.garmin_limit)
    log.info("garmin sync finished: %d new runs in %.0fs", new_runs, time.monotonic() - started)
