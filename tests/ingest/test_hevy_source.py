import json

import httpx
import pytest

from sasoi.ingest.hevy_source import HevyError, HevySource, HevyTokens, renew

AN_ACCESS_TOKEN = "an-access-token"
A_TOKEN_PAIR = HevyTokens("an-access-token", "a-refresh-token")


def a_hevy_workout(workout_id: str, index: int) -> dict:
    return {
        "id": workout_id,
        "index": index,
        "name": "Full Body A",
        "description": "",
        "start_time": 1704218400,
        "end_time": 1704222000,
        "exercises": [],
    }


def hevy_api(batches: dict[int, list[dict]], renewed: dict | None = None):
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if request.url.path == "/auth/refresh_token":
            return httpx.Response(200, json=renewed)
        return httpx.Response(200, json=batches.get(int(request.url.path.rsplit("/", 1)[1]), []))

    return httpx.Client(transport=httpx.MockTransport(handler)), requests


class TestRenew:
    def test_sends_the_token_pair_as_the_web_app(self):
        http, requests = hevy_api({}, renewed={"access_token": "new-access", "refresh_token": "new-refresh"})

        renew(http, HevyTokens("old-access", "old-refresh"))

        request = requests[0]
        assert (
            str(request.url),
            request.headers["x-api-key"],
            request.headers["hevy-platform"],
            request.headers["authorization"],
            json.loads(request.content),
        ) == (
            "https://api.hevyapp.com/auth/refresh_token",
            "shelobs_hevy_web",
            "web",
            "Bearer old-access",
            {"refresh_token": "old-refresh"},
        )

    def test_returns_the_new_token_pair(self):
        http, _ = hevy_api(
            {},
            renewed={
                "access_token": "new-access",
                "refresh_token": "new-refresh",
                "expires_at": "2024-01-02T18:15:00.000Z",
            },
        )

        assert renew(http, A_TOKEN_PAIR) == HevyTokens("new-access", "new-refresh")


class TestHevySource:
    def test_all_workouts_sends_the_access_token(self):
        http, requests = hevy_api({})

        HevySource(http, "token-123").all_workouts()

        assert requests[0].headers["authorization"] == "Bearer token-123"

    def test_all_workouts_pages_from_the_index_after_the_last_workout_of_each_batch(self):
        http, requests = hevy_api(
            {
                0: [a_hevy_workout("w-1", 10), a_hevy_workout("w-2", 20)],
                21: [a_hevy_workout("w-3", 30)],
            }
        )

        workouts = HevySource(http, AN_ACCESS_TOKEN).all_workouts()

        assert [workout.workout_id for workout in workouts] == ["w-1", "w-2", "w-3"]
        assert [request.url.path for request in requests] == [
            "/workouts_batch/0",
            "/workouts_batch/21",
            "/workouts_batch/31",
        ]

    def test_raises_error_with_body_on_error_response(self):
        http = httpx.Client(transport=httpx.MockTransport(lambda _: httpx.Response(401, text="Unauthorized")))

        with pytest.raises(HevyError, match="Hevy error 401 on /auth/refresh_token: Unauthorized"):
            renew(http, A_TOKEN_PAIR)

    def test_raises_error_when_unreachable(self):
        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("no route", request=request)

        with pytest.raises(HevyError, match="Hevy unreachable: no route"):
            HevySource(httpx.Client(transport=httpx.MockTransport(handler)), AN_ACCESS_TOKEN).all_workouts()
