## Project

Sasoi: personal agent analysing running (Garmin Connect) and strength (Hevy) training. Read `Plan.md` for roadmap, scope and decided constraints.

## Commands

```sh
uv sync                                   # install
uv run sasoi                              # chat REPL (needs ANTHROPIC_API_KEY in .env)
docker compose up -d                      # local services (Postgres)
uv run sasoi-sync                         # apply migrations, pull latest Garmin runs into Postgres
uv run pytest                             # all tests
uv run pytest tests/test_cli.py::TestRepl::test_skips_empty_prompts   # single test
scripts/trace.sh [--full] [trace.jsonl]   # follow latest trace; --full skips truncating tool results
```

Env: `.env` loaded by `cli.main`; `SASOI_MODEL` overrides the default model.

## Architecture

- `cli.py`: `main` wires env, `httpx.Client` and an `Agent` into `repl`. `repl` only does terminal I/O; takes injectable `read`/`write` for tests.
- `agent.py`: `Agent.ask` runs one turn: history, Claude call, tool-use loop.
- `claude_client.py`: raw-HTTP call to the Messages API (no Anthropic SDK, by design). Errors raised as `ClaudeApiError`.
- `conversation.py`: in-memory message history; `messages` returns a copy.
- `pricing.py`: per-model `Price` turning a turn's `Usage` into dollars; unknown models show tokens only.
- `retrying.py`: `RetryingClient` wraps the Claude client, retrying connection errors, 429 and 5xx with backoff.
- `sync_cli.py`: `main` applies yoyo migrations (`migrations/*.sql`), then syncs Garmin. Garmin login may prompt for email, password and MFA.
- `ingest/`: `sync.py` stores only runs not yet stored (latest `SASOI_GARMIN_LIMIT`), so backfill and incremental sync are the same code. Raw payloads go into `jsonb` via `RawStore`.
- `tracing.py`: `TracedClient` and `TracedToolbox` wrap the Claude client and toolbox, writing every call to `traces/<timestamp>.jsonl` via `Tracer`.

## Testing conventions

- HTTP mocked with `httpx.MockTransport`, never real network.
- `RawStore` tests run against the `postgres-test` compose service via `TEST_DATABASE_URL` (loaded from `.env` by `tests/conftest.py`); skipped when unset.
- CLI tested via fake agent and injected `read`/`write` (no monkeypatching `input`).

## Docs

- [Testing: Relevant test data lives inside the test](docs/testing/relevant-test-data-lives-inside-the-test.md).
- [Testing: Assertions state exactly what the test claims](docs/testing/assertions-state-exactly-what-the-test-claims.md).
- [Config: No defaults in code, only in .env.example](docs/config/no-defaults-in-code-only-in-env-example.md).
