import psycopg
import pytest
from psycopg.conninfo import make_conninfo

from sasoi.sync_cli import migrate
from sasoi.tools.run_sql import MAX_ROWS, run_sql
from sasoi.tools.tool import ToolError

A_SCHEMA = "garmin_runs: One row per run."


@pytest.fixture
def conn(database_url):
    migrate(database_url)
    reader_url = make_conninfo(database_url, user="sasoi_reader", password="sasoi_reader")
    with psycopg.connect(reader_url, autocommit=True) as conn:
        yield conn


class TestRunSql:
    def test_returns_rows_as_csv_with_a_row_count(self, conn):
        result = run_sql(conn, A_SCHEMA).run({"query": "SELECT 1 AS lap, 'easy, slow' AS note UNION SELECT 2, NULL"})

        assert result == 'lap,note\n1,"easy, slow"\n2,\n(2 rows)'

    def test_truncates_results_above_the_row_cap(self, conn):
        result = run_sql(conn, A_SCHEMA).run({"query": f"SELECT n FROM generate_series(1, {MAX_ROWS + 1}) AS n"})

        assert result.splitlines() == [
            "n",
            *(str(n) for n in range(1, MAX_ROWS + 1)),
            f"(truncated: more than {MAX_ROWS} rows; showing the first {MAX_ROWS})",
        ]

    def test_raises_tool_error_for_invalid_sql(self, conn):
        with pytest.raises(ToolError, match='column "pace" does not exist'):
            run_sql(conn, A_SCHEMA).run({"query": "SELECT pace FROM garmin_runs"})

    def test_rejects_writes(self, conn):
        with pytest.raises(ToolError, match="read-only transaction"):
            run_sql(conn, A_SCHEMA).run({"query": "DELETE FROM garmin_runs"})

    def test_rejects_writes_after_escaping_the_transaction(self, conn):
        with pytest.raises(ToolError, match="permission denied for table garmin_runs"):
            run_sql(conn, A_SCHEMA).run({"query": "COMMIT; DELETE FROM garmin_runs"})

    def test_hides_tables_not_granted_to_the_reader(self, conn):
        with pytest.raises(ToolError, match="permission denied for table _yoyo_migration"):
            run_sql(conn, A_SCHEMA).run({"query": "SELECT * FROM _yoyo_migration"})

    def test_keeps_working_after_a_failed_query(self, conn):
        tool = run_sql(conn, A_SCHEMA)
        with pytest.raises(ToolError):
            tool.run({"query": "SELECT pace FROM garmin_runs"})

        assert tool.run({"query": "SELECT 1 AS n"}) == "n\n1\n(1 rows)"

    def test_describes_the_schema(self, conn):
        assert run_sql(conn, "garmin_runs: One row per run.").definition["description"].endswith(
            "Schema:\n\ngarmin_runs: One row per run."
        )
