## Project

Sasoi: personal agent analysing running (Garmin Connect) and strength (Hevy) training. Read `Plan.md` for roadmap, scope and decided constraints.

## Commands

```sh
uv sync                                   # install
uv run pre-commit install                 # run ruff, pyright, pytest and sasoi-eval before each commit
uv run sasoi                              # chat REPL (needs ANTHROPIC_API_KEY in .env)
docker compose up -d                      # local services (Postgres)
uv run sasoi-sync                         # apply migrations, pull latest Garmin runs into Postgres
uv run sasoi-eval                         # ask every question in evals/runs.toml, grade the agent's SQL results
uv run sasoi-eval --repeat 3              # run every case 3 times, show a pass rate per case; --workers sets parallel cases
uv run pytest                             # all tests
uv run pytest tests/test_cli.py::TestRepl::test_skips_empty_prompts   # single test
uv run ruff check --fix . && uv run ruff format .   # lint and format (config in pyproject.toml)
uv run pyright                            # type check src and tests
scripts/trace.sh [--full] [trace.jsonl]   # follow latest trace; --full skips truncating tool results
```

Env: `.env` loaded by `cli.main`; `SASOI_MODEL` picks the model (required, no default in code).

## Architecture

- `cli.py`: `main` wires env, `httpx.Client` and an `Agent` into `repl`. `repl` only does terminal I/O; takes injectable `read`/`write` for tests.
- `app.py`: `load_config` and `build_agent`, the wiring shared by the chat and eval CLIs.
- `agent.py`: `Agent.ask` runs one turn: history, Claude call, tool-use loop.
- `claude_client.py`: raw-HTTP call to the Messages API (no Anthropic SDK, by design). Errors raised as `ClaudeApiError`.
- `conversation.py`: in-memory message history; `messages` returns a copy.
- `pricing.py`: per-model `Price` turning a turn's `Usage` into dollars; unknown models show tokens only.
- `settings.py`: `required` env lookup and `SettingError`; config loaders raise it, each `main` formats it for its output.
- `retrying.py`: `RetryingClient` wraps the Claude client, retrying connection errors, 429 and 5xx with backoff.
- `sync_cli.py`: `main` applies yoyo migrations (`migrations/*.sql`), then syncs Garmin, logging to stdout at `SASOI_LOG_LEVEL` (third-party loggers capped at WARNING). Garmin login may prompt for email, password and MFA.
- `ingest/`: `sync.py` stores only runs not yet stored (latest `SASOI_GARMIN_LIMIT`), so backfill and incremental sync are the same code. `GarminSource` maps API payloads (`garmin_types.py`) to `Run`/`Lap` (`runs.py`) via `garmin_mapping.py`, an allow-list: fields not mapped are never stored. `PostgresRunStore` writes typed rows.
- `eval_cli.py` and `evals/`: runs each case in `evals/runs.toml` in parallel, each with a fresh agent, its own reader connection and its own trace in `traces/evals/<timestamp>/<repeat>/`. A case passes when one of the agent's `run_sql` results contains every row of the case's ground-truth query (columns in any order, numbers within rounding or a unit scale).
- `tracing.py`: `TracedClient` and `TracedToolbox` wrap the Claude client and toolbox, writing every call to `traces/<timestamp>.jsonl` via `Tracer`.

## Testing conventions

- HTTP mocked with `httpx.MockTransport`, never real network.
- Database tests run against the `postgres-test` compose service via `TEST_DATABASE_URL` (loaded from `.env` by `tests/conftest.py`); they fail when it is unset.
- CLI tested via fake agent and injected `read`/`write` (no monkeypatching `input`).
