import argparse
import os
from datetime import datetime
from pathlib import Path

import httpx
import psycopg
from dotenv import load_dotenv

from sasoi.app import Config, load_config
from sasoi.evals.cases import load_cases
from sasoi.evals.evaluator import Evaluator
from sasoi.evals.report import line, pass_rates, summary
from sasoi.settings import SettingError

CASES_PATH = Path("evals/runs.toml")
RUNS_DIR = Path("traces/evals")


def main() -> None:
    repeat = _repeat()
    load_dotenv(".env")
    config = _config()
    run_dir = _run_dir()
    cases = load_cases(CASES_PATH)
    grades = []
    with (
        httpx.Client(timeout=60, trust_env=False) as http,
        psycopg.connect(config.reader_database_url, autocommit=True) as db,
    ):
        for attempt in range(1, repeat + 1):
            print(f"Run {attempt}/{repeat}")
            evaluator = Evaluator(config, http, db, _attempt_dir(run_dir, attempt))
            for case in cases:
                case_grade = evaluator.evaluate(case)
                grades.append(case_grade)
                print(line(case_grade))
    if repeat > 1:
        print(pass_rates(grades))
    print(summary(grades, run_dir))


def _repeat() -> int:
    parser = argparse.ArgumentParser(description="Ask every eval question and grade the agent's SQL results.")
    parser.add_argument("--repeat", type=int, default=1, help="run every case this many times")
    return parser.parse_args().repeat


def _config() -> Config:
    try:
        return load_config(os.environ)
    except SettingError as error:
        raise SystemExit(f"Error: {error}") from error


def _run_dir() -> Path:
    run_dir = RUNS_DIR / f"{datetime.now():%Y%m%d-%H%M%S}"
    run_dir.mkdir(parents=True)
    return run_dir


def _attempt_dir(run_dir: Path, attempt: int) -> Path:
    attempt_dir = run_dir / str(attempt)
    attempt_dir.mkdir()
    return attempt_dir
