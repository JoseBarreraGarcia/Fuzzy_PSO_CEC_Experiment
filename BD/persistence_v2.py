"""Compatibility bridge for persistence moved to :mod:`afcs.persistence`."""

from afcs.persistence.database import (
    DEFAULT_MIGRATIONS_DIR,
    MIGRATION_NAME_PATTERN,
    Migration,
    MigrationError,
    apply_migrations,
    configure_campaign_metrics,
    connect_v2_database,
    current_schema_version,
    discover_migrations,
    initialize_v2_database,
    sync_metric_definitions,
)

__all__ = [
    "DEFAULT_MIGRATIONS_DIR",
    "MIGRATION_NAME_PATTERN",
    "Migration",
    "MigrationError",
    "apply_migrations",
    "configure_campaign_metrics",
    "connect_v2_database",
    "current_schema_version",
    "discover_migrations",
    "initialize_v2_database",
    "sync_metric_definitions",
]

