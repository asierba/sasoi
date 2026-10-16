from dataclasses import dataclass

from sasoi.claude_client import Usage

TOKENS_PER_PRICE_UNIT = 1_000_000


@dataclass(frozen=True)
class Price:
    input_per_mtok: float
    output_per_mtok: float

    def cost(self, usage: Usage) -> float:
        return (
            usage.input_tokens * self.input_per_mtok + usage.output_tokens * self.output_per_mtok
        ) / TOKENS_PER_PRICE_UNIT


PRICES = {
    "claude-haiku-5-5": Price(0.10, 0.50),
    "claude-sonnet-5-5": Price(2.00, 10.00),
    "claude-opus-5-5": Price(4.00, 20.00),
}
