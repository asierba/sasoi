from datetime import UTC, datetime

from sasoi.ingest.hevy_types import HevyExercise, HevySet, HevyWorkout
from sasoi.ingest.workouts import Exercise, Workout, WorkoutSet


def to_workout(workout: HevyWorkout) -> Workout:
    return Workout(
        workout_id=workout["id"],
        name=workout["name"],
        description=workout["description"] or None,
        start_time_utc=datetime.fromtimestamp(workout["start_time"], UTC),
        end_time_utc=datetime.fromtimestamp(workout["end_time"], UTC),
        exercises=[_to_exercise(index, exercise) for index, exercise in enumerate(workout["exercises"])],
    )


def _to_exercise(index: int, exercise: HevyExercise) -> Exercise:
    return Exercise(
        exercise_index=index,
        title=exercise["title"],
        template_id=exercise["exercise_template_id"],
        exercise_type=exercise["exercise_type"],
        muscle_group=exercise["muscle_group"],
        other_muscles=exercise["other_muscles"],
        equipment=exercise["equipment_category"],
        superset_id=exercise["superset_id"],
        notes=exercise["notes"] or None,
        sets=[_to_set(workout_set) for workout_set in exercise["sets"]],
    )


def _to_set(workout_set: HevySet) -> WorkoutSet:
    completed_at = workout_set["completed_at"]
    return WorkoutSet(
        set_index=workout_set["index"],
        set_type=workout_set["indicator"],
        weight_kg=workout_set["weight_kg"],
        reps=workout_set["reps"],
        duration_s=workout_set["duration_seconds"],
        distance_m=workout_set["distance_meters"],
        rpe=workout_set["rpe"],
        completed_at_utc=datetime.fromisoformat(completed_at) if completed_at else None,
    )
