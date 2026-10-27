import json

import httpx

from sasoi.app import Config
from sasoi.evals.cases import Case
from sasoi.evals.evaluator import Evaluator
from sasoi.evals.grading import Grade

A_CONFIG = Config("a-key", "a-model", "postgresql://unused")
A_QUESTION = "a question"
A_USAGE = {"input_tokens": 1, "output_tokens": 1}


def a_run_sql_reply(query: str) -> httpx.Response:
    tool_use = {"type": "tool_use", "id": "toolu_1", "name": "run_sql", "input": {"query": query}}
    return httpx.Response(200, json={"content": [tool_use], "stop_reason": "tool_use", "usage": A_USAGE})


def a_final_reply() -> httpx.Response:
    return httpx.Response(
        200, json={"content": [{"type": "text", "text": "an answer"}], "stop_reason": "end_turn", "usage": A_USAGE}
    )


def a_claude(*replies: httpx.Response, requests: list[httpx.Request] | None = None) -> httpx.Client:
    pending = list(replies)

    def handler(request: httpx.Request) -> httpx.Response:
        if requests is not None:
            requests.append(request)
        return pending.pop(0)

    return httpx.Client(transport=httpx.MockTransport(handler))


class TestEvaluate:
    def test_asks_the_agent_the_case_question(self, reader, tmp_path):
        requests = []
        http = a_claude(a_final_reply(), requests=requests)

        Evaluator(A_CONFIG, http, reader, tmp_path).evaluate(Case("a-case", "How far did I run?", "SELECT 1"))

        [first_message] = json.loads(requests[0].content)["messages"]
        assert first_message == {"role": "user", "content": "How far did I run?"}

    def test_passes_when_the_agent_query_returns_the_expected_rows(self, reader, tmp_path):
        http = a_claude(a_run_sql_reply("SELECT 30.4 AS total_km, 7 AS runs"), a_final_reply())

        grade = Evaluator(A_CONFIG, http, reader, tmp_path).evaluate(Case("a-case", A_QUESTION, "SELECT 30.4 AS km"))

        assert grade == Grade("a-case", ())

    def test_fails_when_the_agent_query_returns_other_rows(self, reader, tmp_path):
        http = a_claude(a_run_sql_reply("SELECT 34.8 AS km"), a_final_reply())

        grade = Evaluator(A_CONFIG, http, reader, tmp_path).evaluate(Case("a-case", A_QUESTION, "SELECT 30.4 AS km"))

        assert grade == Grade("a-case", ("no run_sql result contains the ground truth",))

    def test_ignores_agent_queries_that_errored(self, reader, tmp_path):
        http = a_claude(a_run_sql_reply("SELECT pace FROM nowhere"), a_final_reply())

        grade = Evaluator(A_CONFIG, http, reader, tmp_path).evaluate(Case("a-case", A_QUESTION, "SELECT 30.4 AS km"))

        assert grade == Grade("a-case", ("run_sql never returned a result",))

    def test_fails_when_the_agent_raises(self, reader, tmp_path):
        error = {"type": "error", "error": {"type": "invalid_request_error", "message": "Bad request"}}
        http = a_claude(httpx.Response(400, json=error))

        grade = Evaluator(A_CONFIG, http, reader, tmp_path).evaluate(Case("a-case", A_QUESTION, "SELECT 1"))

        assert grade == Grade("a-case", ("agent failed: 400 invalid_request_error: Bad request",))

    def test_fails_when_the_ground_truth_query_raises(self, reader, tmp_path):
        http = a_claude(a_final_reply())

        grade = Evaluator(A_CONFIG, http, reader, tmp_path).evaluate(Case("a-case", A_QUESTION, "SELECT 1 / 0"))

        assert grade == Grade("a-case", ("ground truth failed: division by zero",))

    def test_writes_the_case_trace_to_the_run_dir(self, reader, tmp_path):
        http = a_claude(a_final_reply())

        Evaluator(A_CONFIG, http, reader, tmp_path).evaluate(Case("a-case", A_QUESTION, "SELECT 1"))

        assert [path.name for path in tmp_path.iterdir()] == ["a-case.jsonl"]
