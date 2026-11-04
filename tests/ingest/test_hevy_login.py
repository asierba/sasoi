import json
from pathlib import Path

import httpx
import pytest

from sasoi.ingest.hevy_login import login
from sasoi.ingest.hevy_source import HevyError

A_RENEWED_PAIR = {"access_token": "new-access", "refresh_token": "new-refresh"}


def no_prompt(label: str) -> str:
    raise AssertionError(f"unexpected prompt: {label}")


def a_tokenstore(directory: Path, access_token: str = "an-access", refresh_token: str = "a-refresh") -> Path:
    tokenstore = directory / "hevy" / "tokens.json"
    tokenstore.parent.mkdir()
    tokenstore.write_text(json.dumps({"access_token": access_token, "refresh_token": refresh_token}))
    return tokenstore


def hevy_api(renewed: dict, status: int = 200):
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if request.url.path == "/auth/refresh_token":
            return httpx.Response(status, json=renewed)
        return httpx.Response(200, json=[])

    return httpx.Client(transport=httpx.MockTransport(handler)), requests


class TestLogin:
    def test_renews_the_stored_token_pair(self, tmp_path):
        http, requests = hevy_api(A_RENEWED_PAIR)

        login(http, a_tokenstore(tmp_path, "old-access", "old-refresh"), no_prompt)

        assert (requests[0].headers["authorization"], json.loads(requests[0].content)) == (
            "Bearer old-access",
            {"refresh_token": "old-refresh"},
        )

    def test_saves_the_renewed_token_pair_readable_only_by_the_owner(self, tmp_path):
        http, _ = hevy_api({"access_token": "new-access", "refresh_token": "new-refresh", "expires_at": "x"})
        tokenstore = a_tokenstore(tmp_path)

        login(http, tokenstore, no_prompt)

        assert (json.loads(tokenstore.read_text()), oct(tokenstore.stat().st_mode & 0o777)) == (
            {"access_token": "new-access", "refresh_token": "new-refresh"},
            "0o600",
        )

    def test_returns_a_source_that_sends_the_renewed_access_token(self, tmp_path):
        http, requests = hevy_api({"access_token": "new-access", "refresh_token": "new-refresh"})

        login(http, a_tokenstore(tmp_path), no_prompt).all_workouts()

        assert requests[1].headers["authorization"] == "Bearer new-access"

    def test_prompts_for_a_token_pair_when_none_is_stored(self, tmp_path):
        http, requests = hevy_api(A_RENEWED_PAIR)
        answers = {"Hevy access_token: ": " pasted-access ", "Hevy refresh_token: ": "pasted-refresh\n"}

        login(http, tmp_path / "hevy" / "tokens.json", answers.__getitem__)

        assert (requests[0].headers["authorization"], json.loads(requests[0].content)) == (
            "Bearer pasted-access",
            {"refresh_token": "pasted-refresh"},
        )

    def test_keeps_the_stored_token_pair_when_renewal_fails(self, tmp_path):
        http, _ = hevy_api({"error": "invalid refresh token"}, status=401)
        tokenstore = a_tokenstore(tmp_path, "old-access", "old-refresh")

        with pytest.raises(HevyError):
            login(http, tokenstore, no_prompt)

        assert json.loads(tokenstore.read_text()) == {"access_token": "old-access", "refresh_token": "old-refresh"}
