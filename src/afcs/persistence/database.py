"""Versioned SQLite schema bootstrap for v2 experimental campaigns.

This module prepares the campaign schema without importing or automatically
converting historical databases.
"""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from dataclasses import asdict, dataclass
from pathlib import Path

from afcs.metrics import MetricRegistry

DEFAULT_MIGRATIONS_DIR = Path(__file__).with_name("migrations")
MIGRATION_NAME_PATTERN = re.compile(r"^(?P<version>[0-9]{3})_[a-z0-9_]+\.sql$")


class MigrationError(RuntimeError):
    """Raised when migration discovery or application is inconsistent."""


@dataclass(frozen=True, order=True)
class Migration:
    version: int
    name: str
    path: Path


def connect_v2_database(path: str | Path) -> sqlite3.Connection:
    """Open a v2 database connection with integrity settings enabled."""

    connection = sqlite3.connect(Path(path), timeout=30)
    try:
        connection.row_factory = sqlite3.Row
        current_schema_version(connection)
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA journal_mode = WAL")
    except Exception:
        connection.close()
        raise
    return connection


def connect_readonly_v2_database(path: str | Path) -> sqlite3.Connection:
    """Open existing current-schema evidence without bootstrap or migration."""

    uri = Path(path).resolve().as_uri() + "?mode=ro"
    connection = sqlite3.connect(uri, uri=True, timeout=30)
    try:
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA query_only = ON")
        validate_current_schema(connection)
    except Exception:
        connection.close()
        raise
    return connection


def discover_migrations(
    migrations_dir: str | Path = DEFAULT_MIGRATIONS_DIR,
) -> tuple[Migration, ...]:
    directory = Path(migrations_dir)
    migrations: list[Migration] = []

    for path in sorted(directory.glob("*.sql")):
        match = MIGRATION_NAME_PATTERN.fullmatch(path.name)
        if match is None:
            raise MigrationError(f"Invalid migration filename: {path.name}")
        migrations.append(
            Migration(
                version=int(match.group("version")),
                name=path.stem[4:],
                path=path,
            )
        )

    if not migrations:
        raise MigrationError(f"No migrations found in {directory}")

    versions = [migration.version for migration in migrations]
    if len(versions) != len(set(versions)):
        raise MigrationError("Migration versions must be unique")
    expected = list(range(1, max(versions) + 1))
    if versions != expected:
        raise MigrationError(
            f"Migration versions must be contiguous; found={versions}, expected={expected}"
        )
    return tuple(migrations)


def _validated_schema_version(
    connection: sqlite3.Connection, migrations: tuple[Migration, ...]
) -> int:
    ledger = connection.execute(
        "SELECT type FROM sqlite_master WHERE name='schema_migrations'"
    ).fetchone()
    if ledger is None:
        rows = []
    else:
        if ledger[0] != "table":
            raise MigrationError("schema_migrations must be a table")
        try:
            rows = connection.execute(
                "SELECT version, name FROM schema_migrations ORDER BY version"
            ).fetchall()
        except sqlite3.Error as error:
            raise MigrationError(f"Invalid migration ledger: {error}") from error
    versions = [row[0] for row in rows]
    latest = migrations[-1].version
    if any(not isinstance(version, int) for version in versions):
        raise MigrationError("Migration ledger versions must be integers")
    if any(version > latest for version in versions):
        raise MigrationError(
            f"Unsupported future schema: found={versions}, latest supported={latest}"
        )
    if versions != list(range(1, len(versions) + 1)):
        raise MigrationError(
            f"Migration ledger must be a contiguous prefix: {versions}"
        )
    for row, migration in zip(rows, migrations):
        if row[1] != migration.name:
            raise MigrationError(
                f"Migration {migration.version} name mismatch: "
                f"database={row[1]!r}, file={migration.name!r}"
            )
    if (
        not versions
        and connection.execute(
            """
        SELECT name FROM sqlite_master
        WHERE name NOT LIKE 'sqlite_%' AND name != 'schema_migrations'
        LIMIT 1
        """
        ).fetchone()
        is not None
    ):
        raise MigrationError("Cannot bootstrap a nonempty unversioned database")
    return len(versions)


def validate_current_schema(connection: sqlite3.Connection) -> None:
    """Require the current known ledger, without changing the connection's data."""

    migrations = discover_migrations()
    version = _validated_schema_version(connection, migrations)
    if version != migrations[-1].version:
        raise MigrationError(
            f"Operation requires current schema {migrations[-1].version}; "
            f"found {version}. Migrate explicitly before inspection."
        )


def apply_migrations(
    connection: sqlite3.Connection,
    migrations_dir: str | Path = DEFAULT_MIGRATIONS_DIR,
) -> tuple[int, ...]:
    """Apply missing migrations and return the versions applied in this call."""

    if connection.in_transaction:
        raise MigrationError("Cannot apply migrations inside an active transaction")
    migrations = discover_migrations(migrations_dir)
    version = _validated_schema_version(connection, migrations)
    if version == migrations[-1].version:
        return ()
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version INTEGER PRIMARY KEY,
            name TEXT NOT NULL UNIQUE,
            applied_at TEXT NOT NULL
        )
        """
    )
    connection.commit()

    newly_applied: list[int] = []

    for migration in migrations[version:]:
        sql = migration.path.read_text(encoding="utf-8")
        try:
            connection.executescript(sql)
        except sqlite3.Error as error:
            connection.rollback()
            raise MigrationError(
                f"Failed to apply migration {migration.path.name}: {error}"
            ) from error
        newly_applied.append(migration.version)

    return tuple(newly_applied)


def initialize_v2_database(path: str | Path) -> sqlite3.Connection:
    """Open a database and bring it to the latest available schema version."""

    connection = connect_v2_database(path)
    try:
        apply_migrations(connection)
    except Exception:
        connection.close()
        raise
    return connection


def current_schema_version(connection: sqlite3.Connection) -> int:
    """Return a validated known prefix version, not an unchecked MAX marker."""

    return _validated_schema_version(connection, discover_migrations())


def sync_metric_definitions(
    connection: sqlite3.Connection, registry: MetricRegistry
) -> int:
    """Persist immutable snapshots of metric definitions.

    Existing definitions must have the same canonical hash. Changing a metric
    therefore requires incrementing its version instead of rewriting history.
    The caller owns the transaction.
    """

    inserted = 0
    for definition in registry.metrics.values():
        payload = json.dumps(
            asdict(definition),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        existing = connection.execute(
            """
            SELECT definition_sha256
            FROM metric_definitions
            WHERE metric_id = ? AND metric_version = ?
            """,
            (definition.metric_id, definition.version),
        ).fetchone()
        if existing is not None:
            if existing["definition_sha256"] != digest:
                raise MigrationError(
                    f"Metric definition changed without version bump: "
                    f"{definition.metric_id}@{definition.version}"
                )
            continue
        connection.execute(
            """
            INSERT INTO metric_definitions (
                metric_id, metric_version, definition_json, definition_sha256
            ) VALUES (?, ?, ?, ?)
            """,
            (definition.metric_id, definition.version, payload, digest),
        )
        inserted += 1
    return inserted


def configure_campaign_metrics(
    connection: sqlite3.Connection,
    campaign_id: str,
    registry: MetricRegistry,
    selection: object = "minimal",
) -> tuple[str, ...]:
    """Resolve and persist the metric selection for a draft campaign."""

    campaign = connection.execute(
        "SELECT status FROM campaigns WHERE campaign_id = ?", (campaign_id,)
    ).fetchone()
    if campaign is None:
        raise MigrationError(f"Unknown campaign: {campaign_id!r}")
    if campaign["status"] != "draft":
        raise MigrationError(
            "Metric selection can only change while a campaign is draft"
        )

    sync_metric_definitions(connection, registry)
    resolved = registry.resolve(selection)
    required = set(registry.required_metrics)

    connection.execute(
        "DELETE FROM campaign_metrics WHERE campaign_id = ?", (campaign_id,)
    )
    for metric_id in resolved:
        definition = registry.metrics[metric_id]
        connection.execute(
            """
            INSERT INTO campaign_metrics (
                campaign_id, metric_id, metric_version, sampling_json, required
            ) VALUES (?, ?, ?, '{}', ?)
            """,
            (
                campaign_id,
                metric_id,
                definition.version,
                int(metric_id in required),
            ),
        )
    return resolved
