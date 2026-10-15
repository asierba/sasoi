from dataclasses import dataclass

import httpx

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"
HOURLY_VARIABLES = [
    "temperature_2m",
    "apparent_temperature",
    "relative_humidity_2m",
    "dew_point_2m",
    "precipitation",
    "wind_speed_10m",
]


class OpenMeteoError(Exception):
    pass


@dataclass(frozen=True)
class Place:
    name: str
    region: str | None
    country: str | None
    latitude: float
    longitude: float
    timezone: str


@dataclass(frozen=True)
class WeatherHour:
    time: str
    temperature_c: float
    feels_like_c: float
    humidity_pct: float
    dew_point_c: float
    precipitation_mm: float
    wind_speed_kmh: float


class OpenMeteoClient:
    def __init__(self, http: httpx.Client):
        self._http = http

    def search_places(self, name: str, count: int) -> list[Place]:
        results = self._get(GEOCODING_URL, {"name": name, "count": count}).get("results", [])
        return [_to_place(result) for result in results]

    def hourly_weather(self, latitude: float, longitude: float, date: str) -> list[WeatherHour]:
        body = self._get(
            ARCHIVE_URL,
            {
                "latitude": latitude,
                "longitude": longitude,
                "start_date": date,
                "end_date": date,
                "hourly": ",".join(HOURLY_VARIABLES),
                "timezone": "auto",
            },
        )
        return _to_weather_hours(body["hourly"])

    def _get(self, url: str, params: dict) -> dict:
        try:
            response = self._http.get(url, params=params)
        except httpx.TransportError as error:
            raise OpenMeteoError(f"Open-Meteo unreachable: {error}") from error
        if response.is_error:
            raise OpenMeteoError(f"Open-Meteo error {response.status_code}: {_reason(response)}")
        return response.json()


def _to_place(result: dict) -> Place:
    return Place(
        name=result["name"],
        region=result.get("admin1"),
        country=result.get("country"),
        latitude=result["latitude"],
        longitude=result["longitude"],
        timezone=result["timezone"],
    )


def _to_weather_hours(hourly: dict) -> list[WeatherHour]:
    return [
        WeatherHour(
            time=time,
            temperature_c=hourly["temperature_2m"][hour],
            feels_like_c=hourly["apparent_temperature"][hour],
            humidity_pct=hourly["relative_humidity_2m"][hour],
            dew_point_c=hourly["dew_point_2m"][hour],
            precipitation_mm=hourly["precipitation"][hour],
            wind_speed_kmh=hourly["wind_speed_10m"][hour],
        )
        for hour, time in enumerate(hourly["time"])
    ]


def _reason(response: httpx.Response) -> str:
    try:
        return response.json()["reason"]
    except (ValueError, KeyError, TypeError):
        return response.text
