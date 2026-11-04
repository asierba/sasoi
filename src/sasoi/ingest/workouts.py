from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class WorkoutSet:
    set_index: int
    set_type: str
    weight_kg: float | None
    reps: int | None
    duration_s: float | None
    distance_m: float | None
    rpe: float | None
    completed_at_utc: datetime | None


@dataclass(frozen=True)
class Exercise:
    exercise_index: int
    title: str
    template_id: str
    exercise_type: str
    muscle_group: str
    other_muscles: list[str]
    equipment: str
    superset_id: int | None
    notes: str | None
    sets: list[WorkoutSet]


@dataclass(frozen=True)
class Workout:
    workout_id: str
    name: str
    description: str | None
    start_time_utc: datetime
    end_time_utc: datetime
    exercises: list[Exercise]
