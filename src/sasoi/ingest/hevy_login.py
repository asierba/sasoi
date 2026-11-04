import json
from collections.abc import Callable
from getpass import getpass
from pathlib import Path

import httpx

from sasoi.ingest.hevy_source import HevySource, HevyTokens, renew

TOKENSTORE = Path("data/hevy/tokens.json")


def login(http: httpx.Client, tokenstore: Path = TOKENSTORE, prompt: Callable[[str], str] = getpass) -> HevySource:
    tokens = renew(http, _stored_tokens(tokenstore, prompt))
    _save(tokenstore, tokens)
    return HevySource(http, tokens.access_token)


def _stored_tokens(tokenstore: Path, prompt: Callable[[str], str]) -> HevyTokens:
    if tokenstore.exists():
        stored = json.loads(tokenstore.read_text())
        return HevyTokens(stored["access_token"], stored["refresh_token"])
    return HevyTokens(prompt("Hevy access_token: ").strip(), prompt("Hevy refresh_token: ").strip())


def _save(tokenstore: Path, tokens: HevyTokens) -> None:
    tokenstore.parent.mkdir(parents=True, exist_ok=True)
    tokenstore.write_text(json.dumps({"access_token": tokens.access_token, "refresh_token": tokens.refresh_token}))
    tokenstore.chmod(0o600)
