BEGIN IMMEDIATE;

ALTER TABLE runs ADD COLUMN cancellation_reason TEXT;
ALTER TABLE run_attempts ADD COLUMN cancellation_reason TEXT;

UPDATE runs
SET cancellation_reason = 'legacy cancellation without recorded reason'
WHERE status = 'cancelled' AND cancellation_reason IS NULL;

UPDATE run_attempts
SET cancellation_reason = 'legacy cancellation without recorded reason'
WHERE status = 'cancelled' AND cancellation_reason IS NULL;

CREATE TABLE campaign_seal_waivers (
    campaign_id TEXT PRIMARY KEY,
    reason TEXT NOT NULL CHECK (trim(reason) <> ''),
    approved_at TEXT NOT NULL,
    failed_run_count INTEGER NOT NULL CHECK (failed_run_count >= 0),
    cancelled_run_count INTEGER NOT NULL CHECK (cancelled_run_count >= 0),
    FOREIGN KEY (campaign_id) REFERENCES campaigns(campaign_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT
);

INSERT INTO schema_migrations(version, name, applied_at)
VALUES (5, 'cancellation_and_seal_waivers', strftime('%Y-%m-%dT%H:%M:%fZ', 'now'));

COMMIT;
