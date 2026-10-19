import logging
from typing import Protocol

from sasoi.ingest.runs import Lap, Run


class RunSource(Protocol):
    def recent_runs(self, limit: int) -> list[Run]: ...

    def laps(self, activity_id: int) -> list[Lap]: ...


class RunStore(Protocol):
    def stored_garmin_ids(self) -> set[int]: ...

    def save_garmin_run(self, run: Run, laps: list[Lap]) -> None: ...


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
