import logging
from typing import Protocol

from sasoi.ingest.garmin_types import GarminActivity, GarminSplits


class RunSource(Protocol):
    def recent_runs(self, limit: int) -> list[GarminActivity]: ...

    def splits(self, activity_id: int) -> GarminSplits: ...


class RunStore(Protocol):
    def stored_garmin_ids(self) -> set[int]: ...

    def save_garmin_run(self, summary: GarminActivity, splits: GarminSplits) -> None: ...


log = logging.getLogger(__name__)


def sync_garmin(source: RunSource, store: RunStore, limit: int) -> int:
    stored = store.stored_garmin_ids()
    runs = source.recent_runs(limit)
    new_runs = [run for run in runs if run["activityId"] not in stored]
    log.info("garmin: %d runs listed, %d new", len(runs), len(new_runs))
    for saved, run in enumerate(new_runs, start=1):
        store.save_garmin_run(run, source.splits(run["activityId"]))
        log.info(
            "garmin: saved %d/%d run %d %s %s",
            saved,
            len(new_runs),
            run["activityId"],
            run["startTimeLocal"],
            run.get("activityName", "(no name)"),
        )
    return len(new_runs)
