from datetime import datetime

from sasoi.tools.tool import Tool


def _now(_: dict) -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


current_time = Tool(
    name="current_time",
    description="Get the current local date and time, with timezone offset, in ISO 8601 format.",
    input_schema={"type": "object", "properties": {}},
    run=_now,
)
