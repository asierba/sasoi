import logging
from datetime import UTC, datetime

from builders import a_lap, a_run, a_workout

from sasoi.ingest.runs import Lap, Run
from sasoi.ingest.sync import sync_garmin, sync_hevy
from sasoi.ingest.workouts import Workout

A_VERY_LARGE_LIMIT = 100000


class FakeRunSource:
    def __init__(self, runs: list[Run], laps: dict[int, list[Lap]] | None = None):
        self._runs = runs
        self._laps = laps or {}
        self.laps_requested = []

    def recent_runs(self, limit: int) -> list[Run]:
        return self._runs[:limit]

    def laps(self, activity_id: int) -> list[Lap]:
        self.laps_requested.append(activity_id)
        return self._laps.get(activity_id, [])


class FakeStore:
    def __init__(self, garmin: dict[int, tuple[Run, list[Lap]]] | None = None):
        self.garmin = garmin or {}

    def stored_garmin_ids(self) -> set[int]:
        return set(self.garmin)

    def save_garmin_run(self, run: Run, laps: list[Lap]) -> None:
        self.garmin[run.activity_id] = (run, laps)


class FakeWorkoutSource:
    def __init__(self, workouts: list[Workout]):
        self._workouts = workouts

    def all_workouts(self) -> list[Workout]:
        return self._workouts


class FakeWorkoutStore:
    def __init__(self, hevy: dict[str, Workout] | None = None):
        self.hevy = hevy or {}

    def stored_hevy_ids(self) -> set[str]:
        return set(self.hevy)

    def save_hevy_workout(self, workout: Workout) -> None:
        self.hevy[workout.workout_id] = workout


class TestSyncGarmin:
    def test_saves_every_run_with_its_laps_into_an_empty_store(self):
        store = FakeStore()
        source = FakeRunSource([a_run(3), a_run(2), a_run(1)], laps={3: [a_lap(1), a_lap(2)], 2: [a_lap(1)]})

        new = sync_garmin(source, store, A_VERY_LARGE_LIMIT)

        assert new == 3
        assert store.garmin == {
            3: (a_run(3), [a_lap(1), a_lap(2)]),
            2: (a_run(2), [a_lap(1)]),
            1: (a_run(1), []),
        }

    def test_saves_only_the_latest_runs_up_to_the_limit(self):
        store = FakeStore()
        source = FakeRunSource([a_run(3), a_run(2), a_run(1)])

        new = sync_garmin(source, store, limit=2)

        assert new == 2
        assert set(store.garmin) == {3, 2}

    def test_fetches_laps_only_for_runs_not_yet_stored(self):
        store = FakeStore(garmin={2: (a_run(2), [])})
        source = FakeRunSource([a_run(3), a_run(2), a_run(1)])

        sync_garmin(source, store, limit=3)

        assert source.laps_requested == [3, 1]

    def test_saves_nothing_when_rerun(self):
        store = FakeStore()
        source = FakeRunSource([a_run(1)])
        sync_garmin(source, store, A_VERY_LARGE_LIMIT)

        new = sync_garmin(source, store, A_VERY_LARGE_LIMIT)

        assert new == 0

    def test_logs_runs_listed_and_each_saved_run(self, caplog):
        caplog.set_level(logging.INFO, logger="sasoi.ingest.sync")
        store = FakeStore(garmin={2: (a_run(2), [])})
        source = FakeRunSource(
            [
                a_run(3, start_time_local=datetime(2024, 1, 2, 7, 0), name="Morning Run"),
                a_run(2),
                a_run(1, start_time_local=datetime(2024, 1, 1, 18, 30), name="Evening Run"),
            ]
        )

        sync_garmin(source, store, A_VERY_LARGE_LIMIT)

        assert caplog.messages == [
            "garmin: 3 runs listed, 2 new",
            "garmin: saved 1/2 run 3 2024-01-02 07:00:00 Morning Run",
            "garmin: saved 2/2 run 1 2024-01-01 18:30:00 Evening Run",
        ]

    def test_logs_a_run_without_a_name(self, caplog):
        caplog.set_level(logging.INFO, logger="sasoi.ingest.sync")
        source = FakeRunSource([a_run(1, start_time_local=datetime(2024, 1, 3, 7, 15), name=None)])

        sync_garmin(source, FakeStore(), A_VERY_LARGE_LIMIT)

        assert caplog.messages == [
            "garmin: 1 runs listed, 1 new",
            "garmin: saved 1/1 run 1 2024-01-03 07:15:00 (no name)",
        ]


class TestSyncHevy:
    def test_saves_every_workout_into_an_empty_store(self):
        store = FakeWorkoutStore()

        new = sync_hevy(FakeWorkoutSource([a_workout("w-1"), a_workout("w-2")]), store)

        assert (new, store.hevy) == (2, {"w-1": a_workout("w-1"), "w-2": a_workout("w-2")})

    def test_keeps_stored_workouts_and_saves_only_new_ones(self):
        store = FakeWorkoutStore(hevy={"w-1": a_workout("w-1", name="Stored")})

        new = sync_hevy(FakeWorkoutSource([a_workout("w-1", name="Edited"), a_workout("w-2")]), store)

        assert (new, store.hevy) == (1, {"w-1": a_workout("w-1", name="Stored"), "w-2": a_workout("w-2")})

    def test_logs_workouts_listed_and_each_saved_workout(self, caplog):
        caplog.set_level(logging.INFO, logger="sasoi.ingest.sync")
        store = FakeWorkoutStore(hevy={"w-1": a_workout("w-1")})
        source = FakeWorkoutSource(
            [
                a_workout("w-1"),
                a_workout("w-2", start_time_utc=datetime(2024, 1, 2, 18, 0, tzinfo=UTC), name="Full Body A"),
            ]
        )

        sync_hevy(source, store)

        assert caplog.messages == [
            "hevy: 2 workouts listed, 1 new",
            "hevy: saved 1/1 workout w-2 2024-01-02 18:00:00+00:00 Full Body A",
        ]
