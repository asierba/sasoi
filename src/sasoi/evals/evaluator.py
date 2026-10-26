import json
from pathlib import Path

import httpx
import psycopg

from sasoi.app import Config, build_agent
from sasoi.claude_client import ClaudeError
from sasoi.evals.cases import Case
from sasoi.evals.grading import Grade, QueryResult
from sasoi.tools.run_sql import run_sql
from sasoi.tracing import Tracer


class Evaluator:
    def __init__(self, config: Config, http: httpx.Client, db: psycopg.Connection, run_dir: Path):
        self._config = config
        self._http = http
        self._db = db
        self._run_dir = run_dir

    def evaluate(self, case: Case) -> Grade:
        trace_path = self._run_dir / f"{case.id}.jsonl"
        try:
            self._ask(case.question, trace_path)
        except ClaudeError as error:
            return Grade.agent_failed(case.id, error)
        ground_truth_csv = run_sql(self._db, "").run({"query": case.sql})
        ground_truth = QueryResult.from_csv(ground_truth_csv)
        agent_results = [
            QueryResult.from_csv(csv) for csv in _successful_run_sql_results(_read_trace_events(trace_path))
        ]
        return Grade.compare(case.id, ground_truth, agent_results)

    def _ask(self, question: str, trace_path: Path) -> None:
        with trace_path.open("w") as trace_file:
            build_agent(self._config, self._http, self._db, Tracer(trace_file)).ask(question)


def _read_trace_events(trace_path: Path) -> list[dict]:
    return [json.loads(line) for line in trace_path.read_text().splitlines()]


def _successful_run_sql_results(trace_events: list[dict]) -> list[str]:
    return [
        event["result"]
        for event in trace_events
        if event["type"] == "tool_call" and event["name"] == "run_sql" and not event["is_error"]
    ]
