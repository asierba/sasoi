DROP TABLE garmin_runs;

CREATE TABLE garmin_runs (
    activity_id bigint PRIMARY KEY,
    activity_type text NOT NULL,
    name text,
    start_time_local timestamp NOT NULL,
    start_time_utc timestamptz NOT NULL,
    distance_m double precision NOT NULL,
    duration_s double precision NOT NULL,
    moving_duration_s double precision,
    avg_speed_mps double precision NOT NULL,
    max_speed_mps double precision NOT NULL,
    avg_hr double precision,
    max_hr double precision,
    hr_zone_1_s double precision,
    hr_zone_2_s double precision,
    hr_zone_3_s double precision,
    hr_zone_4_s double precision,
    hr_zone_5_s double precision,
    avg_cadence_spm double precision NOT NULL,
    max_cadence_spm double precision NOT NULL,
    elevation_gain_m double precision NOT NULL,
    elevation_loss_m double precision NOT NULL,
    aerobic_training_effect double precision,
    anaerobic_training_effect double precision,
    training_load double precision,
    vo2max double precision,
    lap_count integer
);

CREATE TABLE garmin_laps (
    activity_id bigint NOT NULL REFERENCES garmin_runs ON DELETE CASCADE,
    lap_index integer NOT NULL,
    start_time_utc timestamptz NOT NULL,
    distance_m double precision NOT NULL,
    duration_s double precision NOT NULL,
    avg_speed_mps double precision NOT NULL,
    max_speed_mps double precision NOT NULL,
    avg_hr double precision,
    max_hr double precision,
    avg_cadence_spm double precision NOT NULL,
    elevation_gain_m double precision NOT NULL,
    elevation_loss_m double precision NOT NULL,
    intensity_type text,
    PRIMARY KEY (activity_id, lap_index)
);
