from dataclasses import asdict, fields

import psycopg
from psycopg import sql

from sasoi.ingest.runs import Lap, Run

RUN_COLUMNS = [field.name for field in fields(Run)]
LAP_COLUMNS = ["activity_id", *(field.name for field in fields(Lap))]


class PostgresRunStore:
    def __init__(self, conn: psycopg.Connection):
        self._conn = conn

    def stored_garmin_ids(self) -> set[int]:
        return {row[0] for row in self._conn.execute("SELECT activity_id FROM garmin_runs")}

    def save_garmin_run(self, run: Run, laps: list[Lap]) -> None:
        with self._conn.transaction():
            self._conn.execute(_insert("garmin_runs", RUN_COLUMNS), asdict(run))
            with self._conn.cursor() as cursor:
                cursor.executemany(
                    _insert("garmin_laps", LAP_COLUMNS),
                    [{"activity_id": run.activity_id, **asdict(lap)} for lap in laps],
                )


def _insert(table: str, columns: list[str]) -> sql.Composed:
    return sql.SQL("INSERT INTO {} ({}) VALUES ({}) ON CONFLICT DO NOTHING").format(
        sql.Identifier(table),
        sql.SQL(", ").join(map(sql.Identifier, columns)),
        sql.SQL(", ").join(map(sql.Placeholder, columns)),
    )
