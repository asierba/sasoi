from dataclasses import fields
from typing import Any

import psycopg
from psycopg import sql

from sasoi.ingest.workouts import Exercise, Workout, WorkoutSet

WORKOUT_FIELDS = [field.name for field in fields(Workout) if field.name != "exercises"]
EXERCISE_FIELDS = [field.name for field in fields(Exercise) if field.name != "sets"]
SET_FIELDS = [field.name for field in fields(WorkoutSet)]


class PostgresWorkoutStore:
    def __init__(self, conn: psycopg.Connection):
        self._conn = conn

    def stored_hevy_ids(self) -> set[str]:
        return {row[0] for row in self._conn.execute("SELECT workout_id FROM hevy_workouts")}

    def save_hevy_workout(self, workout: Workout) -> None:
        with self._conn.transaction(), self._conn.cursor() as cursor:
            cursor.execute(_insert("hevy_workouts", WORKOUT_FIELDS), _row(workout, WORKOUT_FIELDS))
            cursor.executemany(_insert("hevy_exercises", ["workout_id", *EXERCISE_FIELDS]), _exercise_rows(workout))
            cursor.executemany(_insert("hevy_sets", ["workout_id", "exercise_index", *SET_FIELDS]), _set_rows(workout))


def _exercise_rows(workout: Workout) -> list[dict[str, Any]]:
    return [{"workout_id": workout.workout_id, **_row(exercise, EXERCISE_FIELDS)} for exercise in workout.exercises]


def _set_rows(workout: Workout) -> list[dict[str, Any]]:
    return [
        {"workout_id": workout.workout_id, "exercise_index": exercise.exercise_index, **_row(workout_set, SET_FIELDS)}
        for exercise in workout.exercises
        for workout_set in exercise.sets
    ]


def _row(record: object, field_names: list[str]) -> dict[str, Any]:
    return {name: getattr(record, name) for name in field_names}


def _insert(table: str, columns: list[str]) -> sql.Composed:
    return sql.SQL("INSERT INTO {} ({}) VALUES ({}) ON CONFLICT DO NOTHING").format(
        sql.Identifier(table),
        sql.SQL(", ").join(map(sql.Identifier, columns)),
        sql.SQL(", ").join(map(sql.Placeholder, columns)),
    )
