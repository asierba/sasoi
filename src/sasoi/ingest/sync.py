import logging
from typing import Protocol

from sasoi.ingest.runs import Lap, Run
from sasoi.ingest.workouts import Workout


class RunSource(Protocol):
    def recent_runs(self, limit: int) -> list[Run]: ...

    def laps(self, activity_id: int) -> list[Lap]: ...


class RunStore(Protocol):
    def stored_garmin_ids(self) -> set[int]: ...

    def save_garmin_run(self, run: Run, laps: list[Lap]) -> None: ...


class WorkoutSource(Protocol):
    def all_workouts(self) -> list[Workout]: ...


class WorkoutStore(Protocol):
    def stored_hevy_ids(self) -> set[str]: ...

    def save_hevy_workout(self, workout: Workout) -> None: ...


log = logging.getLogger(__name__)


def sync_garmin(source: RunSource, store: RunStore, limit: int) -> int:
    stored = store.stored_garmin_ids()
    runs = source.recent_runs(limit)
    new_runs = [run for run in runs if run.activity_id not in stored]
    log.info("garmin: %d runs listed, %d new", len(runs), len(new_runs))
    for saved, run in enumerate(new_runs, start=1):
        store.save_garmin_run(run, source.laps(run.activity_id))
        log.info(
            "garmin: saved %d/%d run %d %s %s",
            saved,
            len(new_runs),
            run.activity_id,
            run.start_time_local,
            run.name or "(no name)",
        )
    return len(new_runs)


def sync_hevy(source: WorkoutSource, store: WorkoutStore) -> int:
    stored = store.stored_hevy_ids()
    workouts = source.all_workouts()
    new_workouts = [workout for workout in workouts if workout.workout_id not in stored]
    log.info("hevy: %d workouts listed, %d new", len(workouts), len(new_workouts))
    for saved, workout in enumerate(new_workouts, start=1):
        store.save_hevy_workout(workout)
        log.info(
            "hevy: saved %d/%d workout %s %s %s",
            saved,
            len(new_workouts),
            workout.workout_id,
            workout.start_time_utc,
            workout.name,
        )
    return len(new_workouts)
