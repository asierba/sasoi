CREATE ROLE sasoi_reader LOGIN PASSWORD 'sasoi_reader';
GRANT SELECT ON garmin_runs, garmin_laps TO sasoi_reader;
