import json
from dataclasses import asdict
from datetime import datetime
from typing import Protocol

from sasoi.open_meteo_client import OpenMeteoError, WeatherHour
from sasoi.tools.tool import Tool, ToolError


class WeatherArchive(Protocol):
    def hourly_weather(self, latitude: float, longitude: float, start_date: str, end_date: str) -> list[WeatherHour]: ...


def weather_history(open_meteo: WeatherArchive) -> Tool:
    def run(tool_input: dict) -> str:
        start = datetime.fromisoformat(tool_input["start"])
        end = datetime.fromisoformat(tool_input["end"])
        try:
            hours = open_meteo.hourly_weather(
                tool_input["latitude"], tool_input["longitude"], start.date().isoformat(), end.date().isoformat()
            )
        except OpenMeteoError as error:
            raise ToolError(str(error)) from error
        return json.dumps([asdict(hour) for hour in hours if start <= datetime.fromisoformat(hour.time) <= end])

    return Tool(
        name="weather_history",
        description=(
            "Get the hourly weather between two past times at given coordinates, in the location's local time: "
            "temperature, feels-like temperature, humidity, dew point, precipitation and wind speed. "
            "Covers 1940 up to today."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "latitude": {"type": "number"},
                "longitude": {"type": "number"},
                "start": {"type": "string", "description": "First hour, local time, YYYY-MM-DDTHH:00"},
                "end": {"type": "string", "description": "Last hour, inclusive, local time, YYYY-MM-DDTHH:00"},
            },
            "required": ["latitude", "longitude", "start", "end"],
        },
        run=run,
    )
