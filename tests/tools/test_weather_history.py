import json

import pytest

from sasoi.open_meteo_client import OpenMeteoError, WeatherHour
from sasoi.tools.tool import ToolError
from sasoi.tools.weather_history import weather_history


AN_INPUT = {"latitude": 43.263, "longitude": -2.935, "start": "2026-10-14T20:00", "end": "2026-10-15T06:00"}


def hour_at(time: str) -> WeatherHour:
    return WeatherHour(time, 15.9, 15.1, 88, 13.9, 0.2, 7.4)


class FakeOpenMeteo:
    def __init__(self, hours: list[WeatherHour] | OpenMeteoError):
        self._hours = hours
        self.requests: list[tuple[float, float, str, str]] = []

    def hourly_weather(self, latitude: float, longitude: float, start_date: str, end_date: str) -> list[WeatherHour]:
        self.requests.append((latitude, longitude, start_date, end_date))
        if isinstance(self._hours, OpenMeteoError):
            raise self._hours
        return self._hours


class TestWeatherHistory:
    def test_returns_only_the_requested_hours(self):
        open_meteo = FakeOpenMeteo(
            [
                hour_at("2026-10-14T19:00"),
                hour_at("2026-10-14T20:00"),
                hour_at("2026-10-15T06:00"),
                hour_at("2026-10-15T07:00"),
            ]
        )

        result = weather_history(open_meteo).run(
            {"latitude": 43.263, "longitude": -2.935, "start": "2026-10-14T20:00", "end": "2026-10-15T06:00"}
        )

        assert open_meteo.requests == [(43.263, -2.935, "2026-10-14", "2026-10-15")]
        assert [hour["time"] for hour in json.loads(result)] == ["2026-10-14T20:00", "2026-10-15T06:00"]

    def test_returns_each_hour_as_named_fields(self):
        open_meteo = FakeOpenMeteo([WeatherHour("2026-10-14T20:00", 15.9, 15.1, 88, 13.9, 0.2, 7.4)])

        result = weather_history(open_meteo).run({**AN_INPUT, "start": "2026-10-14T20:00", "end": "2026-10-14T20:00"})

        assert json.loads(result) == [
            {
                "time": "2026-10-14T20:00",
                "temperature_c": 15.9,
                "feels_like_c": 15.1,
                "humidity_pct": 88,
                "dew_point_c": 13.9,
                "precipitation_mm": 0.2,
                "wind_speed_kmh": 7.4,
            }
        ]

    def test_raises_tool_error_when_open_meteo_fails(self):
        open_meteo = FakeOpenMeteo(OpenMeteoError("Open-Meteo error 400: Parameter 'start_date' is out of range"))

        with pytest.raises(ToolError, match="Open-Meteo error 400: Parameter 'start_date' is out of range"):
            weather_history(open_meteo).run(AN_INPUT)
