import httpx
import pytest

from sasoi.open_meteo_client import OpenMeteoClient, OpenMeteoError, Place, WeatherHour

A_PLACE = "Bilbao"
A_COUNT = 3


def client(handler) -> OpenMeteoClient:
    return OpenMeteoClient(httpx.Client(transport=httpx.MockTransport(handler)))


def test_search_places_queries_geocoding_api_and_returns_places():
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["request"] = request
        return httpx.Response(
            200,
            json={
                "results": [
                    {
                        "name": "Bilbao",
                        "latitude": 43.26271,
                        "longitude": -2.92528,
                        "elevation": 20.0,
                        "timezone": "Europe/Madrid",
                        "country": "Spain",
                        "admin1": "Basque Country",
                    }
                ]
            },
        )

    places = client(handler).search_places("Bilbao", 3)

    assert str(captured["request"].url) == "https://geocoding-api.open-meteo.com/v1/search?name=Bilbao&count=3"
    assert places == [Place("Bilbao", "Basque Country", "Spain", 43.26271, -2.92528, "Europe/Madrid")]


def test_search_places_leaves_region_and_country_empty_when_missing():
    open_meteo = client(
        lambda _: httpx.Response(
            200,
            json={"results": [{"name": "Antarctica", "latitude": -75.0, "longitude": 0.0, "timezone": "Antarctica/Troll"}]},
        )
    )

    places = open_meteo.search_places(A_PLACE, A_COUNT)

    assert places == [Place("Antarctica", None, None, -75.0, 0.0, "Antarctica/Troll")]


def test_search_places_returns_empty_list_when_nothing_found():
    places = client(lambda _: httpx.Response(200, json={"generationtime_ms": 0.07})).search_places(A_PLACE, A_COUNT)

    assert places == []


def test_hourly_weather_queries_archive_api_for_the_day_in_local_time_and_returns_hours():
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["request"] = request
        return httpx.Response(
            200,
            json={
                "timezone": "Europe/Madrid",
                "hourly_units": {"time": "iso8601", "temperature_2m": "°C"},
                "hourly": {
                    "time": ["2026-10-14T09:00", "2026-10-14T10:00"],
                    "temperature_2m": [15.9, 16.7],
                    "apparent_temperature": [15.1, 16.2],
                    "relative_humidity_2m": [88, 81],
                    "dew_point_2m": [13.9, 13.4],
                    "precipitation": [0.2, 0.0],
                    "wind_speed_10m": [7.4, 9.1],
                },
            },
        )

    hours = client(handler).hourly_weather(43.263, -2.935, "2026-10-14")

    request = captured["request"]
    assert request.url.copy_with(query=None) == "https://archive-api.open-meteo.com/v1/archive"
    assert dict(request.url.params) == {
        "latitude": "43.263",
        "longitude": "-2.935",
        "start_date": "2026-10-14",
        "end_date": "2026-10-14",
        "hourly": "temperature_2m,apparent_temperature,relative_humidity_2m,dew_point_2m,precipitation,wind_speed_10m",
        "timezone": "auto",
    }
    assert hours == [
        WeatherHour("2026-10-14T09:00", 15.9, 15.1, 88, 13.9, 0.2, 7.4),
        WeatherHour("2026-10-14T10:00", 16.7, 16.2, 81, 13.4, 0.0, 9.1),
    ]


def test_raises_error_with_reason_on_error_response():
    open_meteo = client(lambda _: httpx.Response(400, json={"error": True, "reason": "Parameter 'name' is missing"}))

    with pytest.raises(OpenMeteoError, match="Open-Meteo error 400: Parameter 'name' is missing"):
        open_meteo.search_places(A_PLACE, A_COUNT)


def test_raises_error_with_body_on_non_json_error_response():
    open_meteo = client(lambda _: httpx.Response(502, text="Bad Gateway"))

    with pytest.raises(OpenMeteoError, match="Open-Meteo error 502: Bad Gateway"):
        open_meteo.search_places(A_PLACE, A_COUNT)


def test_raises_error_when_unreachable():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("no route", request=request)

    with pytest.raises(OpenMeteoError, match="Open-Meteo unreachable: no route"):
        client(handler).search_places(A_PLACE, A_COUNT)
