import psycopg
from psycopg.types.json import Jsonb

from sasoi.ingest.garmin_types import GarminActivity, GarminSplits


class PostgresRunStore:
    def __init__(self, conn: psycopg.Connection):
        self._conn = conn

    def stored_garmin_ids(self) -> set[int]:
        return {row[0] for row in self._conn.execute("SELECT activity_id FROM garmin_runs")}

    def save_garmin_run(self, summary: GarminActivity, splits: GarminSplits) -> None:
        with self._conn.transaction():
            self._conn.execute(
                "INSERT INTO garmin_runs (activity_id, summary, splits) VALUES (%s, %s, %s) ON CONFLICT DO NOTHING",
                (summary["activityId"], Jsonb(summary), Jsonb(splits)),
            )
