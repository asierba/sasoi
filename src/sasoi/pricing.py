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


def usage_summary(model: str, usage: Usage, price: Price | None) -> str:
    tokens = f"{usage.input_tokens:,} in · {usage.output_tokens:,} out"
    cost = f" · ${price.cost(usage):.4f}" if price else ""
    return f"{model} · {tokens}{cost}"
