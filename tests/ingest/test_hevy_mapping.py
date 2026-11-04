from datetime import UTC, datetime

from sasoi.ingest.hevy_mapping import to_workout
from sasoi.ingest.hevy_types import HevyExercise, HevySet, HevyWorkout
from sasoi.ingest.workouts import Exercise, Workout, WorkoutSet


def a_hevy_workout(exercises: list[HevyExercise], description: str = "") -> HevyWorkout:
    return {
        "id": "00000000-0000-0000-0000-000000000001",
        "index": 1,
        "name": "Full Body A",
        "description": description,
        "start_time": 1704218400,
        "end_time": 1704222000,
        "exercises": exercises,
    }


def a_hevy_exercise(sets: list[HevySet], notes: str = "") -> HevyExercise:
    return {
        "title": "Goblet Squat",
        "exercise_template_id": "A1B2C3D4",
        "exercise_type": "weight_reps",
        "muscle_group": "quadriceps",
        "other_muscles": [],
        "equipment_category": "dumbbell",
        "superset_id": None,
        "notes": notes,
        "sets": sets,
    }


def a_hevy_set(index: int, completed_at: str | None) -> HevySet:
    return {
        "index": index,
        "indicator": "normal",
        "weight_kg": 20.0,
        "reps": 10,
        "duration_seconds": None,
        "distance_meters": None,
        "rpe": None,
        "completed_at": completed_at,
    }


class TestToWorkout:
    def test_maps_every_field(self):
        workout: HevyWorkout = {
            "id": "00000000-0000-0000-0000-000000000007",
            "index": 42,
            "name": "Full Body A",
            "description": "Felt strong",
            "start_time": 1704218400,
            "end_time": 1704222000,
            "exercises": [
                {
                    "title": "Goblet Squat",
                    "exercise_template_id": "A1B2C3D4",
                    "exercise_type": "weight_reps",
                    "muscle_group": "quadriceps",
                    "other_muscles": ["glutes", "hamstrings"],
                    "equipment_category": "dumbbell",
                    "superset_id": 1,
                    "notes": "Slow descent",
                    "sets": [
                        {
                            "index": 0,
                            "indicator": "warmup",
                            "weight_kg": 12.5,
                            "reps": 8,
                            "duration_seconds": 45,
                            "distance_meters": 100,
                            "rpe": 7.5,
                            "completed_at": "2024-01-02T18:10:30.500Z",
                        }
                    ],
                }
            ],
        }

        assert to_workout(workout) == Workout(
            workout_id="00000000-0000-0000-0000-000000000007",
            name="Full Body A",
            description="Felt strong",
            start_time_utc=datetime(2024, 1, 2, 18, 0, tzinfo=UTC),
            end_time_utc=datetime(2024, 1, 2, 19, 0, tzinfo=UTC),
            exercises=[
                Exercise(
                    exercise_index=0,
                    title="Goblet Squat",
                    template_id="A1B2C3D4",
                    exercise_type="weight_reps",
                    muscle_group="quadriceps",
                    other_muscles=["glutes", "hamstrings"],
                    equipment="dumbbell",
                    superset_id=1,
                    notes="Slow descent",
                    sets=[
                        WorkoutSet(
                            set_index=0,
                            set_type="warmup",
                            weight_kg=12.5,
                            reps=8,
                            duration_s=45,
                            distance_m=100,
                            rpe=7.5,
                            completed_at_utc=datetime(2024, 1, 2, 18, 10, 30, 500000, tzinfo=UTC),
                        )
                    ],
                )
            ],
        )

    def test_numbers_exercises_in_the_order_hevy_lists_them(self):
        workout = a_hevy_workout([a_hevy_exercise([]), a_hevy_exercise([]), a_hevy_exercise([])])

        assert [exercise.exercise_index for exercise in to_workout(workout).exercises] == [0, 1, 2]

    def test_leaves_empty_description_and_notes_empty(self):
        workout = a_hevy_workout([a_hevy_exercise([], notes="")], description="")

        mapped = to_workout(workout)

        assert (mapped.description, mapped.exercises[0].notes) == (None, None)

    def test_leaves_completion_time_empty_when_missing(self):
        workout = a_hevy_workout([a_hevy_exercise([a_hevy_set(0, completed_at=None)])])

        assert to_workout(workout).exercises[0].sets[0].completed_at_utc is None
