import csv
import io

import psycopg

from sasoi.tools.tool import Tool, ToolError

MAX_ROWS = 200
TRUNCATED_FOOTER = f"(truncated: more than {MAX_ROWS} rows; showing the first {MAX_ROWS})"


def run_sql(conn: psycopg.Connection, schema: str) -> Tool:
    conn.read_only = True

    def run(tool_input: dict) -> str:
        try:
            with conn.transaction(), conn.cursor() as cursor:
                cursor.execute(tool_input["query"])
                if cursor.description is None:
                    raise ToolError("query returned no rows; only SELECT queries are supported")
                header = [column.name for column in cursor.description]
                rows = cursor.fetchmany(MAX_ROWS + 1)
        except psycopg.Error as error:
            raise ToolError(str(error).strip()) from error
        return _csv(header, rows[:MAX_ROWS]) + _footer(len(rows))

    return Tool(
        name="run_sql",
        description=(
            "Run a read-only PostgreSQL SELECT query on the training database and get the result as CSV. "
            f"Returns at most {MAX_ROWS} rows, so aggregate in SQL rather than fetching raw rows. "
            "When grouping by period, include periods with no runs as 0 (e.g. with generate_series).\n\n"
            f"Schema:\n\n{schema}"
        ),
        input_schema={
            "type": "object",
            "properties": {"query": {"type": "string", "description": "A single PostgreSQL SELECT query"}},
            "required": ["query"],
        },
        run=run,
    )


def _csv(header: list[str], rows: list[tuple]) -> str:
    output = io.StringIO()
    writer = csv.writer(output, lineterminator="\n")
    writer.writerow(header)
    writer.writerows(rows)
    return output.getvalue()


def _footer(row_count: int) -> str:
    if row_count > MAX_ROWS:
        return TRUNCATED_FOOTER
    return f"({row_count} rows)"
