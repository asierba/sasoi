import json
import os
from pathlib import Path

import httpx
from dotenv import load_dotenv

OUT = Path("data/hevy/workouts.json")


def client():
    return httpx.Client(
        base_url="https://api.hevyapp.com",
        headers={
            "authorization": f"Bearer {os.environ['HEVY_AUTH_TOKEN']}",
            "x-api-key": "shelobs_hevy_web",
            "hevy-platform": "web",
        },
    )


def fetch_all(http):
    workouts = []
    next_index = 0
    while batch := http.get(f"/workouts_batch/{next_index}").raise_for_status().json():
        workouts.extend(batch)
        next_index = batch[-1]["index"] + 1
    return workouts


def main():
    load_dotenv(".env")
    with client() as http:
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
