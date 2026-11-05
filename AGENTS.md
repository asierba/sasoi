## Project

Sasoi: personal agent analysing running (Garmin Connect) and strength (Hevy) training. Read `Plan.md` for roadmap, scope and decided constraints.

## Commands

```sh
uv sync                                   # install
uv run pre-commit install                 # run ruff, pyright, pytest and sasoi-eval before each commit
uv run sasoi                              # chat REPL (needs ANTHROPIC_API_KEY in .env)
docker compose up -d                      # local services (Postgres)
uv run sasoi-sync                         # apply migrations, pull latest Garmin runs and Hevy workouts into Postgres
uv run sasoi-eval                         # ask every question in evals/runs.toml, grade the agent's SQL results
uv run sasoi-eval --repeat 3              # run every case 3 times, show a pass rate per case; --workers sets parallel cases
uv run pytest                             # all tests
uv run pytest tests/test_cli.py::TestRepl::test_skips_empty_prompts   # single test
uv run ruff check --fix . && uv run ruff format .   # lint and format (config in pyproject.toml)
uv run pyright                            # type check src and tests
scripts/trace.sh [--full] [trace.jsonl]   # follow latest trace; --full skips truncating tool results
```

Env: `.env` loaded by `cli.main`; `SASOI_MODEL` picks the chat model and `SASOI_EVAL_MODEL` the eval model (both required, no default in code).

## Architecture

@docs/architecture.md

## Testing conventions

- HTTP mocked with `httpx.MockTransport`, never real network.
- Database tests run against the `postgres-test` compose service via `TEST_DATABASE_URL` (loaded from `.env` by `tests/conftest.py`); they fail when it is unset.
- CLI tested via fake agent and injected `read`/`write` (no monkeypatching `input`).
