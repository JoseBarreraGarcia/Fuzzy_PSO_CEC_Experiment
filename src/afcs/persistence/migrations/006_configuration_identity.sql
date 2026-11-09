BEGIN IMMEDIATE;

ALTER TABLE algorithm_configurations ADD COLUMN treatment_id TEXT
    CHECK (treatment_id IS NULL OR trim(treatment_id) <> '');

UPDATE algorithm_configurations SET treatment_id = configuration_id;

CREATE UNIQUE INDEX uq_campaign_treatment
    ON algorithm_configurations(campaign_id, COALESCE(treatment_id, configuration_id));

ALTER TABLE runs ADD COLUMN initial_state_hash_version TEXT
    CHECK (initial_state_hash_version IS NULL OR trim(initial_state_hash_version) <> '');

INSERT INTO schema_migrations(version, name, applied_at)
VALUES (6, 'configuration_identity', strftime('%Y-%m-%dT%H:%M:%fZ', 'now'));

COMMIT;
