BEGIN IMMEDIATE;

CREATE TABLE run_attempts (
    attempt_id INTEGER PRIMARY KEY,
    run_id INTEGER NOT NULL,
    attempt_index INTEGER NOT NULL CHECK (attempt_index >= 1),
    status TEXT NOT NULL
        CHECK (status IN ('running', 'completed', 'failed', 'cancelled', 'abandoned')),
    started_at TEXT NOT NULL,
    finished_at TEXT,
    error_type TEXT,
    error_message TEXT,
    recovery_reason TEXT,
    discarded_trace_points INTEGER NOT NULL DEFAULT 0
        CHECK (discarded_trace_points >= 0),
    discarded_run_metrics INTEGER NOT NULL DEFAULT 0
        CHECK (discarded_run_metrics >= 0),
    FOREIGN KEY (run_id) REFERENCES runs(run_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    UNIQUE (run_id, attempt_index),
    CHECK (status = 'running' OR finished_at IS NOT NULL),
    CHECK (status <> 'abandoned' OR recovery_reason IS NOT NULL)
);

CREATE UNIQUE INDEX idx_run_attempts_one_running
ON run_attempts(run_id)
WHERE status = 'running';

CREATE INDEX idx_run_attempts_run
ON run_attempts(run_id, attempt_index);

INSERT INTO run_attempts (
    run_id, attempt_index, status, started_at, finished_at,
    error_type, error_message
)
SELECT
    run_id,
    1,
    status,
    COALESCE(started_at, finished_at, 'legacy-unknown'),
    finished_at,
    error_type,
    error_message
FROM runs
WHERE status IN ('running', 'completed', 'failed', 'cancelled')
  AND (started_at IS NOT NULL OR finished_at IS NOT NULL);

INSERT INTO schema_migrations(version, name, applied_at)
VALUES (4, 'run_attempts', strftime('%Y-%m-%dT%H:%M:%fZ', 'now'));

COMMIT;
