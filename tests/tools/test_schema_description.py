import psycopg
import pytest

from sasoi.tools.schema_description import schema_description


@pytest.fixture
def conn(database_url):
    with psycopg.connect(database_url) as conn:
        yield conn
        conn.rollback()


def tables(description: str) -> dict[str, str]:
    return {section.split(":", 1)[0]: section for section in description.split("\n\n")}


class TestSchemaDescription:
    def test_describes_a_commented_table_and_its_columns(self, conn):
        conn.execute("CREATE TABLE shoes (id integer PRIMARY KEY, worn_km double precision, brand text)")
        conn.execute("COMMENT ON TABLE shoes IS 'Running shoes.'")
        conn.execute("COMMENT ON COLUMN shoes.worn_km IS 'Distance run in them, in km.'")

        assert tables(schema_description(conn))["shoes"] == (
            "shoes: Running shoes.\n"
            "- id (integer)\n"
            "- worn_km (double precision, nullable): Distance run in them, in km.\n"
            "- brand (text, nullable)"
        )

    def test_leaves_out_tables_without_a_comment(self, conn):
        conn.execute("CREATE TABLE scratch (id integer)")

        assert "scratch" not in tables(schema_description(conn))
