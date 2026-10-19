from typing import Any, NotRequired, TypedDict


class ActivityType(TypedDict):
    typeKey: str


class GarminActivity(TypedDict):
    activityId: int
    activityName: NotRequired[str]
    activityType: ActivityType
    startTimeLocal: str


class GarminSplits(TypedDict):
    activityId: int
    lapDTOs: list[dict[str, Any]]
    eventDTOs: list[dict[str, Any]]
