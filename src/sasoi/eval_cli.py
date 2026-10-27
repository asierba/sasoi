import argparse
import os
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from functools import partial
from pathlib import Path

import httpx
import psycopg
from dotenv import load_dotenv

from sasoi.app import Config, load_config
from sasoi.evals.cases import Case, load_cases
from sasoi.evals.evaluator import Evaluator
from sasoi.evals.grading import Grade
from sasoi.evals.report import line, pass_rates, summary
from sasoi.settings import SettingError

CASES_PATH = Path("evals/runs.toml")
RUNS_DIR = Path("traces/evals")


def main() -> None:
    args = _args()
    load_dotenv(".env")
    config = _config()
    run_dir = _run_dir()
    cases = load_cases(CASES_PATH)
    grades = []
    with httpx.Client(timeout=60, trust_env=False) as http, ThreadPoolExecutor(args.workers) as pool:
        for attempt in range(1, args.repeat + 1):
            print(f"Run {attempt}/{args.repeat}")
            attempt_dir = _attempt_dir(run_dir, attempt)
            for case_grade in pool.map(partial(_evaluate, config, http, attempt_dir), cases):
                grades.append(case_grade)
                print(line(case_grade))
    if args.repeat > 1:
        print(pass_rates(grades))
    print(summary(grades, run_dir))
    if not all(grade.passed for grade in grades):
        raise SystemExit(1)


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ask every eval question and grade the agent's SQL results.")
    parser.add_argument("--repeat", type=int, default=1, help="run every case this many times")
    parser.add_argument("--workers", type=int, default=8, help="cases evaluated at the same time")
    return parser.parse_args()


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


def _evaluate(config: Config, http: httpx.Client, attempt_dir: Path, case: Case) -> Grade:
    with psycopg.connect(config.reader_database_url, autocommit=True) as db:
        return Evaluator(config, http, db, attempt_dir).evaluate(case)
