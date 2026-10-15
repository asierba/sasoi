import json
from dataclasses import asdict
from typing import Protocol

from sasoi.open_meteo_client import OpenMeteoError, WeatherHour
from sasoi.tools.tool import Tool, ToolError


class WeatherArchive(Protocol):
    def hourly_weather(self, latitude: float, longitude: float, date: str) -> list[WeatherHour]: ...


def weather_history(open_meteo: WeatherArchive) -> Tool:
    def run(tool_input: dict) -> str:
        try:
            hours = open_meteo.hourly_weather(tool_input["latitude"], tool_input["longitude"], tool_input["date"])
        except OpenMeteoError as error:
            raise ToolError(str(error)) from error
        return json.dumps([asdict(hour) for hour in hours])

    return Tool(
        name="weather_history",
        description=(
            "Get the hourly weather on a past date at given coordinates, in the location's local time: "
            "temperature, feels-like temperature, humidity, dew point, precipitation and wind speed. "
            "Covers 1940 up to today."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "latitude": {"type": "number"},
                "longitude": {"type": "number"},
                "date": {"type": "string", "description": "Date in YYYY-MM-DD format"},
            },
            "required": ["latitude", "longitude", "date"],
        },
        run=run,
    )
