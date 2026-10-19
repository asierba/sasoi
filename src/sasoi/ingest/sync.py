from typing import Protocol

from sasoi.ingest.garmin_types import GarminActivity, GarminSplits


class RunSource(Protocol):
    def recent_runs(self, limit: int) -> list[GarminActivity]: ...

    def splits(self, activity_id: int) -> GarminSplits: ...


class RunStore(Protocol):
    def stored_garmin_ids(self) -> set[int]: ...

    def save_garmin_run(self, summary: GarminActivity, splits: GarminSplits) -> None: ...


def sync_garmin(source: RunSource, store: RunStore, limit: int) -> int:
    stored = store.stored_garmin_ids()
    new_runs = [run for run in source.recent_runs(limit) if run["activityId"] not in stored]
    for run in new_runs:
        store.save_garmin_run(run, source.splits(run["activityId"]))
    return len(new_runs)
