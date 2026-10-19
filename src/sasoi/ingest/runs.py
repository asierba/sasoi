from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Lap:
    lap_index: int
    start_time_utc: datetime
    distance_m: float
    duration_s: float
    avg_speed_mps: float
    max_speed_mps: float
    avg_hr: float | None
    max_hr: float | None
    avg_cadence_spm: float
    elevation_gain_m: float
    elevation_loss_m: float
    intensity_type: str | None


@dataclass(frozen=True)
class Run:
    activity_id: int
    activity_type: str
    name: str | None
    start_time_local: datetime
    start_time_utc: datetime
    distance_m: float
    duration_s: float
    moving_duration_s: float | None
    avg_speed_mps: float
    max_speed_mps: float
    avg_hr: float | None
    max_hr: float | None
    hr_zone_1_s: float | None
    hr_zone_2_s: float | None
    hr_zone_3_s: float | None
    hr_zone_4_s: float | None
    hr_zone_5_s: float | None
    avg_cadence_spm: float
    max_cadence_spm: float
    elevation_gain_m: float
    elevation_loss_m: float
    aerobic_training_effect: float | None
    anaerobic_training_effect: float | None
    training_load: float | None
    vo2max: float | None
    lap_count: int | None
