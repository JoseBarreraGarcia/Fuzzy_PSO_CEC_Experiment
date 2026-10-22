BEGIN IMMEDIATE;

CREATE TABLE campaigns (
    campaign_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'draft'
        CHECK (status IN ('draft', 'running', 'completed', 'failed', 'sealed')),
    config_json TEXT NOT NULL,
    config_sha256 TEXT NOT NULL
        CHECK (length(config_sha256) = 64),
    code_commit TEXT NOT NULL,
    metric_registry_version INTEGER NOT NULL CHECK (metric_registry_version >= 1),
    schema_version INTEGER NOT NULL CHECK (schema_version >= 1),
    created_at TEXT NOT NULL,
    started_at TEXT,
    finished_at TEXT,
    sealed_at TEXT,
    notes TEXT,
    CHECK (status <> 'sealed' OR sealed_at IS NOT NULL)
);

CREATE TABLE problem_instances (
    instance_id INTEGER PRIMARY KEY,
    problem_family TEXT NOT NULL,
    name TEXT NOT NULL,
    dimension INTEGER,
    optimum REAL,
    direction TEXT NOT NULL DEFAULT 'minimize'
        CHECK (direction IN ('minimize', 'maximize')),
    parameters_json TEXT NOT NULL DEFAULT '{}',
    data_sha256 TEXT,
    CHECK (dimension IS NULL OR dimension > 0),
    CHECK (data_sha256 IS NULL OR length(data_sha256) = 64),
    UNIQUE (problem_family, name, dimension, parameters_json)
);

CREATE TABLE algorithm_configurations (
    configuration_id TEXT PRIMARY KEY,
    campaign_id TEXT NOT NULL,
    algorithm TEXT NOT NULL,
    parameters_json TEXT NOT NULL,
    parameters_sha256 TEXT NOT NULL CHECK (length(parameters_sha256) = 64),
    budget_type TEXT NOT NULL
        CHECK (budget_type IN ('evaluations', 'iterations', 'hybrid')),
    budget_evaluations INTEGER,
    budget_iterations INTEGER,
    population_size INTEGER,
    created_at TEXT NOT NULL,
    FOREIGN KEY (campaign_id) REFERENCES campaigns(campaign_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CHECK (budget_evaluations IS NULL OR budget_evaluations > 0),
    CHECK (budget_iterations IS NULL OR budget_iterations > 0),
    CHECK (population_size IS NULL OR population_size > 0),
    CHECK (
        (budget_type = 'evaluations' AND budget_evaluations IS NOT NULL) OR
        (budget_type = 'iterations' AND budget_iterations IS NOT NULL) OR
        (budget_type = 'hybrid' AND budget_evaluations IS NOT NULL
                                AND budget_iterations IS NOT NULL)
    ),
    UNIQUE (configuration_id, campaign_id)
);

CREATE TABLE runs (
    run_id INTEGER PRIMARY KEY,
    campaign_id TEXT NOT NULL,
    configuration_id TEXT NOT NULL,
    instance_id INTEGER NOT NULL,
    replica_index INTEGER NOT NULL CHECK (replica_index >= 0),
    random_seed INTEGER,
    status TEXT NOT NULL DEFAULT 'planned'
        CHECK (status IN ('planned', 'running', 'completed', 'failed', 'cancelled')),
    started_at TEXT,
    finished_at TEXT,
    objective_best REAL,
    solution_json TEXT,
    evaluations INTEGER CHECK (evaluations IS NULL OR evaluations >= 0),
    runtime_total_seconds REAL
        CHECK (runtime_total_seconds IS NULL OR runtime_total_seconds >= 0),
    feasible INTEGER CHECK (feasible IS NULL OR feasible IN (0, 1)),
    constraint_violation REAL
        CHECK (constraint_violation IS NULL OR constraint_violation >= 0),
    error_type TEXT,
    error_message TEXT,
    FOREIGN KEY (campaign_id) REFERENCES campaigns(campaign_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    FOREIGN KEY (configuration_id, campaign_id)
        REFERENCES algorithm_configurations(configuration_id, campaign_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    FOREIGN KEY (instance_id) REFERENCES problem_instances(instance_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    UNIQUE (campaign_id, configuration_id, instance_id, replica_index),
    CHECK (status <> 'completed' OR objective_best IS NOT NULL),
    CHECK (status <> 'failed' OR error_type IS NOT NULL)
);

CREATE TABLE metric_definitions (
    metric_id TEXT NOT NULL,
    metric_version INTEGER NOT NULL CHECK (metric_version >= 1),
    definition_json TEXT NOT NULL,
    definition_sha256 TEXT NOT NULL CHECK (length(definition_sha256) = 64),
    PRIMARY KEY (metric_id, metric_version)
);

CREATE TABLE campaign_metrics (
    campaign_id TEXT NOT NULL,
    metric_id TEXT NOT NULL,
    metric_version INTEGER NOT NULL,
    sampling_json TEXT NOT NULL DEFAULT '{}',
    required INTEGER NOT NULL DEFAULT 0 CHECK (required IN (0, 1)),
    PRIMARY KEY (campaign_id, metric_id),
    FOREIGN KEY (campaign_id) REFERENCES campaigns(campaign_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    FOREIGN KEY (metric_id, metric_version)
        REFERENCES metric_definitions(metric_id, metric_version)
        ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE trace_points (
    run_id INTEGER NOT NULL,
    checkpoint_index INTEGER NOT NULL CHECK (checkpoint_index >= 0),
    iteration_index INTEGER CHECK (iteration_index IS NULL OR iteration_index >= 0),
    evaluations INTEGER NOT NULL CHECK (evaluations >= 0),
    elapsed_seconds REAL CHECK (elapsed_seconds IS NULL OR elapsed_seconds >= 0),
    PRIMARY KEY (run_id, checkpoint_index),
    FOREIGN KEY (run_id) REFERENCES runs(run_id)
        ON UPDATE RESTRICT ON DELETE CASCADE
);

CREATE TABLE run_metric_values (
    run_id INTEGER NOT NULL,
    metric_id TEXT NOT NULL,
    metric_version INTEGER NOT NULL,
    provenance TEXT NOT NULL DEFAULT 'observed'
        CHECK (provenance IN ('observed', 'reconstructed', 'expected')),
    value_real REAL,
    value_integer INTEGER,
    value_text TEXT,
    value_json TEXT,
    PRIMARY KEY (run_id, metric_id),
    FOREIGN KEY (run_id) REFERENCES runs(run_id)
        ON UPDATE RESTRICT ON DELETE CASCADE,
    FOREIGN KEY (metric_id, metric_version)
        REFERENCES metric_definitions(metric_id, metric_version)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CHECK (
        (value_real IS NOT NULL) +
        (value_integer IS NOT NULL) +
        (value_text IS NOT NULL) +
        (value_json IS NOT NULL) = 1
    )
);

CREATE TABLE trace_metric_values (
    run_id INTEGER NOT NULL,
    checkpoint_index INTEGER NOT NULL,
    metric_id TEXT NOT NULL,
    metric_version INTEGER NOT NULL,
    provenance TEXT NOT NULL DEFAULT 'observed'
        CHECK (provenance IN ('observed', 'reconstructed', 'expected')),
    value_real REAL,
    value_integer INTEGER,
    value_text TEXT,
    value_json TEXT,
    PRIMARY KEY (run_id, checkpoint_index, metric_id),
    FOREIGN KEY (run_id, checkpoint_index)
        REFERENCES trace_points(run_id, checkpoint_index)
        ON UPDATE RESTRICT ON DELETE CASCADE,
    FOREIGN KEY (metric_id, metric_version)
        REFERENCES metric_definitions(metric_id, metric_version)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CHECK (
        (value_real IS NOT NULL) +
        (value_integer IS NOT NULL) +
        (value_text IS NOT NULL) +
        (value_json IS NOT NULL) = 1
    )
);

CREATE INDEX idx_runs_campaign_status
    ON runs(campaign_id, status);
CREATE INDEX idx_runs_configuration_instance
    ON runs(configuration_id, instance_id);
CREATE INDEX idx_trace_points_evaluations
    ON trace_points(run_id, evaluations);
CREATE INDEX idx_trace_metric_lookup
    ON trace_metric_values(metric_id, run_id, checkpoint_index);

INSERT INTO schema_migrations(version, name, applied_at)
VALUES (1, 'initial_schema', strftime('%Y-%m-%dT%H:%M:%fZ', 'now'));

COMMIT;
