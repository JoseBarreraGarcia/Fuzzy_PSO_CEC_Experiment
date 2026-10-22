BEGIN IMMEDIATE;

ALTER TABLE campaigns ADD COLUMN base_seed INTEGER
    CHECK (base_seed IS NULL OR base_seed >= 0);
ALTER TABLE campaigns ADD COLUMN seed_protocol TEXT;
ALTER TABLE campaigns ADD COLUMN rng_engine TEXT;

ALTER TABLE runs ADD COLUMN initial_population_sha256 TEXT
    CHECK (
        initial_population_sha256 IS NULL
        OR length(initial_population_sha256) = 64
    );
ALTER TABLE runs ADD COLUMN initial_velocity_sha256 TEXT
    CHECK (
        initial_velocity_sha256 IS NULL
        OR length(initial_velocity_sha256) = 64
    );

CREATE TRIGGER validate_paired_run_seed_insert
BEFORE INSERT ON runs
WHEN (
    SELECT seed_protocol FROM campaigns
    WHERE campaign_id = NEW.campaign_id
) = 'paired_by_replica_v1'
BEGIN
    SELECT CASE
        WHEN NEW.random_seed IS NULL THEN
            RAISE(ABORT, 'paired campaign requires random_seed')
        WHEN NEW.random_seed < 0 THEN
            RAISE(ABORT, 'random_seed must be non-negative')
        WHEN NEW.random_seed != (
            SELECT base_seed + NEW.replica_index
            FROM campaigns WHERE campaign_id = NEW.campaign_id
        ) THEN
            RAISE(ABORT, 'random_seed must equal base_seed + replica_index')
    END;
END;

CREATE TRIGGER validate_paired_run_seed_update
BEFORE UPDATE OF replica_index, random_seed, campaign_id ON runs
WHEN (
    SELECT seed_protocol FROM campaigns
    WHERE campaign_id = NEW.campaign_id
) = 'paired_by_replica_v1'
BEGIN
    SELECT CASE
        WHEN NEW.random_seed IS NULL THEN
            RAISE(ABORT, 'paired campaign requires random_seed')
        WHEN NEW.random_seed < 0 THEN
            RAISE(ABORT, 'random_seed must be non-negative')
        WHEN NEW.random_seed != (
            SELECT base_seed + NEW.replica_index
            FROM campaigns WHERE campaign_id = NEW.campaign_id
        ) THEN
            RAISE(ABORT, 'random_seed must equal base_seed + replica_index')
    END;
END;

CREATE INDEX idx_runs_paired_replica
ON runs (campaign_id, instance_id, replica_index, random_seed);

INSERT INTO schema_migrations(version, name, applied_at)
VALUES (2, 'paired_randomness', strftime('%Y-%m-%dT%H:%M:%fZ', 'now'));

COMMIT;
