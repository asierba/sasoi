from dataclasses import dataclass
from typing import Any

import httpx

from sasoi.ingest.hevy_mapping import to_workout
from sasoi.ingest.hevy_types import HevyWorkout
from sasoi.ingest.workouts import Workout

API = "https://api.hevyapp.com"
WEB_APP_HEADERS = {"x-api-key": "shelobs_hevy_web", "hevy-platform": "web"}


class HevyError(Exception):
    pass


@dataclass(frozen=True)
class HevyTokens:
    access_token: str
    refresh_token: str


def renew(http: httpx.Client, tokens: HevyTokens) -> HevyTokens:
    request = http.build_request(
        "POST",
        f"{API}/auth/refresh_token",
        headers=_authorized(tokens.access_token),
        json={"refresh_token": tokens.refresh_token},
    )
    body = _send(http, request)
    return HevyTokens(body["access_token"], body["refresh_token"])


class HevySource:
    def __init__(self, http: httpx.Client, access_token: str):
        self._http = http
        self._headers = _authorized(access_token)

    def all_workouts(self) -> list[Workout]:
        return [to_workout(workout) for workout in self._all_hevy_workouts()]

    def _all_hevy_workouts(self) -> list[HevyWorkout]:
        workouts: list[HevyWorkout] = []
        next_index = 0
        while batch := self._get(f"/workouts_batch/{next_index}"):
            workouts.extend(batch)
            next_index = batch[-1]["index"] + 1
        return workouts

    def _get(self, path: str) -> Any:
        return _send(self._http, self._http.build_request("GET", f"{API}{path}", headers=self._headers))


def _authorized(access_token: str) -> dict[str, str]:
    return {**WEB_APP_HEADERS, "authorization": f"Bearer {access_token}"}


def _send(http: httpx.Client, request: httpx.Request) -> Any:
    try:
        response = http.send(request)
    except httpx.TransportError as error:
        raise HevyError(f"Hevy unreachable: {error}") from error
    if response.is_error:
        raise HevyError(f"Hevy error {response.status_code} on {request.url.path}: {response.text}")
    return response.json()
