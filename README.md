# Sasoi

Sasoi (Basque for being in good shape) is a personal agent that analyses my running and strength training. It sends feedback after every session and answers questions about my training.

## Setup

```sh
cp .env.example .env   # then set ANTHROPIC_API_KEY
uv sync
```

## Usage

```sh
uv run sasoi
```

Type a message at the `>` prompt. Ctrl-D exits.

Set `SASOI_MODEL` in `.env` to override the default model (`claude-haiku-5-5`).

## Tests

```sh
uv run pytest
```

## Architecture

See [docs/architecture.excalidraw](docs/architecture.excalidraw) (open with [Excalidraw](https://excalidraw.com)).
