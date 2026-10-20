import os

import pytest
from dotenv import load_dotenv

from sasoi.settings import required

load_dotenv(".env")


@pytest.fixture
def database_url() -> str:
    return required(os.environ, "TEST_DATABASE_URL")
