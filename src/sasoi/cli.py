import os
import sys

import httpx

from sasoi.claude_client import ClaudeClient

DEFAULT_MODEL = "claude-haiku-5-5"


def main() -> None:
    prompt = " ".join(sys.argv[1:])
    api_key = os.environ["ANTHROPIC_API_KEY"]
    model = os.environ.get("SASOI_MODEL", DEFAULT_MODEL)
    with httpx.Client(timeout=60) as http:
        print(ClaudeClient(api_key, model, http).send(prompt))
