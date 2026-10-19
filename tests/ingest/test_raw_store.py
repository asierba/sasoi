import os

import psycopg
import pytest

from sasoi.ingest.garmin_types import GarminActivity, GarminSplits
from sasoi.ingest.raw_store import RawStore
from sasoi.sync_cli import migrate

A_SPLITS: GarminSplits = {"activityId": 0, "lapDTOs": [], "eventDTOs": []}


@pytest.fixture
def conn():
    database_url = os.environ.get("TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("TEST_DATABASE_URL not set")
    migrate(database_url)
    with psycopg.connect(database_url, autocommit=True) as conn:
        conn.execute("TRUNCATE garmin_runs")
        yield conn


@pytest.fixture
def store(conn):
    return RawStore(conn)


def a_run(activity_id: int) -> GarminActivity:
    return {"activityId": activity_id, "activityType": {"typeKey": "running"}}


def a_splits(activity_id: int, laps: list[dict]) -> GarminSplits:
    return {"activityId": activity_id, "lapDTOs": laps, "eventDTOs": []}


def stored_runs(conn) -> list[tuple]:
    return conn.execute("SELECT activity_id, summary, splits FROM garmin_runs ORDER BY activity_id").fetchall()


class TestRawStore:
    def test_stored_garmin_ids_is_empty_for_an_empty_table(self, store):
        assert store.stored_garmin_ids() == set()

    def test_stored_garmin_ids_returns_the_ids_of_saved_runs(self, store):
        store.save_garmin_run(a_run(7), A_SPLITS)
        store.save_garmin_run(a_run(8), A_SPLITS)

        assert store.stored_garmin_ids() == {7, 8}

    def test_saves_summary_and_splits_as_json(self, store, conn):
        store.save_garmin_run(a_run(7), a_splits(7, [{"lapIndex": 1}]))

        assert stored_runs(conn) == [(7, a_run(7), a_splits(7, [{"lapIndex": 1}]))]

    def test_keeps_the_first_save_when_a_run_is_saved_twice(self, store, conn):
        store.save_garmin_run(a_run(7), a_splits(7, [{"lapIndex": 1}]))
        store.save_garmin_run(a_run(7), a_splits(7, [{"lapIndex": 2}]))

        assert stored_runs(conn) == [(7, a_run(7), a_splits(7, [{"lapIndex": 1}]))]
