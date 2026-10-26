from pathlib import Path

from sasoi.evals.grading import Grade
from sasoi.evals.report import line, pass_rates, summary


class TestLine:
    def test_shows_a_passed_case(self):
        assert line(Grade("a-case", ())) == "PASS a-case"

    def test_shows_a_failed_case_with_every_reason(self):
        assert line(Grade("a-case", ("first reason", "second reason"))) == "FAIL a-case: first reason; second reason"


class TestPassRates:
    def test_shows_how_many_runs_of_each_case_passed_in_case_order(self):
        grades = [
            Grade("flaky", ()),
            Grade("stable", ()),
            Grade("flaky", ("a reason",)),
            Grade("stable", ()),
        ]

        assert pass_rates(grades) == "1/2 flaky\n2/2 stable"


class TestSummary:
    def test_counts_passed_cases_and_points_to_the_traces(self):
        grades = [
            Grade("passed", ()),
            Grade("failed", ("a reason",)),
            Grade("also-passed", ()),
        ]

        assert summary(grades, Path("traces/evals/run")) == "2/3 passed · traces in traces/evals/run"
