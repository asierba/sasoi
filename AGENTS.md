## Project

Sasoi: personal agent analysing running (Garmin via Intervals.icu) and strength (Hevy) training. Read `Plan.md` for roadmap, scope and decided constraints.

## Commands

```sh
uv sync                                   # install
uv run sasoi                              # chat REPL (needs ANTHROPIC_API_KEY in .env)
uv run pytest                             # all tests
uv run pytest tests/test_cli.py::test_repl_skips_empty_prompts   # single test
```

Env: `.env` loaded by `cli.main`; `SASOI_MODEL` overrides the default model.

## Architecture

- `cli.py`: `main` wires env, `httpx.Client`, `Conversation`, `ClaudeClient` into `repl`. `repl` takes injectable `read`/`write` for tests.
- `claude_client.py`: raw-HTTP call to the Messages API (no Anthropic SDK, by design). Errors raised as `ClaudeApiError`.
- `conversation.py`: in-memory message history; `messages` returns a copy.

## Testing conventions

- HTTP mocked with `httpx.MockTransport`, never real network.
- CLI tested via fake client and injected `read`/`write` (no monkeypatching `input`).

## Docs

- [Testing: Relevant test data lives inside the test](docs/testing/relevant-test-data-lives-inside-the-test.md).
