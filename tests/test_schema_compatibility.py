import sqlite3
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from afcs.analysis import export_campaign_csv
from afcs.experiments.cli import main
from afcs.metrics import load_metric_registry
from afcs.persistence import (
    ExperimentRepository,
    MigrationError,
    apply_migrations,
    audit_campaign_integrity,
    connect_readonly_v2_database,
    current_schema_version,
    discover_migrations,
    initialize_v2_database,
)
from afcs.problems.benchmarks.cec2017 import transforms
from afcs.problems.benchmarks.cec2017.problem import CEC2017_DATA_SHA256


class TestSchemaCompatibility(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / "campaign #1%26.db"
        self.connection = initialize_v2_database(self.path)
        self.addCleanup(self.connection.close)

    def test_invalid_ledger_rejected_before_writes_or_replay(self):
        cases = (
            ("INSERT INTO schema_migrations VALUES(999,'future','test')", "future"),
            ("DELETE FROM schema_migrations WHERE version=3", "prefix"),
            ("UPDATE schema_migrations SET name='different' WHERE version=5", "name"),
            ("UPDATE schema_migrations SET version=0 WHERE version=1", "prefix"),
        )
        for mutation, diagnostic in cases:
            with self.subTest(mutation=mutation):
                copy = sqlite3.connect(":memory:")
                self.addCleanup(copy.close)
                copy.row_factory = sqlite3.Row
                self.connection.backup(copy)
                copy.execute(mutation)
                copy.commit()
                before = "\n".join(copy.iterdump())
                statements = []
                copy.set_trace_callback(statements.append)
                for operation in (apply_migrations, current_schema_version):
                    with self.assertRaisesRegex(MigrationError, diagnostic):
                        operation(copy)
                copy.set_trace_callback(None)
                self.assertEqual("\n".join(copy.iterdump()), before)
                self.assertFalse(
                    any(
                        sql.lstrip()
                        .upper()
                        .startswith(("CREATE", "ALTER", "BEGIN", "COMMIT"))
                        for sql in statements
                    )
                )

    def test_discovery_errors_do_not_create_ledger(self):
        connection = sqlite3.connect(":memory:")
        connection.row_factory = sqlite3.Row
        self.addCleanup(connection.close)
        with self.assertRaises(MigrationError):
            apply_migrations(connection, Path(self.directory.name) / "missing")
        self.assertEqual(
            connection.execute("SELECT name FROM sqlite_master").fetchall(), []
        )

    def test_unversioned_nonempty_database_is_not_bootstrapped(self):
        connection = sqlite3.connect(":memory:")
        connection.row_factory = sqlite3.Row
        self.addCleanup(connection.close)
        connection.execute("CREATE TABLE historical(value TEXT)")
        before = "\n".join(connection.iterdump())
        with self.assertRaisesRegex(MigrationError, "unversioned"):
            apply_migrations(connection)
        self.assertEqual("\n".join(connection.iterdump()), before)

    def test_valid_prefix_is_migrated_explicitly(self):
        path = Path(self.directory.name) / "older.db"
        connection = sqlite3.connect(path)
        connection.row_factory = sqlite3.Row
        self.addCleanup(connection.close)
        connection.execute(
            "CREATE TABLE schema_migrations("
            "version INTEGER PRIMARY KEY,name TEXT NOT NULL UNIQUE,applied_at TEXT NOT NULL)"
        )
        migrations = discover_migrations()
        connection.executescript(migrations[0].path.read_text(encoding="utf-8"))
        self.assertEqual(current_schema_version(connection), 1)
        with self.assertRaisesRegex(MigrationError, "current schema"):
            audit_campaign_integrity(connection, "missing")
        self.assertEqual(apply_migrations(connection), (2, 3, 4, 5, 6, 7))
        self.assertEqual(current_schema_version(connection), 7)

    def test_cli_audit_missing_file_does_not_create_database(self):
        path = Path(self.directory.name) / "absent.db"
        with self.assertRaises(sqlite3.OperationalError):
            main(["audit", "--database", str(path), "--campaign-id", "missing"])
        self.assertFalse(path.exists())

    def test_cli_audit_old_schema_does_not_migrate_or_change_file(self):
        path = Path(self.directory.name) / "old.db"
        connection = sqlite3.connect(path)
        connection.execute(
            "CREATE TABLE schema_migrations("
            "version INTEGER PRIMARY KEY,name TEXT NOT NULL UNIQUE,applied_at TEXT NOT NULL)"
        )
        connection.executescript(
            discover_migrations()[0].path.read_text(encoding="utf-8")
        )
        connection.close()
        before = path.read_bytes()
        with self.assertRaisesRegex(MigrationError, "current schema"):
            main(["audit", "--database", str(path), "--campaign-id", "missing"])
        self.assertEqual(path.read_bytes(), before)
        self.assertFalse(Path(str(path) + "-wal").exists())

    def test_cli_audit_is_read_only_without_loading_live_registry(self):
        repository = ExperimentRepository(self.connection, load_metric_registry())
        repository.create_campaign("audit", "Audit", {}, "test")
        self.connection.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        before = self.path.read_bytes()
        output = StringIO()
        with patch(
            "afcs.experiments.cli.load_metric_registry",
            side_effect=AssertionError("audit must use persisted evidence"),
        ):
            with redirect_stdout(output):
                self.assertEqual(
                    main(
                        [
                            "audit",
                            "--database",
                            str(self.path),
                            "--campaign-id",
                            "audit",
                        ]
                    ),
                    0,
                )
        self.assertIn('"is_valid": true', output.getvalue())
        self.assertEqual(self.path.read_bytes(), before)

    def test_initializer_rejects_future_before_changing_journal_mode(self):
        path = Path(self.directory.name) / "future.db"
        connection = sqlite3.connect(path)
        self.connection.backup(connection)
        connection.execute("PRAGMA journal_mode=DELETE")
        connection.execute("INSERT INTO schema_migrations VALUES(999,'future','test')")
        connection.commit()
        connection.close()
        before = path.read_bytes()
        with self.assertRaisesRegex(MigrationError, "future"):
            initialize_v2_database(path)
        self.assertEqual(path.read_bytes(), before)
        self.assertFalse(Path(str(path) + "-wal").exists())

    def test_readonly_connection_rejects_writes_and_preserves_journal_mode(self):
        path = Path(self.directory.name) / "read only #2.db"
        writable = initialize_v2_database(path)
        writable.execute("PRAGMA journal_mode=DELETE")
        writable.close()
        before = path.read_bytes()
        readonly = connect_readonly_v2_database(path)
        self.addCleanup(readonly.close)
        self.assertEqual(
            readonly.execute("PRAGMA journal_mode").fetchone()[0], "delete"
        )
        with self.assertRaises(sqlite3.OperationalError):
            readonly.execute("CREATE TABLE forbidden(value TEXT)")
        self.assertEqual(path.read_bytes(), before)
        self.assertFalse(Path(str(path) + "-wal").exists())

    def test_repository_and_export_reject_unknown_schema_before_operating(self):
        self.connection.execute(
            "INSERT INTO schema_migrations VALUES(999,'future','test')"
        )
        self.connection.commit()
        with self.assertRaisesRegex(MigrationError, "future"):
            ExperimentRepository(self.connection, load_metric_registry())
        runs = Path(self.directory.name) / "runs.csv"
        traces = Path(self.directory.name) / "traces.csv"
        with self.assertRaisesRegex(MigrationError, "future"):
            export_campaign_csv(self.connection, "missing", runs, traces)
        self.assertFalse(runs.exists())
        self.assertFalse(traces.exists())

    def test_readonly_audit_includes_committed_wal_evidence(self):
        repository = ExperimentRepository(self.connection, load_metric_registry())
        self.connection.execute("PRAGMA wal_autocheckpoint=0")
        self.connection.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        before = self.path.read_bytes()
        repository.create_campaign("wal", "WAL evidence", {}, "test")
        self.assertEqual(self.path.read_bytes(), before)
        readonly = connect_readonly_v2_database(self.path)
        self.addCleanup(readonly.close)
        self.assertTrue(audit_campaign_integrity(readonly, "wal").is_valid)
        self.assertEqual(self.path.read_bytes(), before)


class TestCECResourceIntegrity(unittest.TestCase):
    def test_loader_checks_exact_bytes_before_deserializing(self):
        with patch.object(Path, "read_bytes", return_value=b"changed payload"):
            with patch.object(transforms.pickle, "loads") as deserialize:
                with self.assertRaisesRegex(ValueError, "SHA-256"):
                    transforms._load_data(Path("unused"))
                deserialize.assert_not_called()

    def test_module_load_rejects_changed_payload(self):
        import runpy

        with patch.object(Path, "read_bytes", return_value=b"changed payload"):
            with self.assertRaisesRegex(ValueError, "SHA-256"):
                runpy.run_path(transforms.__file__)

    def test_loaded_resource_matches_declared_digest(self):
        import hashlib

        payload = Path(transforms.__file__).with_name("data.pkl").read_bytes()
        self.assertEqual(hashlib.sha256(payload).hexdigest(), CEC2017_DATA_SHA256)
        self.assertEqual(transforms.CEC2017_DATA_SHA256, CEC2017_DATA_SHA256)
        data = transforms._load_data(Path(transforms.__file__).with_name("data.pkl"))
        self.assertEqual(data["shift"].shape, transforms.shifts.shape)
