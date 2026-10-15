import json

import pytest

from sasoi.open_meteo_client import OpenMeteoError, Place
from sasoi.tools.geocode import geocode
from sasoi.tools.tool import ToolError

A_PLACE = "Bilbao"


class FakeOpenMeteo:
    def __init__(self, places: list[Place] | OpenMeteoError):
        self._places = places
        self.searches: list[tuple[str, int]] = []

    def search_places(self, name: str, count: int) -> list[Place]:
        self.searches.append((name, count))
        if isinstance(self._places, OpenMeteoError):
            raise self._places
        return self._places


def test_geocode_searches_up_to_three_places_and_returns_their_location():
    open_meteo = FakeOpenMeteo([Place("Bilbao", "Basque Country", "Spain", 43.26271, -2.92528, "Europe/Madrid")])

    result = geocode(open_meteo).run({"place": "Bilbao"})

    assert open_meteo.searches == [("Bilbao", 3)]
    assert json.loads(result) == [
        {
            "name": "Bilbao",
            "region": "Basque Country",
            "country": "Spain",
            "latitude": 43.26271,
            "longitude": -2.92528,
            "timezone": "Europe/Madrid",
        }
    ]


def test_geocode_raises_tool_error_when_no_place_found():
    with pytest.raises(ToolError, match="No place found for 'xqzzqx'"):
        geocode(FakeOpenMeteo([])).run({"place": "xqzzqx"})


def test_geocode_raises_tool_error_when_open_meteo_fails():
    open_meteo = FakeOpenMeteo(OpenMeteoError("Open-Meteo unreachable: no route"))

    with pytest.raises(ToolError, match="Open-Meteo unreachable: no route"):
        geocode(open_meteo).run({"place": A_PLACE})
