import psycopg
import pytest
from builders import a_lap, a_run
from psycopg.rows import class_row

from sasoi.ingest.postgres_run_store import PostgresRunStore
from sasoi.ingest.runs import Lap, Run
from sasoi.sync_cli import migrate


@pytest.fixture
def conn(database_url):
    migrate(database_url)
    with psycopg.connect(database_url, autocommit=True) as conn:
        conn.execute("TRUNCATE garmin_runs CASCADE")
        yield conn


@pytest.fixture
def store(conn):
    return PostgresRunStore(conn)


def stored_runs(conn) -> list[Run]:
    with conn.cursor(row_factory=class_row(Run)) as cursor:
        return cursor.execute("SELECT * FROM garmin_runs ORDER BY activity_id").fetchall()


def stored_laps(conn, activity_id: int) -> list[Lap]:
    columns = ", ".join(Lap.__dataclass_fields__)
    with conn.cursor(row_factory=class_row(Lap)) as cursor:
        query = f"SELECT {columns} FROM garmin_laps WHERE activity_id = %s ORDER BY lap_index"
        return cursor.execute(query, (activity_id,)).fetchall()


class TestPostgresRunStore:
    def test_stored_garmin_ids_is_empty_for_an_empty_table(self, store):
        assert store.stored_garmin_ids() == set()

    def test_stored_garmin_ids_returns_the_ids_of_saved_runs(self, store):
        store.save_garmin_run(a_run(7), [])
        store.save_garmin_run(a_run(8), [])

        assert store.stored_garmin_ids() == {7, 8}

    def test_saves_every_run_field(self, store, conn):
        store.save_garmin_run(a_run(7), [])

        assert stored_runs(conn) == [a_run(7)]

    def test_saves_empty_optional_run_fields_as_null(self, store, conn):
        store.save_garmin_run(a_run(7, name=None, avg_hr=None, vo2max=None, lap_count=None), [])

        assert stored_runs(conn) == [a_run(7, name=None, avg_hr=None, vo2max=None, lap_count=None)]

    def test_saves_the_laps_of_the_run(self, store, conn):
        store.save_garmin_run(a_run(7), [a_lap(1, distance_m=1000.0), a_lap(2, distance_m=600.0, avg_hr=None)])

        assert stored_laps(conn, 7) == [a_lap(1, distance_m=1000.0), a_lap(2, distance_m=600.0, avg_hr=None)]

    def test_keeps_the_first_save_when_a_run_is_saved_twice(self, store, conn):
        store.save_garmin_run(a_run(7, distance_m=5000.0), [a_lap(1, distance_m=5000.0)])
        store.save_garmin_run(a_run(7, distance_m=9999.0), [a_lap(1, distance_m=9999.0)])

        assert (stored_runs(conn), stored_laps(conn, 7)) == (
            [a_run(7, distance_m=5000.0)],
            [a_lap(1, distance_m=5000.0)],
        )
