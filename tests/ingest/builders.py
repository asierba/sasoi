from dataclasses import replace
from datetime import UTC, datetime

from sasoi.ingest.runs import Lap, Run
from sasoi.ingest.workouts import Exercise, Workout, WorkoutSet

A_RUN = Run(
    activity_id=1,
    activity_type="running",
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

A_LAP = Lap(
    lap_index=1,
    start_time_utc=datetime(2024, 1, 2, 6, 0, tzinfo=UTC),
    distance_m=1000.0,
    duration_s=360.0,
    avg_speed_mps=2.78,
    max_speed_mps=3.2,
    avg_hr=148.0,
    max_hr=160.0,
    avg_cadence_spm=165.0,
    elevation_gain_m=4.0,
    elevation_loss_m=3.0,
    intensity_type="ACTIVE",
)

A_WORKOUT_SET = WorkoutSet(
    set_index=0,
    set_type="normal",
    weight_kg=20.0,
    reps=10,
    duration_s=None,
    distance_m=None,
    rpe=None,
    completed_at_utc=datetime(2024, 1, 2, 18, 10, tzinfo=UTC),
)

AN_EXERCISE = Exercise(
    exercise_index=0,
    title="Goblet Squat",
    template_id="A1B2C3D4",
    exercise_type="weight_reps",
    muscle_group="quadriceps",
    other_muscles=["glutes"],
    equipment="dumbbell",
    superset_id=None,
    notes=None,
    sets=[],
)

A_WORKOUT = Workout(
    workout_id="00000000-0000-0000-0000-000000000001",
    name="Full Body A",
    description=None,
    start_time_utc=datetime(2024, 1, 2, 18, 0, tzinfo=UTC),
    end_time_utc=datetime(2024, 1, 2, 19, 0, tzinfo=UTC),
    exercises=[],
)


def a_run(activity_id: int, **changes) -> Run:
    return replace(A_RUN, activity_id=activity_id, **changes)


def a_lap(lap_index: int, **changes) -> Lap:
    return replace(A_LAP, lap_index=lap_index, **changes)


def a_workout(workout_id: str, **changes) -> Workout:
    return replace(A_WORKOUT, workout_id=workout_id, **changes)


def an_exercise(exercise_index: int, **changes) -> Exercise:
    return replace(AN_EXERCISE, exercise_index=exercise_index, **changes)


def a_workout_set(set_index: int, **changes) -> WorkoutSet:
    return replace(A_WORKOUT_SET, set_index=set_index, **changes)
