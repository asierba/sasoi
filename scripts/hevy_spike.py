#!/usr/bin/env -S uv run --script
# /// script
# dependencies = ["httpx"]
# ///
import json
from pathlib import Path

import httpx

OUT = Path("data/hevy/workouts.json")
TOKENS = Path("data/hevy/tokens.json")
API = "https://api.hevyapp.com"
HEADERS = {"x-api-key": "shelobs_hevy_web", "hevy-platform": "web"}


def stored_tokens():
    if TOKENS.exists():
        return json.loads(TOKENS.read_text())
    return {"access_token": input("access_token: ").strip(), "refresh_token": input("refresh_token: ").strip()}


def save_tokens(tokens):
    TOKENS.parent.mkdir(parents=True, exist_ok=True)
    TOKENS.write_text(json.dumps(tokens, indent=2))
    TOKENS.chmod(0o600)


def refreshed(tokens):
    response = httpx.post(
        f"{API}/auth/refresh_token",
        headers={**HEADERS, "authorization": f"Bearer {tokens['access_token']}"},
        json={"refresh_token": tokens["refresh_token"]},
    )
    if response.is_error:
        raise SystemExit(f"token refresh failed: {response.status_code} {response.text}")
    return response.json()


def client(access_token):
    return httpx.Client(base_url=API, headers={**HEADERS, "authorization": f"Bearer {access_token}"})


def fetch_all(http):
    workouts = []
    next_index = 0
    while batch := http.get(f"/workouts_batch/{next_index}").raise_for_status().json():
        workouts.extend(batch)
        next_index = batch[-1]["index"] + 1
    return workouts


def main():
    tokens = refreshed(stored_tokens())
    save_tokens(tokens)
    print(f"access token expires at: {tokens.get('expires_at')}")
    with client(tokens["access_token"]) as http:
        count = http.get("/workout_count").raise_for_status().json()["workout_count"]
        workouts = fetch_all(http)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(workouts, indent=2))
    sets = sum(len(e["sets"]) for w in workouts for e in w["exercises"])
    print(f"workout_count: {count}, fetched: {len(workouts)}, unique ids: {len({w['id'] for w in workouts})}")
    print(f"sets: {sets}")
    print(f"first: {workouts[0]['start_time']} last: {workouts[-1]['start_time']}")
    print(f"saved to {OUT}")


main()
