CREATE TABLE hevy_workouts (
    workout_id text PRIMARY KEY,
    name text NOT NULL,
    description text,
    start_time_utc timestamptz NOT NULL,
    end_time_utc timestamptz NOT NULL
);

CREATE TABLE hevy_exercises (
    workout_id text NOT NULL REFERENCES hevy_workouts ON DELETE CASCADE,
    exercise_index integer NOT NULL,
    title text NOT NULL,
    template_id text NOT NULL,
    exercise_type text NOT NULL,
    muscle_group text NOT NULL,
    other_muscles text[] NOT NULL,
    equipment text NOT NULL,
    superset_id integer,
    notes text,
    PRIMARY KEY (workout_id, exercise_index)
);

CREATE TABLE hevy_sets (
    workout_id text NOT NULL,
    exercise_index integer NOT NULL,
    set_index integer NOT NULL,
    set_type text NOT NULL,
    weight_kg double precision,
    reps integer,
    duration_s double precision,
    distance_m double precision,
    rpe double precision,
    completed_at_utc timestamptz,
    PRIMARY KEY (workout_id, exercise_index, set_index),
    FOREIGN KEY (workout_id, exercise_index) REFERENCES hevy_exercises ON DELETE CASCADE
);
