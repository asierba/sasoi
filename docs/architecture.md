# Architecture

```mermaid
flowchart LR
    user_node(["User"])
    profile_file["data/athlete_profile.md"]
    trace_files["traces/*.jsonl"]
    anthropic_api(["Anthropic Messages API"])
    meteo_api(["Open-Meteo API"])
    garmin_api(["Garmin Connect API"])
    hevy_api(["Hevy private API"])
    hevy_tokens["data/hevy/tokens.json"]
    postgres_db[("Postgres")]

    subgraph entry_points["Entry points"]
        chat_cli["sasoi: cli.repl"]
        eval_cli["sasoi-eval: eval_cli, evals/"]
        sync_cli["sasoi-sync: sync_cli"]
    end

    subgraph agent_core["Agent core: app.build_agent"]
        agent_node["Agent"]
        conversation_node["Conversation"]
        commands_node["COMMANDS: saved prompts"]
        retrying_client["RetryingClient"]
        traced_client["TracedClient"]
        claude_client["ClaudeClient"]
        traced_toolbox["TracedToolbox"]
        toolbox_node["Toolbox"]
        web_tools["current_time, geocode, weather_history"]
        run_sql_tool["run_sql"]
        open_meteo_client["OpenMeteoClient"]
    end

    subgraph ingest_package["ingest/"]
        sync_garmin["sync_garmin"]
        garmin_source["GarminSource"]
        run_store["PostgresRunStore"]
        sync_hevy["sync_hevy"]
        hevy_source["HevySource"]
        workout_store["PostgresWorkoutStore"]
    end

    user_node --> chat_cli
    chat_cli -->|"ask"| agent_node
    eval_cli -->|"ask, fresh Agent per case"| agent_node
    eval_cli -->|"ground-truth SQL"| postgres_db
    profile_file -->|"system prompt"| agent_node
    commands_node --> agent_node
    agent_node --> conversation_node
    agent_node -->|"send"| retrying_client
    retrying_client --> traced_client
    traced_client --> claude_client
    claude_client -->|"HTTP"| anthropic_api
    agent_node -->|"definitions, run"| traced_toolbox
    traced_toolbox --> toolbox_node
    toolbox_node --> web_tools
    toolbox_node --> run_sql_tool
    web_tools --> open_meteo_client
    open_meteo_client -->|"HTTP"| meteo_api
    run_sql_tool -->|"SELECT as sasoi_reader"| postgres_db
    traced_client --> trace_files
    traced_toolbox --> trace_files

    sync_cli -->|"migrate with yoyo"| postgres_db
    sync_cli --> sync_garmin
    sync_garmin --> garmin_source
    garmin_source -->|"garminconnect"| garmin_api
    sync_garmin -->|"save new"| run_store
    run_store --> postgres_db
    sync_cli --> sync_hevy
    sync_hevy --> hevy_source
    hevy_source -->|"HTTP"| hevy_api
    hevy_source -->|"renew token pair"| hevy_tokens
    sync_hevy -->|"save new"| workout_store
    workout_store --> postgres_db
```

- The Claude client is raw HTTP, with no Anthropic SDK, by design. Errors are `ClaudeError`: `ClaudeConnectionError` or `ClaudeApiError`.
- `RetryingClient` retries only connection errors, 429 and 5xx, and honours `retry-after` up to `MAX_WAIT_SECONDS`.
- `repl` only does terminal I/O; tests inject `read`/`write`.
- Config loaders raise `SettingError`; each `main` formats it for its output. Unknown models show tokens only, no dollars.
- The agent reads Postgres only as `sasoi_reader`, through a read-only `run_sql` that returns at most `MAX_ROWS`. The schema description lists only tables with a comment.
- Sync stores only sessions not yet stored (Garmin: latest `SASOI_GARMIN_LIMIT`), so backfill and incremental sync are the same code.
- `garmin_mapping.py` and `hevy_mapping.py` are allow-lists: fields not mapped are never stored.
- Garmin login may prompt for email, password and MFA. Hevy's `/login` needs a reCAPTCHA token, so `hevy_login` prompts once for a token pair copied from the web app.
- Sync logs to stdout at `SASOI_LOG_LEVEL`; third-party loggers stay at WARNING.
- Evals run cases in parallel, each with its own reader connection and trace in `traces/evals/<timestamp>/<repeat>/`. A case passes when one of the agent's `run_sql` results contains every row of the ground-truth query (columns in any order, numbers within rounding or a unit scale).
