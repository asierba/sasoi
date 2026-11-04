from typing import TypedDict


class HevySet(TypedDict):
    index: int
    indicator: str
    weight_kg: float | None
    reps: int | None
    duration_seconds: float | None
    distance_meters: float | None
    rpe: float | None
    completed_at: str | None


class HevyExercise(TypedDict):
    title: str
    exercise_template_id: str
    exercise_type: str
    muscle_group: str
    other_muscles: list[str]
    equipment_category: str
    superset_id: int | None
    notes: str
    sets: list[HevySet]


class HevyWorkout(TypedDict):
    id: str
    index: int
    name: str
    description: str
    start_time: int
    end_time: int
    exercises: list[HevyExercise]
