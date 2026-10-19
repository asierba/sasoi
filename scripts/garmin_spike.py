#!/usr/bin/env -S uv run --script
# /// script
# dependencies = ["garminconnect"]
# ///
import json
from getpass import getpass
from pathlib import Path

from garminconnect import Garmin

TOKENSTORE = "~/.garminconnect"
OUT = Path("data/garmin")
LOCATION_HINTS = ("lat", "lon", "polyline", "location", "geo")


def login():
    try:
        client = Garmin()
        client.login(TOKENSTORE)
        return client
    except Exception:
        client = Garmin(
            input("Garmin email: "),
            getpass("Garmin password: "),
            prompt_mfa=lambda: input("MFA code: "),
        )
        client.login(TOKENSTORE)
        return client


def save(name, data):
    (OUT / name).write_text(json.dumps(data, indent=2, default=str))


def safe_keys(data):
    return sorted(k for k in data if not any(h in k.lower() for h in LOCATION_HINTS))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    client = login()

    runs = client.get_activities(0, 10, activitytype="running")
    save("runs.json", runs)
    print(f"runs found: {len(runs)}")
    latest = runs[0]
    activity_id = latest["activityId"]
    print("latest:", latest.get("startTimeLocal"), latest.get("activityType", {}).get("typeKey"))
    print("distance m:", latest.get("distance"), "duration s:", latest.get("duration"))
    print("avg/max HR:", latest.get("averageHR"), latest.get("maxHR"))
    print("summary keys:", safe_keys(latest))

    laps = client.get_activity_splits(activity_id)
    save("splits.json", laps)
    lap_list = laps.get("lapDTOs", [])
    print(f"laps: {len(lap_list)}")
    if lap_list:
        print("lap keys:", safe_keys(lap_list[0]))

    details = client.get_activity_details(activity_id)
    save("details.json", details)
    metrics = [m["key"] for m in details.get("metricDescriptors", [])]
    print("stream metrics:", [m for m in metrics if not any(h in m.lower() for h in LOCATION_HINTS)])
    print("has GPS stream:", any(h in m.lower() for m in metrics for h in ("lat", "lon")))
    print("samples:", len(details.get("activityDetailMetrics", [])))

    fit_zip = client.download_activity(activity_id, dl_fmt=Garmin.ActivityDownloadFormat.ORIGINAL)
    (OUT / f"{activity_id}.zip").write_bytes(fit_zip)
    print(f"original FIT zip: {len(fit_zip)} bytes")
    print(f"raw files in {OUT}")


main()
