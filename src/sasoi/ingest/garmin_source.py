from typing import Any, Protocol, cast

from sasoi.ingest.garmin_types import GarminActivity, GarminSplits

# garminconnect rejects get_activities calls asking for more than 1000 activities.
# A single call keeps recent_runs simple. Syncing more runs needs a code change, not just
# a higher SASOI_GARMIN_LIMIT: drop this cap and page through get_activities with its start offset.
MAX_RECENT_RUNS = 1000


class GarminApi(Protocol):
    def get_activities(self, start: int, limit: int, activitytype: str | None) -> dict[str, Any] | list[Any]: ...

    def get_activity_splits(self, activity_id: str) -> dict[str, Any]: ...


class GarminSource:
    def __init__(self, api: GarminApi):
        self._api = api

    def recent_runs(self, limit: int) -> list[GarminActivity]:
        return cast(list[GarminActivity], self._api.get_activities(0, limit, "running"))

    def splits(self, activity_id: int) -> GarminSplits:
        return cast(GarminSplits, self._api.get_activity_splits(str(activity_id)))
