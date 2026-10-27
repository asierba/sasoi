import json
from dataclasses import asdict
from typing import Protocol

from sasoi.open_meteo_client import OpenMeteoError, Place
from sasoi.tools.tool import Tool, ToolError

MAX_MATCHES = 3


class PlaceSearch(Protocol):
    def search_places(self, name: str, count: int) -> list[Place]: ...


def geocode(open_meteo: PlaceSearch) -> Tool:
    def run(tool_input: dict) -> str:
        place = tool_input["place"]
        try:
            places = open_meteo.search_places(place, MAX_MATCHES)
        except OpenMeteoError as error:
            raise ToolError(str(error)) from error
        if not places:
            raise ToolError(f"No place found for '{place}'")
        return json.dumps([asdict(found) for found in places])

    return Tool(
        name="geocode",
        description=(
            "Find the coordinates and timezone of a place by name. "
            "Returns up to 3 matches; if they are in different places, ask the user which one."
        ),
        input_schema={
            "type": "object",
            "properties": {"place": {"type": "string", "description": "Place name, e.g. 'Bilbao'"}},
            "required": ["place"],
        },
        run=run,
    )
