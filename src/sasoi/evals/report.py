from pathlib import Path

from sasoi.evals.grading import Grade


def line(grade: Grade) -> str:
    if grade.passed:
        return f"PASS {grade.case_id}"
    return f"FAIL {grade.case_id}: {'; '.join(grade.failures)}"


def summary(grades: list[Grade], run_dir: Path) -> str:
    passed = sum(grade.passed for grade in grades)
    return f"{passed}/{len(grades)} passed · traces in {run_dir}"
