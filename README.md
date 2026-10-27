# Sasoi

Sasoi (Basque for being in good shape) is a personal agent that analyses my running and strength training. It sends feedback after every session and answers questions about my training.

## Setup

```sh
cp .env.example .env   # then set ANTHROPIC_API_KEY
uv sync
docker compose up -d
```

## Usage

```sh
uv run sasoi
```

Type a message at the `>` prompt. Ctrl-D exits.

`SASOI_MODEL` in `.env` picks the Claude model.

## Sync

```sh
uv run sasoi-sync
```

Pulls the latest Garmin runs and their laps into Postgres. Only new runs are fetched, so the first sync fills a fresh database and later ones pick up new sessions.

Set `SASOI_GARMIN_LIMIT` in `.env` to change how many recent Garmin runs are kept. Progress is logged to stdout at `SASOI_LOG_LEVEL`; other libraries only log warnings. The first Garmin login asks for email, password and MFA code; the token is saved in `~/.garminconnect` and reused.

## Evals

```sh
uv run sasoi-eval
uv run sasoi-eval --repeat 3
```

Asks every question in `evals/runs.toml` and grades the agent's SQL results against each case's ground-truth query. Traces go to `traces/evals/<timestamp>/`. Answers vary between runs, so use `--repeat` to run every case several times and see a pass rate per case, e.g. before and after a change. Cases run in parallel; `--workers` sets how many at once (default 8).

## Tests

```sh
uv run pytest
```

Database tests run against the `postgres-test` compose service (in-memory, port 5433) via `TEST_DATABASE_URL`; they fail when it is not set.

## Lint, format and type check

```sh
uv run ruff check --fix .
uv run ruff format .
uv run pyright
```

## Architecture

See [docs/architecture.excalidraw](docs/architecture.excalidraw) (open with [Excalidraw](https://excalidraw.com)).
