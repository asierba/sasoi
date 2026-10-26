from pathlib import Path

from sasoi.evals.grading import Grade


def line(grade: Grade) -> str:
    if grade.passed:
        return f"PASS {grade.case_id}"
    return f"FAIL {grade.case_id}: {'; '.join(grade.failures)}"


def pass_rates(grades: list[Grade]) -> str:
    grades_by_case: dict[str, list[Grade]] = {}
    for grade in grades:
        grades_by_case.setdefault(grade.case_id, []).append(grade)
    return "\n".join(
        f"{sum(grade.passed for grade in case_grades)}/{len(case_grades)} {case_id}"
        for case_id, case_grades in grades_by_case.items()
    )


def summary(grades: list[Grade], run_dir: Path) -> str:
    passed = sum(grade.passed for grade in grades)
    return f"{passed}/{len(grades)} passed · traces in {run_dir}"
