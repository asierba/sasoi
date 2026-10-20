# Code: Small functions that do one thing

## Convention

Every function does one thing and stays a few lines long. When a function grows a second responsibility, extract it into a named function, so the caller reads as a sequence of steps.

## Benefits

- Code reads top-down like prose: names say what happens, bodies say how.
- Each step can be understood, changed and tested on its own.
- Names replace comments as the explanation of intent.

## Examples

### Good: the caller reads as a sequence of named steps

```python
def main() -> None:
    load_dotenv(".env")
    config = _config()
    with httpx.Client() as http, _trace_file() as trace_file:
        tracer = Tracer(trace_file)
        repl(_agent(config, http, tracer))


def _config() -> Config:
    try:
        return load_config(os.environ)
    except SettingError as error:
        raise SystemExit(f"Error: {error}") from error


def _trace_file() -> TextIO:
    TRACES_DIR.mkdir(exist_ok=True)
    return (TRACES_DIR / f"{datetime.now():%Y%m%d-%H%M%S}.jsonl").open("w")
```

### Bad: one function mixing error handling, file setup and wiring

```python
def main() -> None:
    load_dotenv(".env")
    try:
        config = load_config(os.environ)
    except SettingError as error:
        raise SystemExit(f"Error: {error}") from error
    TRACES_DIR.mkdir(exist_ok=True)
    trace_path = TRACES_DIR / f"{datetime.now():%Y%m%d-%H%M%S}.jsonl"
    with httpx.Client() as http, trace_path.open("w") as trace_file:
        tracer = Tracer(trace_file)
        client = RetryingClient(TracedClient(ClaudeClient(config.api_key, config.model, http), tracer))
        toolbox = TracedToolbox(Toolbox([current_time, geocode(OpenMeteoClient(http))]), tracer)
        repl(Agent(Conversation(), client, toolbox))
```

## Real world examples

- [`cli.main`](../../src/sasoi/cli.py).
- [`sync_cli.load_config`](../../src/sasoi/sync_cli.py).
- [`run_sql`](../../src/sasoi/tools/run_sql.py).
