from sasoi.ingest.garmin_source import GarminSource
from sasoi.ingest.garmin_types import GarminActivity

A_VERY_LARGE_LIMIT = 100000


class FakeGarminApi:
    def __init__(self, activities: list[GarminActivity], laps: dict[int, list[dict]] | None = None):
        self._activities = activities
        self._laps_by_id = {str(activity_id): activity_laps for activity_id, activity_laps in (laps or {}).items()}

    def get_activities(self, start: int, limit: int, activitytype: str | None) -> list[GarminActivity]:
        matching = [a for a in self._activities if activitytype in (None, a["activityType"]["typeKey"])]
        return matching[start : start + limit]

    def get_activity_splits(self, activity_id: str) -> dict:
        return {"activityId": int(activity_id), "lapDTOs": self._laps_by_id[activity_id], "eventDTOs": []}


def an_activity(activity_id: int, type_key: str) -> GarminActivity:
    return {"activityId": activity_id, "activityType": {"typeKey": type_key}}


class TestGarminSource:
    def test_recent_runs_returns_every_run(self):
        api = FakeGarminApi([an_activity(3, "running"), an_activity(2, "running"), an_activity(1, "running")])

        runs = GarminSource(api).recent_runs(A_VERY_LARGE_LIMIT)

        assert runs == [an_activity(3, "running"), an_activity(2, "running"), an_activity(1, "running")]

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

        assert runs == [an_activity(4, "running"), an_activity(2, "running")]

    def test_splits_returns_the_laps_of_the_activity(self):
        api = FakeGarminApi(
            [],
            laps={
                7: [{"lapIndex": 1, "distance": 1000.0}, {"lapIndex": 2, "distance": 1000.0}],
                8: [{"lapIndex": 1, "distance": 5000.0}],
            },
        )

        splits = GarminSource(api).splits(7)

        assert splits == {
            "activityId": 7,
            "lapDTOs": [{"lapIndex": 1, "distance": 1000.0}, {"lapIndex": 2, "distance": 1000.0}],
            "eventDTOs": [],
        }
