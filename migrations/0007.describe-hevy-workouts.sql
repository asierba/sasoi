COMMENT ON TABLE hevy_workouts IS 'One row per strength session logged in Hevy.';
COMMENT ON COLUMN hevy_workouts.workout_id IS 'Hevy workout id.';
COMMENT ON COLUMN hevy_workouts.name IS 'Title given to the workout in Hevy.';
COMMENT ON COLUMN hevy_workouts.description IS 'Notes written for the whole workout.';
COMMENT ON COLUMN hevy_workouts.start_time_utc IS 'Start time in UTC. Convert to the user''s time zone for dates and weekdays.';
COMMENT ON COLUMN hevy_workouts.end_time_utc IS 'End time in UTC. Duration is end_time_utc - start_time_utc.';

COMMENT ON TABLE hevy_exercises IS 'Exercises of each workout, in the order they were done.';
COMMENT ON COLUMN hevy_exercises.workout_id IS 'The workout this exercise belongs to (hevy_workouts.workout_id).';
COMMENT ON COLUMN hevy_exercises.exercise_index IS 'Position in the workout, starting at 0.';
COMMENT ON COLUMN hevy_exercises.title IS 'Exercise name as shown in Hevy, e.g. ''Squat (Barbell)''. Equipment is part of the name.';
COMMENT ON COLUMN hevy_exercises.template_id IS 'Hevy exercise template id; the same exercise has the same id in every workout. Group by it to follow one exercise over time.';
COMMENT ON COLUMN hevy_exercises.exercise_type IS 'Which set columns are filled: weight_reps (weight_kg and reps), reps_only (reps), duration (duration_s), or another Hevy type.';
COMMENT ON COLUMN hevy_exercises.muscle_group IS 'Primary muscle group, e.g. chest, quadriceps, hamstrings, glutes, lats, upper_back, shoulders, biceps, triceps, abdominals, full_body.';
COMMENT ON COLUMN hevy_exercises.other_muscles IS 'Secondary muscle groups, same values as muscle_group.';
COMMENT ON COLUMN hevy_exercises.equipment IS 'barbell, dumbbell, kettlebell, machine, resistance_band, none or other.';
COMMENT ON COLUMN hevy_exercises.superset_id IS 'Exercises of a workout with the same superset_id were done as a superset. Null when not in a superset.';
COMMENT ON COLUMN hevy_exercises.notes IS 'Notes written for this exercise in this workout.';

COMMENT ON TABLE hevy_sets IS 'Sets of each exercise. Join to hevy_exercises on workout_id and exercise_index.';
COMMENT ON COLUMN hevy_sets.workout_id IS 'The workout this set belongs to (hevy_workouts.workout_id).';
COMMENT ON COLUMN hevy_sets.exercise_index IS 'The exercise this set belongs to (hevy_exercises.exercise_index).';
COMMENT ON COLUMN hevy_sets.set_index IS 'Position in the exercise, starting at 0.';
COMMENT ON COLUMN hevy_sets.set_type IS 'normal, warmup, dropset or failure. Leave out warmup sets for volume, top sets and set counts unless asked.';
COMMENT ON COLUMN hevy_sets.weight_kg IS 'Load in kg. Null for exercises without weight. Volume is sum(weight_kg * reps).';
COMMENT ON COLUMN hevy_sets.reps IS 'Repetitions. Null for duration exercises.';
COMMENT ON COLUMN hevy_sets.duration_s IS 'Hold or work time in seconds, for duration exercises.';
COMMENT ON COLUMN hevy_sets.distance_m IS 'Distance in metres, for distance exercises.';
COMMENT ON COLUMN hevy_sets.rpe IS 'Rate of perceived exertion, 6 to 10. Null when not logged.';
COMMENT ON COLUMN hevy_sets.completed_at_utc IS 'Time the set was ticked as done, in UTC. Null when not recorded.';

GRANT SELECT ON hevy_workouts, hevy_exercises, hevy_sets TO sasoi_reader;
