from typing import NotRequired, TypedDict


class ActivityType(TypedDict):
    typeKey: str


class GarminActivity(TypedDict):
    activityId: int
    activityName: NotRequired[str]
    activityType: ActivityType
    startTimeLocal: str
    startTimeGMT: str
    distance: float
    duration: float
    movingDuration: NotRequired[float]
    averageSpeed: float
    maxSpeed: float
    averageHR: NotRequired[float]
    maxHR: NotRequired[float]
    hrTimeInZone_1: NotRequired[float]
    hrTimeInZone_2: NotRequired[float]
    hrTimeInZone_3: NotRequired[float]
    hrTimeInZone_4: NotRequired[float]
    hrTimeInZone_5: NotRequired[float]
    averageRunningCadenceInStepsPerMinute: float
    maxRunningCadenceInStepsPerMinute: float
    elevationGain: float
    elevationLoss: float
    aerobicTrainingEffect: NotRequired[float]
    anaerobicTrainingEffect: NotRequired[float]
    activityTrainingLoad: NotRequired[float]
    vO2MaxValue: NotRequired[float]
    lapCount: NotRequired[int]


class GarminLap(TypedDict):
    lapIndex: int
    startTimeGMT: str
    distance: float
    duration: float
    averageSpeed: float
    maxSpeed: float
    averageHR: NotRequired[float]
    maxHR: NotRequired[float]
    averageRunCadence: float
    elevationGain: float
    elevationLoss: float
    intensityType: NotRequired[str]


class GarminSplits(TypedDict):
    activityId: int
    lapDTOs: list[GarminLap]
