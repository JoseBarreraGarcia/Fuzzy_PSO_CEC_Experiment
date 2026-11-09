BEGIN IMMEDIATE;

ALTER TABLE runs ADD COLUMN failure_phase TEXT;
ALTER TABLE run_attempts ADD COLUMN failure_phase TEXT;
ALTER TABLE runs ADD COLUMN finalization_status TEXT
    CHECK (finalization_status IS NULL OR finalization_status IN ('pending', 'completed', 'failed'));
ALTER TABLE runs ADD COLUMN finalization_error_type TEXT;
ALTER TABLE runs ADD COLUMN finalization_error_message TEXT;

INSERT INTO schema_migrations(version, name, applied_at)
VALUES (7, 'run_finalization', strftime('%Y-%m-%dT%H:%M:%fZ', 'now'));

COMMIT;
