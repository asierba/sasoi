from collections.abc import Callable
from dataclasses import dataclass


class ToolError(Exception):
    pass


@dataclass(frozen=True)
class Tool:
    name: str
    description: str
    input_schema: dict
    run: Callable[[dict], str]

    @property
    def definition(self) -> dict:
        return {"name": self.name, "description": self.description, "input_schema": self.input_schema}

