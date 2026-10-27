import pytest

from sasoi.app import Config, load_config
from sasoi.settings import SettingError

AN_API_KEY = "an api key"
A_MODEL = "a model"
A_READER_DATABASE_URL = "postgresql://reader@localhost/sasoi"


class TestLoadConfig:
    def test_rejects_with_message_when_api_key_missing(self):
        with pytest.raises(SettingError) as raised:
            load_config({"SASOI_MODEL": A_MODEL, "READER_DATABASE_URL": A_READER_DATABASE_URL})

        assert str(raised.value) == "ANTHROPIC_API_KEY is not set"

    def test_rejects_with_message_when_model_missing(self):
        with pytest.raises(SettingError) as raised:
            load_config({"ANTHROPIC_API_KEY": AN_API_KEY, "READER_DATABASE_URL": A_READER_DATABASE_URL})

        assert str(raised.value) == "SASOI_MODEL is not set"

    def test_rejects_with_message_when_reader_database_url_missing(self):
        with pytest.raises(SettingError) as raised:
            load_config({"ANTHROPIC_API_KEY": AN_API_KEY, "SASOI_MODEL": A_MODEL})

        assert str(raised.value) == "READER_DATABASE_URL is not set"

    def test_rejects_with_message_when_athlete_profile_missing(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)

        with pytest.raises(SettingError) as raised:
            load_config(
                {"ANTHROPIC_API_KEY": AN_API_KEY, "SASOI_MODEL": A_MODEL, "READER_DATABASE_URL": A_READER_DATABASE_URL}
            )

        assert str(raised.value) == "Missing data/athlete_profile.md"

    def test_reads_api_key_model_reader_database_url_and_athlete_profile(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "data").mkdir()
        (tmp_path / "data/athlete_profile.md").write_text("Up to 4 sessions a week.")

        config = load_config(
            {"ANTHROPIC_API_KEY": "key", "SASOI_MODEL": "claude-test", "READER_DATABASE_URL": "postgresql://db/sasoi"}
        )

        assert config == Config("key", "claude-test", "postgresql://db/sasoi", "Up to 4 sessions a week.")
