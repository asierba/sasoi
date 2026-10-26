import tomllib
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Case:
    id: str
    question: str
    sql: str


def load_cases(path: Path) -> list[Case]:
    with path.open("rb") as file:
        return [Case(case["id"], case["question"], case["sql"]) for case in tomllib.load(file)["case"]]
