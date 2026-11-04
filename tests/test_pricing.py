from sasoi.claude_client import Usage
from sasoi.pricing import Price, usage_summary


class TestUsageSummary:
    def test_shows_model_tokens_and_dollars(self):
        assert (
            usage_summary("claude-test", Usage(1_500_000, 100_000), Price(1.00, 5.00))
            == "claude-test · 1,500,000 in · 100,000 out · $2.0000"
        )

    def test_shows_only_tokens_when_the_model_has_no_price(self):
        assert usage_summary("claude-test", Usage(1_500, 100), None) == "claude-test · 1,500 in · 100 out"
