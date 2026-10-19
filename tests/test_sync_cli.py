import pytest

from sasoi.cli import RED, RESET
from sasoi.sync_cli import SyncConfig, load_config

A_DATABASE_URL = "postgresql://localhost/sasoi"
A_GARMIN_LIMIT = "100"


class TestLoadConfig:
    def test_reads_database_url_and_garmin_limit(self):
        config = load_config({"DATABASE_URL": "postgresql://db/sasoi", "SASOI_GARMIN_LIMIT": "20"})

        assert config == SyncConfig("postgresql://db/sasoi", 20)

    def test_exits_when_database_url_is_not_set(self):
        with pytest.raises(SystemExit) as raised:
            load_config({"SASOI_GARMIN_LIMIT": A_GARMIN_LIMIT})

        assert raised.value.code == f"{RED}Error: DATABASE_URL is not set{RESET}"

    def test_exits_when_garmin_limit_is_not_set(self):
        with pytest.raises(SystemExit) as raised:
            load_config({"DATABASE_URL": A_DATABASE_URL})

        assert raised.value.code == f"{RED}Error: SASOI_GARMIN_LIMIT is not set{RESET}"

    def test_accepts_a_garmin_limit_of_1000(self):
        config = load_config({"DATABASE_URL": A_DATABASE_URL, "SASOI_GARMIN_LIMIT": "1000"})

        assert config.garmin_limit == 1000

    def test_exits_when_garmin_limit_exceeds_1000(self):
        with pytest.raises(SystemExit) as raised:
            load_config({"DATABASE_URL": A_DATABASE_URL, "SASOI_GARMIN_LIMIT": "1001"})

        assert raised.value.code == f"{RED}Error: SASOI_GARMIN_LIMIT cannot exceed 1000{RESET}"
