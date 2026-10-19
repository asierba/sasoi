# Config: No defaults in code, only in .env.example

## Convention

The application reads every setting as required and fails at startup when one is missing. Suggested values live only in `.env.example`.

## Benefits

- One source of truth: the value in use is always visible in `.env`.
- A missing setting fails loudly instead of running with a value nobody chose.
- No hidden fallback buried in code to find when behaviour surprises.

## Examples

### Good: required in code, suggested value in the example env

```python
garmin_limit = int(os.environ["SASOI_GARMIN_LIMIT"])
```

```sh
SASOI_GARMIN_LIMIT=100
```

### Bad: silent default injected in code

```python
DEFAULT_GARMIN_LIMIT = 100

garmin_limit = int(os.environ.get("SASOI_GARMIN_LIMIT", DEFAULT_GARMIN_LIMIT))
```

## Real world examples

- [`sync_cli.main`](../../src/sasoi/sync_cli.py).
- [`.env.example`](../../.env.example).
