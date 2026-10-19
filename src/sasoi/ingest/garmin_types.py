from typing import Any, TypedDict


class ActivityType(TypedDict):
    typeKey: str


class GarminActivity(TypedDict):
    activityId: int
    activityType: ActivityType


class GarminSplits(TypedDict):
    activityId: int
    lapDTOs: list[dict[str, Any]]
    eventDTOs: list[dict[str, Any]]
