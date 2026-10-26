import os
from datetime import datetime
from pathlib import Path

import httpx
import psycopg
from dotenv import load_dotenv

from sasoi.app import Config, load_config
from sasoi.evals.cases import load_cases
from sasoi.evals.evaluator import Evaluator
from sasoi.evals.report import line, summary
from sasoi.settings import SettingError

CASES_PATH = Path("evals/runs.toml")
RUNS_DIR = Path("traces/evals")


def main() -> None:
    load_dotenv(".env")
    config = _config()
    run_dir = _run_dir()
    with (
        httpx.Client(timeout=60, trust_env=False) as http,
        psycopg.connect(config.reader_database_url, autocommit=True) as db,
    ):
        evaluator = Evaluator(config, http, db, run_dir)
        grades = []
        for case in load_cases(CASES_PATH):
            case_grade = evaluator.evaluate(case)
            grades.append(case_grade)
            print(line(case_grade))
    print(summary(grades, run_dir))


def _config() -> Config:
    try:
        return load_config(os.environ)
    except SettingError as error:
        raise SystemExit(f"Error: {error}") from error


def _run_dir() -> Path:
    run_dir = RUNS_DIR / f"{datetime.now():%Y%m%d-%H%M%S}"
    run_dir.mkdir(parents=True)
    return run_dir
