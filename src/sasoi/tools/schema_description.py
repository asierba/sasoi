import psycopg

TABLES_QUERY = """
SELECT c.relname, obj_description(c.oid, 'pg_class')
FROM pg_class c
JOIN pg_namespace n ON n.oid = c.relnamespace
WHERE n.nspname = 'public' AND c.relkind = 'r' AND obj_description(c.oid, 'pg_class') IS NOT NULL
ORDER BY c.relname
"""

COLUMNS_QUERY = """
SELECT a.attname, format_type(a.atttypid, a.atttypmod), a.attnotnull, col_description(a.attrelid, a.attnum)
FROM pg_attribute a
WHERE a.attrelid = %s::regclass AND a.attnum > 0 AND NOT a.attisdropped
ORDER BY a.attnum
"""


def schema_description(conn: psycopg.Connection) -> str:
    return "\n\n".join(_table(conn, name, comment) for name, comment in conn.execute(TABLES_QUERY))


def _table(conn: psycopg.Connection, name: str, comment: str) -> str:
    columns = [_column(*row) for row in conn.execute(COLUMNS_QUERY, (name,))]
    return "\n".join([f"{name}: {comment}", *columns])


def _column(name: str, type_: str, not_null: bool, comment: str | None) -> str:
    nullable = "" if not_null else ", nullable"
    return f"- {name} ({type_}{nullable}): {comment or ''}".rstrip(": ")
