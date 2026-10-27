import csv
import io
from dataclasses import dataclass

from sasoi.tools.run_sql import TRUNCATED_FOOTER

UNIT_SCALES = (1, 1000, 1 / 1000, 60, 1 / 60, 100, 1 / 100)
ABSOLUTE_TOLERANCE = 0.5
RELATIVE_TOLERANCE = 0.01


@dataclass(frozen=True)
class QueryResult:
    rows: list[list[str]]
    truncated: bool

    @classmethod
    def from_csv(cls, text: str) -> "QueryResult":
        table, _, footer = text.rpartition("\n")
        header_and_rows = list(csv.reader(io.StringIO(table)))
        return cls(header_and_rows[1:], footer == TRUNCATED_FOOTER)

    def contains(self, expected: "QueryResult") -> bool:
        return all(any(_row_contains(actual, row) for actual in self.rows) for row in expected.rows)

    def hit_row_cap(self) -> bool:
        return self.truncated


@dataclass(frozen=True)
class Grade:
    case_id: str
    failures: tuple[str, ...]

    @classmethod
    def compare(cls, case_id: str, ground_truth: QueryResult, agent_results: list[QueryResult]) -> "Grade":
        if not agent_results:
            return cls(case_id, ("run_sql never returned a result",))
        failures = []
        if any(result.hit_row_cap() for result in agent_results):
            failures.append("a run_sql result hit the row cap")
        if not any(result.contains(ground_truth) for result in agent_results):
            failures.append("no run_sql result contains the ground truth")
        return cls(case_id, tuple(failures))

    @classmethod
    def agent_failed(cls, case_id: str, error: Exception) -> "Grade":
        return cls(case_id, (f"agent failed: {error}",))

    @classmethod
    def ground_truth_failed(cls, case_id: str, error: Exception) -> "Grade":
        return cls(case_id, (f"ground truth failed: {error}",))

    @property
    def passed(self) -> bool:
        return not self.failures


def _row_contains(actual_row: list[str], expected_row: list[str]) -> bool:
    return all(any(_cells_match(actual, expected) for actual in actual_row) for expected in expected_row)


def _cells_match(actual: str, expected: str) -> bool:
    actual_number, expected_number = _number(actual), _number(expected)
    if expected_number is None:
        return actual.strip().lower().startswith(expected.strip().lower())
    return actual_number is not None and _numbers_match(actual_number, expected_number)


def _numbers_match(actual: float, expected: float) -> bool:
    tolerance = max(ABSOLUTE_TOLERANCE, RELATIVE_TOLERANCE * abs(expected))
    return any(abs(actual * scale - expected) <= tolerance for scale in UNIT_SCALES)


def _number(cell: str) -> float | None:
    try:
        return float(cell)
    except ValueError:
        return None
