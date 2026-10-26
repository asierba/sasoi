from sasoi.evals.grading import Grade, QueryResult

A_CASE_ID = "a-case"


def a_result(*rows: list[str]) -> QueryResult:
    return QueryResult(list(rows), truncated=False)


def a_capped_result(*rows: list[str]) -> QueryResult:
    return QueryResult(list(rows), truncated=True)


class TestFromCsv:
    def test_reads_rows_without_header_or_footer(self):
        assert QueryResult.from_csv('month,km\n2026-09,34.8\n2026-10,"30,4"\n(2 rows)') == QueryResult(
            [["2026-09", "34.8"], ["2026-10", "30,4"]], truncated=False
        )

    def test_flags_a_truncated_result(self):
        result = QueryResult.from_csv("n\n1\n(truncated: more than 1 rows; showing the first 1)")

        assert result == QueryResult([["1"]], truncated=True)


class TestContains:
    def test_matches_rows_ignoring_column_order_and_extra_columns(self):
        assert a_result(["158", "2026-10-02", "5.36"]).contains(a_result(["2026-10-02", "5.36"]))

    def test_matches_numbers_rounded_by_the_agent(self):
        assert a_result(["30"]).contains(a_result(["30.427739"]))

    def test_matches_numbers_in_another_unit(self):
        assert a_result(["5010.5", "1542"]).contains(a_result(["5.0105", "25.7"]))

    def test_matches_a_date_against_a_timestamp(self):
        assert a_result(["2026-10-01 00:00:00"]).contains(a_result(["2026-10"]))

    def test_rejects_a_different_number(self):
        assert not a_result(["30.4"]).contains(a_result(["34.8"]))

    def test_rejects_when_an_expected_row_is_missing(self):
        assert not a_result(["2026-09", "34.8"]).contains(a_result(["2026-09", "34.8"], ["2026-10", "30.4"]))

    def test_rejects_when_values_are_split_across_rows(self):
        assert not a_result(["2026-09", "30.4"], ["2026-10", "34.8"]).contains(a_result(["2026-09", "34.8"]))


class TestCompare:
    def test_passes_when_a_result_contains_the_ground_truth(self):
        grade = Grade.compare(A_CASE_ID, a_result(["30.4"]), [a_result(["1"]), a_result(["30.4"])])

        assert grade == Grade(A_CASE_ID, ())

    def test_fails_when_no_result_contains_the_ground_truth(self):
        grade = Grade.compare(A_CASE_ID, a_result(["30.4"]), [a_result(["34.8"])])

        assert grade == Grade(A_CASE_ID, ("no run_sql result contains the ground truth",))

    def test_fails_when_run_sql_never_returned_a_result(self):
        grade = Grade.compare(A_CASE_ID, a_result(["30.4"]), [])

        assert grade == Grade(A_CASE_ID, ("run_sql never returned a result",))

    def test_fails_when_a_result_hit_the_row_cap(self):
        grade = Grade.compare(A_CASE_ID, a_result(["30.4"]), [a_capped_result(["30.4"])])

        assert grade == Grade(A_CASE_ID, ("a run_sql result hit the row cap",))
