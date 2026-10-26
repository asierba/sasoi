from pathlib import Path

from sasoi.evals.grading import Grade
from sasoi.evals.report import line, summary


class TestLine:
    def test_shows_a_passed_case(self):
        assert line(Grade("a-case", ())) == "PASS a-case"

    def test_shows_a_failed_case_with_every_reason(self):
        assert line(Grade("a-case", ("first reason", "second reason"))) == "FAIL a-case: first reason; second reason"


class TestSummary:
    def test_counts_passed_cases_and_points_to_the_traces(self):
        grades = [
            Grade("passed", ()),
            Grade("failed", ("a reason",)),
            Grade("also-passed", ()),
        ]

        assert summary(grades, Path("traces/evals/run")) == "2/3 passed · traces in traces/evals/run"
