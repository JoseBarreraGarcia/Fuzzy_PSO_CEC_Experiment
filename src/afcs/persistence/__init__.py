"""Versioned SQLite persistence for AFCS campaigns."""

from .database import (
    DEFAULT_MIGRATIONS_DIR,
    Migration,
    MigrationError,
    apply_migrations,
    configure_campaign_metrics,
    connect_readonly_v2_database,
    connect_v2_database,
    current_schema_version,
    discover_migrations,
    initialize_v2_database,
    sync_metric_definitions,
    validate_current_schema,
)
from .integrity import (
    CampaignIntegrityIssue,
    CampaignIntegrityReport,
    CampaignIntegrityWarning,
    audit_campaign_integrity,
)
from .repository import (
    ExperimentRepository,
    PlannedRun,
    RepositoryError,
    StoredValue,
    canonical_json,
    encode_metric_value,
    sha256_text,
    utc_now,
)

__all__ = [
    "DEFAULT_MIGRATIONS_DIR",
    "ExperimentRepository",
    "CampaignIntegrityIssue",
    "CampaignIntegrityReport",
    "CampaignIntegrityWarning",
    "Migration",
    "MigrationError",
    "PlannedRun",
    "RepositoryError",
    "StoredValue",
    "apply_migrations",
    "audit_campaign_integrity",
    "canonical_json",
    "configure_campaign_metrics",
    "connect_v2_database",
    "connect_readonly_v2_database",
    "current_schema_version",
    "discover_migrations",
    "encode_metric_value",
    "initialize_v2_database",
    "sha256_text",
    "sync_metric_definitions",
    "utc_now",
    "validate_current_schema",
]
