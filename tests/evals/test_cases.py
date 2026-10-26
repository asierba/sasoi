from pathlib import Path

import pytest

from sasoi.evals.cases import Case, load_cases
from sasoi.tools.run_sql import run_sql

REPOSITORY_CASES = load_cases(Path("evals/runs.toml"))


class TestLoadCases:
    def test_reads_each_case_with_its_multiline_sql(self, tmp_path):
        path = tmp_path / "cases.toml"
        path.write_text(
            """
[[case]]
id = "km-this-month"
question = "How many km have I run this month?"
sql = '''
SELECT sum(distance_m) / 1000 AS km
FROM garmin_runs
'''
"""
        )

        assert load_cases(path) == [
            Case(
                "km-this-month",
                "How many km have I run this month?",
                "SELECT sum(distance_m) / 1000 AS km\nFROM garmin_runs\n",
            )
        ]

    def test_raises_key_error_when_id_is_missing(self, tmp_path):
        path = tmp_path / "cases.toml"
        path.write_text('[[case]]\nquestion = "a question"\nsql = "SELECT 1"\n')

        with pytest.raises(KeyError) as raised:
            load_cases(path)

        assert repr(raised.value) == "KeyError('id')"

    def test_raises_key_error_when_question_is_missing(self, tmp_path):
        path = tmp_path / "cases.toml"
        path.write_text('[[case]]\nid = "a-case"\nsql = "SELECT 1"\n')

        with pytest.raises(KeyError) as raised:
            load_cases(path)

        assert repr(raised.value) == "KeyError('question')"

    def test_raises_key_error_when_sql_is_missing(self, tmp_path):
        path = tmp_path / "cases.toml"
        path.write_text('[[case]]\nid = "a-case"\nquestion = "a question"\n')

        with pytest.raises(KeyError) as raised:
            load_cases(path)

        assert repr(raised.value) == "KeyError('sql')"


class TestRepositoryCases:
    def test_ids_are_unique(self):
        ids = [case.id for case in REPOSITORY_CASES]

        assert len(ids) == len(set(ids))

    @pytest.mark.parametrize("case", REPOSITORY_CASES, ids=lambda case: case.id)
    def test_ground_truth_runs_as_the_reader(self, case, reader):
        run_sql(reader, "").run({"query": case.sql})
