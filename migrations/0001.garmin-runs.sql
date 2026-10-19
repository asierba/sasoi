CREATE TABLE garmin_runs (
    activity_id bigint PRIMARY KEY,
    summary jsonb NOT NULL,
    splits jsonb NOT NULL,
    fetched_at timestamptz NOT NULL DEFAULT now()
);
