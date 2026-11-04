import pytest

from sasoi.settings import SettingError
from sasoi.sync_cli import SyncConfig, load_config

A_VALID_ENV = {
    "DATABASE_URL": "postgresql://localhost/sasoi",
    "SASOI_GARMIN_LIMIT": "100",
    "SASOI_LOG_LEVEL": "INFO",
}


def an_env_without(name: str) -> dict[str, str]:
    return {key: value for key, value in A_VALID_ENV.items() if key != name}


class TestLoadConfig:
    def test_reads_database_url_garmin_limit_and_log_level(self):
        config = load_config(
            {"DATABASE_URL": "postgresql://db/sasoi", "SASOI_GARMIN_LIMIT": "20", "SASOI_LOG_LEVEL": "DEBUG"}
        )

        assert config == SyncConfig("postgresql://db/sasoi", 20, "DEBUG")

    @pytest.mark.parametrize("name", ["DATABASE_URL", "SASOI_GARMIN_LIMIT", "SASOI_LOG_LEVEL"])
    def test_rejects_when_a_setting_is_not_set(self, name):
        with pytest.raises(SettingError) as raised:
            load_config(an_env_without(name))

        assert str(raised.value) == f"{name} is not set"

    def test_accepts_a_garmin_limit_of_1000(self):
        config = load_config({**A_VALID_ENV, "SASOI_GARMIN_LIMIT": "1000"})

        assert config.garmin_limit == 1000

    def test_rejects_a_garmin_limit_above_1000(self):
        with pytest.raises(SettingError) as raised:
            load_config({**A_VALID_ENV, "SASOI_GARMIN_LIMIT": "1001"})

        assert str(raised.value) == "SASOI_GARMIN_LIMIT 1001 must be between 1 and 1000"

    def test_rejects_a_garmin_limit_of_0(self):
        with pytest.raises(SettingError) as raised:
            load_config({**A_VALID_ENV, "SASOI_GARMIN_LIMIT": "0"})

        assert str(raised.value) == "SASOI_GARMIN_LIMIT 0 must be between 1 and 1000"

    def test_rejects_when_garmin_limit_is_not_a_whole_number(self):
        with pytest.raises(SettingError) as raised:
            load_config({**A_VALID_ENV, "SASOI_GARMIN_LIMIT": "ten"})

        assert str(raised.value) == "SASOI_GARMIN_LIMIT ten is not a whole number"

    def test_rejects_when_log_level_is_not_a_logging_level(self):
        with pytest.raises(SettingError) as raised:
            load_config({**A_VALID_ENV, "SASOI_LOG_LEVEL": "LOUD"})

        assert str(raised.value) == "SASOI_LOG_LEVEL LOUD is not a logging level"
