import psycopg
import pytest
from psycopg.conninfo import make_conninfo

from sasoi.sync_cli import migrate


@pytest.fixture
def reader(database_url):
    migrate(database_url)
    reader_url = make_conninfo(database_url, user="sasoi_reader", password="sasoi_reader")
    with psycopg.connect(reader_url, autocommit=True) as conn:
        yield conn
