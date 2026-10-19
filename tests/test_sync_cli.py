import pytest

from sasoi.cli import RED, RESET
from sasoi.sync_cli import SyncConfig, load_config

A_DATABASE_URL = "postgresql://localhost/sasoi"
A_GARMIN_LIMIT = "100"
A_LOG_LEVEL = "INFO"


class TestLoadConfig:
    def test_reads_database_url_garmin_limit_and_log_level(self):
        config = load_config(
            {"DATABASE_URL": "postgresql://db/sasoi", "SASOI_GARMIN_LIMIT": "20", "SASOI_LOG_LEVEL": "DEBUG"}
        )

        assert config == SyncConfig("postgresql://db/sasoi", 20, "DEBUG")

    def test_exits_when_database_url_is_not_set(self):
        with pytest.raises(SystemExit) as raised:
            load_config({"SASOI_GARMIN_LIMIT": A_GARMIN_LIMIT, "SASOI_LOG_LEVEL": A_LOG_LEVEL})

        assert raised.value.code == f"{RED}Error: DATABASE_URL is not set{RESET}"

    def test_exits_when_garmin_limit_is_not_set(self):
        with pytest.raises(SystemExit) as raised:
            load_config({"DATABASE_URL": A_DATABASE_URL, "SASOI_LOG_LEVEL": A_LOG_LEVEL})

        assert raised.value.code == f"{RED}Error: SASOI_GARMIN_LIMIT is not set{RESET}"

    def test_accepts_a_garmin_limit_of_1000(self):
        config = load_config({"DATABASE_URL": A_DATABASE_URL, "SASOI_GARMIN_LIMIT": "1000", "SASOI_LOG_LEVEL": A_LOG_LEVEL})

        assert config.garmin_limit == 1000

    def test_exits_when_garmin_limit_exceeds_1000(self):
        with pytest.raises(SystemExit) as raised:
            load_config({"DATABASE_URL": A_DATABASE_URL, "SASOI_GARMIN_LIMIT": "1001", "SASOI_LOG_LEVEL": A_LOG_LEVEL})

        assert raised.value.code == f"{RED}Error: SASOI_GARMIN_LIMIT cannot exceed 1000{RESET}"

    def test_exits_when_log_level_is_not_set(self):
        with pytest.raises(SystemExit) as raised:
            load_config({"DATABASE_URL": A_DATABASE_URL, "SASOI_GARMIN_LIMIT": A_GARMIN_LIMIT})

        assert raised.value.code == f"{RED}Error: SASOI_LOG_LEVEL is not set{RESET}"

    def test_exits_when_log_level_is_not_a_logging_level(self):
        with pytest.raises(SystemExit) as raised:
            load_config({"DATABASE_URL": A_DATABASE_URL, "SASOI_GARMIN_LIMIT": A_GARMIN_LIMIT, "SASOI_LOG_LEVEL": "LOUD"})

        assert raised.value.code == f"{RED}Error: SASOI_LOG_LEVEL LOUD is not a logging level{RESET}"
