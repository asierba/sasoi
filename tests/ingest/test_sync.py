from sasoi.ingest.garmin_types import GarminActivity, GarminSplits
from sasoi.ingest.sync import sync_garmin

A_VERY_LARGE_LIMIT = 100000


class FakeRunSource:
    def __init__(self, runs: list[GarminActivity]):
        self._runs = runs
        self.splits_requested = []

    def recent_runs(self, limit: int) -> list[GarminActivity]:
        return self._runs[:limit]

    def splits(self, activity_id: int) -> GarminSplits:
        self.splits_requested.append(activity_id)
        return a_splits(activity_id)


class FakeStore:
    def __init__(self, garmin: dict[int, tuple[GarminActivity, GarminSplits]] | None = None):
        self.garmin = garmin or {}

    def stored_garmin_ids(self) -> set[int]:
        return set(self.garmin)

    def save_garmin_run(self, summary: GarminActivity, splits: GarminSplits) -> None:
        self.garmin[summary["activityId"]] = (summary, splits)


def a_run(activity_id: int) -> GarminActivity:
    return {"activityId": activity_id, "activityType": {"typeKey": "running"}}


def a_splits(activity_id: int) -> GarminSplits:
    return {"activityId": activity_id, "lapDTOs": [], "eventDTOs": []}


class TestSyncGarmin:
    def test_saves_every_run_with_its_splits_into_an_empty_store(self):
        store = FakeStore()
        source = FakeRunSource([a_run(3), a_run(2), a_run(1)])

        new = sync_garmin(source, store, A_VERY_LARGE_LIMIT)

        assert new == 3
        assert store.garmin == {
            3: (a_run(3), a_splits(3)),
            2: (a_run(2), a_splits(2)),
            1: (a_run(1), a_splits(1)),
        }

    def test_saves_only_the_latest_runs_up_to_the_limit(self):
        store = FakeStore()
        source = FakeRunSource([a_run(3), a_run(2), a_run(1)])

        new = sync_garmin(source, store, limit=2)

        assert new == 2
        assert store.garmin == {
            3: (a_run(3), a_splits(3)),
            2: (a_run(2), a_splits(2)),
        }

    def test_fetches_splits_only_for_runs_not_yet_stored(self):
        store = FakeStore(garmin={2: (a_run(2), a_splits(2))})
        source = FakeRunSource([a_run(3), a_run(2), a_run(1)])

        sync_garmin(source, store, limit=3)

        assert source.splits_requested == [3, 1]

    def test_saves_nothing_when_rerun(self):
        store = FakeStore()
        source = FakeRunSource([a_run(1)])
        sync_garmin(source, store, A_VERY_LARGE_LIMIT)

        new = sync_garmin(source, store, A_VERY_LARGE_LIMIT)

        assert new == 0
