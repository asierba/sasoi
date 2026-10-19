from datetime import UTC, datetime

from sasoi.ingest.garmin_mapping import to_lap, to_run
from sasoi.ingest.garmin_types import GarminActivity, GarminLap
from sasoi.ingest.runs import Lap, Run


class TestToRun:
    def test_maps_every_field(self):
        activity: GarminActivity = {
            "activityId": 7,
            "activityName": "Morning Run",
            "activityType": {"typeKey": "trail_running"},
            "startTimeLocal": "2024-01-02 07:00:00",
            "startTimeGMT": "2024-01-02 06:00:00",
            "distance": 5000.0,
            "duration": 1800.0,
            "movingDuration": 1790.0,
            "averageSpeed": 2.78,
            "maxSpeed": 3.5,
            "averageHR": 150.0,
            "maxHR": 170.0,
            "hrTimeInZone_1": 60.0,
            "hrTimeInZone_2": 600.0,
            "hrTimeInZone_3": 900.0,
            "hrTimeInZone_4": 240.0,
            "hrTimeInZone_5": 0.0,
            "averageRunningCadenceInStepsPerMinute": 165.0,
            "maxRunningCadenceInStepsPerMinute": 180.0,
            "elevationGain": 20.0,
            "elevationLoss": 18.0,
            "aerobicTrainingEffect": 3.0,
            "anaerobicTrainingEffect": 0.5,
            "activityTrainingLoad": 80.0,
            "vO2MaxValue": 50.0,
            "lapCount": 5,
        }

        assert to_run(activity) == Run(
            activity_id=7,
            activity_type="trail_running",
            name="Morning Run",
            start_time_local=datetime(2024, 1, 2, 7, 0),
            start_time_utc=datetime(2024, 1, 2, 6, 0, tzinfo=UTC),
            distance_m=5000.0,
            duration_s=1800.0,
            moving_duration_s=1790.0,
            avg_speed_mps=2.78,
            max_speed_mps=3.5,
            avg_hr=150.0,
            max_hr=170.0,
            hr_zone_1_s=60.0,
            hr_zone_2_s=600.0,
            hr_zone_3_s=900.0,
            hr_zone_4_s=240.0,
            hr_zone_5_s=0.0,
            avg_cadence_spm=165.0,
            max_cadence_spm=180.0,
            elevation_gain_m=20.0,
            elevation_loss_m=18.0,
            aerobic_training_effect=3.0,
            anaerobic_training_effect=0.5,
            training_load=80.0,
            vo2max=50.0,
            lap_count=5,
        )

    def test_leaves_fields_missing_on_old_runs_empty(self):
        activity: GarminActivity = {
            "activityId": 7,
            "activityType": {"typeKey": "running"},
            "startTimeLocal": "2015-11-20 06:57:15",
            "startTimeGMT": "2015-11-20 06:57:15",
            "distance": 5000.0,
            "duration": 1800.0,
            "averageSpeed": 2.78,
            "maxSpeed": 3.5,
            "averageRunningCadenceInStepsPerMinute": 165.0,
            "maxRunningCadenceInStepsPerMinute": 180.0,
            "elevationGain": 20.0,
            "elevationLoss": 18.0,
        }

        run = to_run(activity)

        optional = {
            "name": run.name,
            "moving_duration_s": run.moving_duration_s,
            "avg_hr": run.avg_hr,
            "max_hr": run.max_hr,
            "hr_zone_1_s": run.hr_zone_1_s,
            "hr_zone_2_s": run.hr_zone_2_s,
            "hr_zone_3_s": run.hr_zone_3_s,
            "hr_zone_4_s": run.hr_zone_4_s,
            "hr_zone_5_s": run.hr_zone_5_s,
            "aerobic_training_effect": run.aerobic_training_effect,
            "anaerobic_training_effect": run.anaerobic_training_effect,
            "training_load": run.training_load,
            "vo2max": run.vo2max,
            "lap_count": run.lap_count,
        }
        assert optional == dict.fromkeys(optional)


class TestToLap:
    def test_maps_every_field(self):
        lap: GarminLap = {
            "lapIndex": 2,
            "startTimeGMT": "2024-01-02T06:06:00.0",
            "distance": 1000.0,
            "duration": 360.0,
            "averageSpeed": 2.78,
            "maxSpeed": 3.2,
            "averageHR": 148.0,
            "maxHR": 160.0,
            "averageRunCadence": 165.0,
            "elevationGain": 4.0,
            "elevationLoss": 3.0,
            "intensityType": "INTERVAL",
        }

        assert to_lap(lap) == Lap(
            lap_index=2,
            start_time_utc=datetime(2024, 1, 2, 6, 6, tzinfo=UTC),
            distance_m=1000.0,
            duration_s=360.0,
            avg_speed_mps=2.78,
            max_speed_mps=3.2,
            avg_hr=148.0,
            max_hr=160.0,
            avg_cadence_spm=165.0,
            elevation_gain_m=4.0,
            elevation_loss_m=3.0,
            intensity_type="INTERVAL",
        )

    def test_leaves_heart_rate_and_intensity_empty_when_missing(self):
        lap: GarminLap = {
            "lapIndex": 1,
            "startTimeGMT": "2015-11-20T06:57:15.0",
            "distance": 1000.0,
            "duration": 360.0,
            "averageSpeed": 2.78,
            "maxSpeed": 3.2,
            "averageRunCadence": 165.0,
            "elevationGain": 4.0,
            "elevationLoss": 3.0,
        }

        mapped = to_lap(lap)

        assert (mapped.avg_hr, mapped.max_hr, mapped.intensity_type) == (None, None, None)
