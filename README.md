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

Applies database migrations, then stores the latest Garmin runs (with laps) in Postgres as raw JSON. Only runs not already stored are fetched, so the first run fills a fresh database and later runs pick up new sessions.

Set `SASOI_GARMIN_LIMIT` in `.env` to change how many recent Garmin runs are kept. Progress is logged to stdout at `SASOI_LOG_LEVEL`; other libraries only log warnings. The first Garmin login asks for email, password and MFA code; the token is saved in `~/.garminconnect` and reused.

## Tests

```sh
uv run pytest
```

Database tests run against the `postgres-test` compose service (in-memory, port 5433) via `TEST_DATABASE_URL`; they are skipped when it is not set.

## Architecture

See [docs/architecture.excalidraw](docs/architecture.excalidraw) (open with [Excalidraw](https://excalidraw.com)).
