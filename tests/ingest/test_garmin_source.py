from sasoi.ingest.garmin_source import GarminSource
from sasoi.ingest.garmin_types import GarminActivity, GarminLap

A_VERY_LARGE_LIMIT = 100000


class FakeGarminApi:
    def __init__(self, activities: list[GarminActivity], laps: dict[int, list[GarminLap]] | None = None):
        self._activities = activities
        self._laps_by_id = {str(activity_id): activity_laps for activity_id, activity_laps in (laps or {}).items()}

    def get_activities(self, start: int, limit: int, activitytype: str | None) -> list[GarminActivity]:
        matching = [a for a in self._activities if activitytype in (None, a["activityType"]["typeKey"])]
        return matching[start : start + limit]

    def get_activity_splits(self, activity_id: str) -> dict:
        return {"activityId": int(activity_id), "lapDTOs": self._laps_by_id[activity_id], "eventDTOs": []}


def an_activity(activity_id: int, type_key: str) -> GarminActivity:
    return {
        "activityId": activity_id,
        "activityType": {"typeKey": type_key},
        "startTimeLocal": "2024-01-02 07:00:00",
        "startTimeGMT": "2024-01-02 06:00:00",
        "distance": 5000.0,
        "duration": 1800.0,
        "averageSpeed": 2.78,
        "maxSpeed": 3.5,
        "averageRunningCadenceInStepsPerMinute": 165.0,
        "maxRunningCadenceInStepsPerMinute": 180.0,
        "elevationGain": 20.0,
        "elevationLoss": 18.0,
    }


def a_garmin_lap(lap_index: int) -> GarminLap:
    return {
        "lapIndex": lap_index,
        "startTimeGMT": "2024-01-02T06:00:00.0",
        "distance": 1000.0,
        "duration": 360.0,
        "averageSpeed": 2.78,
        "maxSpeed": 3.2,
        "averageRunCadence": 165.0,
        "elevationGain": 4.0,
        "elevationLoss": 3.0,
    }


class TestGarminSource:
    def test_recent_runs_returns_every_run(self):
        api = FakeGarminApi([an_activity(3, "running"), an_activity(2, "running"), an_activity(1, "running")])

        runs = GarminSource(api).recent_runs(A_VERY_LARGE_LIMIT)

        assert [run.activity_id for run in runs] == [3, 2, 1]

    def test_recent_runs_returns_only_the_latest_runs_up_to_the_limit(self):
        api = FakeGarminApi(
            [
                an_activity(4, "running"),
                an_activity(3, "cycling"),
                an_activity(2, "running"),
                an_activity(1, "running"),
            ]
        )

        runs = GarminSource(api).recent_runs(2)

        assert [run.activity_id for run in runs] == [4, 2]

    def test_laps_returns_the_laps_of_the_activity(self):
        api = FakeGarminApi([], laps={7: [a_garmin_lap(1), a_garmin_lap(2)], 8: [a_garmin_lap(1)]})

        laps = GarminSource(api).laps(7)

        assert [lap.lap_index for lap in laps] == [1, 2]
