BEGIN IMMEDIATE;

ALTER TABLE algorithm_configurations ADD COLUMN optimizer_version TEXT;

CREATE TRIGGER require_optimizer_version_insert
BEFORE INSERT ON algorithm_configurations
WHEN NEW.optimizer_version IS NULL OR trim(NEW.optimizer_version) = ''
BEGIN
    SELECT RAISE(ABORT, 'optimizer_version is required');
END;

CREATE TRIGGER require_optimizer_version_update
BEFORE UPDATE OF optimizer_version ON algorithm_configurations
WHEN NEW.optimizer_version IS NULL OR trim(NEW.optimizer_version) = ''
BEGIN
    SELECT RAISE(ABORT, 'optimizer_version is required');
END;

INSERT INTO schema_migrations(version, name, applied_at)
VALUES (3, 'optimizer_version', strftime('%Y-%m-%dT%H:%M:%fZ', 'now'));

COMMIT;
