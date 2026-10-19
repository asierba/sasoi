from datetime import UTC, datetime

from sasoi.ingest.garmin_types import GarminActivity, GarminLap
from sasoi.ingest.runs import Lap, Run


def to_run(activity: GarminActivity) -> Run:
    return Run(
        activity_id=activity["activityId"],
        activity_type=activity["activityType"]["typeKey"],
        name=activity.get("activityName"),
        start_time_local=datetime.fromisoformat(activity["startTimeLocal"]),
        start_time_utc=_utc(activity["startTimeGMT"]),
        distance_m=activity["distance"],
        duration_s=activity["duration"],
        moving_duration_s=activity.get("movingDuration"),
        avg_speed_mps=activity["averageSpeed"],
        max_speed_mps=activity["maxSpeed"],
        avg_hr=activity.get("averageHR"),
        max_hr=activity.get("maxHR"),
        hr_zone_1_s=activity.get("hrTimeInZone_1"),
        hr_zone_2_s=activity.get("hrTimeInZone_2"),
        hr_zone_3_s=activity.get("hrTimeInZone_3"),
        hr_zone_4_s=activity.get("hrTimeInZone_4"),
        hr_zone_5_s=activity.get("hrTimeInZone_5"),
        avg_cadence_spm=activity["averageRunningCadenceInStepsPerMinute"],
        max_cadence_spm=activity["maxRunningCadenceInStepsPerMinute"],
        elevation_gain_m=activity["elevationGain"],
        elevation_loss_m=activity["elevationLoss"],
        aerobic_training_effect=activity.get("aerobicTrainingEffect"),
        anaerobic_training_effect=activity.get("anaerobicTrainingEffect"),
        training_load=activity.get("activityTrainingLoad"),
        vo2max=activity.get("vO2MaxValue"),
        lap_count=activity.get("lapCount"),
    )


def to_lap(lap: GarminLap) -> Lap:
    return Lap(
        lap_index=lap["lapIndex"],
        start_time_utc=_utc(lap["startTimeGMT"]),
        distance_m=lap["distance"],
        duration_s=lap["duration"],
        avg_speed_mps=lap["averageSpeed"],
        max_speed_mps=lap["maxSpeed"],
        avg_hr=lap.get("averageHR"),
        max_hr=lap.get("maxHR"),
        avg_cadence_spm=lap["averageRunCadence"],
        elevation_gain_m=lap["elevationGain"],
        elevation_loss_m=lap["elevationLoss"],
        intensity_type=lap.get("intensityType"),
    )


def _utc(timestamp: str) -> datetime:
    return datetime.fromisoformat(timestamp).replace(tzinfo=UTC)
