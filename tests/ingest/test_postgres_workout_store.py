import psycopg
import pytest
from builders import a_workout, a_workout_set, an_exercise
from psycopg.rows import class_row, dict_row

from sasoi.ingest.postgres_workout_store import PostgresWorkoutStore
from sasoi.ingest.workouts import Exercise, Workout, WorkoutSet
from sasoi.sync_cli import migrate


@pytest.fixture
def conn(database_url):
    migrate(database_url)
    with psycopg.connect(database_url, autocommit=True) as conn:
        conn.execute("TRUNCATE hevy_workouts CASCADE")
        yield conn


@pytest.fixture
def store(conn):
    return PostgresWorkoutStore(conn)


def stored_workouts(conn) -> list[Workout]:
    with conn.cursor(row_factory=dict_row) as cursor:
        rows = cursor.execute("SELECT * FROM hevy_workouts ORDER BY workout_id").fetchall()
    return [Workout(**row, exercises=stored_exercises(conn, row["workout_id"])) for row in rows]


def stored_exercises(conn, workout_id: str) -> list[Exercise]:
    with conn.cursor(row_factory=dict_row) as cursor:
        query = "SELECT * FROM hevy_exercises WHERE workout_id = %s ORDER BY exercise_index"
        rows = cursor.execute(query, (workout_id,)).fetchall()
    return [
        Exercise(**{k: v for k, v in row.items() if k != "workout_id"}, sets=stored_sets(conn, workout_id, row))
        for row in rows
    ]


def stored_sets(conn, workout_id: str, exercise: dict) -> list[WorkoutSet]:
    columns = ", ".join(WorkoutSet.__dataclass_fields__)
    query = f"SELECT {columns} FROM hevy_sets WHERE workout_id = %s AND exercise_index = %s ORDER BY set_index"
    with conn.cursor(row_factory=class_row(WorkoutSet)) as cursor:
        return cursor.execute(query, (workout_id, exercise["exercise_index"])).fetchall()


class TestPostgresWorkoutStore:
    def test_stored_hevy_ids_is_empty_for_an_empty_table(self, store):
        assert store.stored_hevy_ids() == set()

    def test_stored_hevy_ids_returns_the_ids_of_saved_workouts(self, store):
        store.save_hevy_workout(a_workout("w-1"))
        store.save_hevy_workout(a_workout("w-2"))

        assert store.stored_hevy_ids() == {"w-1", "w-2"}

    def test_saves_every_field_of_the_workout_its_exercises_and_their_sets(self, store, conn):
        workout = a_workout(
            "w-1",
            description="Felt strong",
            exercises=[
                an_exercise(0, other_muscles=["glutes"], superset_id=1, notes="Slow descent", sets=[a_workout_set(0)]),
                an_exercise(1, sets=[a_workout_set(0, rpe=8.0), a_workout_set(1, duration_s=30.0, distance_m=100.0)]),
            ],
        )

        store.save_hevy_workout(workout)

        assert stored_workouts(conn) == [workout]

    def test_saves_empty_optional_fields_as_null(self, store, conn):
        workout = a_workout(
            "w-1",
            description=None,
            exercises=[
                an_exercise(
                    0,
                    superset_id=None,
                    notes=None,
                    sets=[a_workout_set(0, weight_kg=None, reps=None, rpe=None, completed_at_utc=None)],
                )
            ],
        )

        store.save_hevy_workout(workout)

        assert stored_workouts(conn) == [workout]

    def test_keeps_the_first_save_when_a_workout_is_saved_twice(self, store, conn):
        store.save_hevy_workout(a_workout("w-1", name="First", exercises=[an_exercise(0, sets=[a_workout_set(0)])]))
        store.save_hevy_workout(a_workout("w-1", name="Second", exercises=[an_exercise(0, sets=[a_workout_set(0)])]))

        assert stored_workouts(conn) == [
            a_workout("w-1", name="First", exercises=[an_exercise(0, sets=[a_workout_set(0)])])
        ]
