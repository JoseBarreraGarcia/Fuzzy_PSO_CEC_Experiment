import sqlite3
import tempfile
import unittest
from pathlib import Path

from afcs.metrics import load_metric_registry
from afcs.persistence import (
    MigrationError,
    apply_migrations,
    configure_campaign_metrics,
    current_schema_version,
    initialize_v2_database,
    sync_metric_definitions,
)

HASH = "0" * 64


class TestPersistenceV2(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "campaign.db"
        self.connection = initialize_v2_database(self.db_path)

    def tearDown(self):
        self.connection.close()
        self.temp_dir.cleanup()

    def _insert_campaign_graph(self):
        self.connection.execute(
            """
            INSERT INTO campaigns (
                campaign_id, name, config_json, config_sha256, code_commit,
                metric_registry_version, schema_version, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            ("fixture", "Fixture", "{}", HASH, "abc123", 1, 1, "2026-10-19T00:00:00Z"),
        )
        self.connection.execute(
            """
            INSERT INTO problem_instances (
                problem_family, name, dimension, optimum
            ) VALUES (?, ?, ?, ?)
            """,
            ("BEN", "F1", 2, 0.0),
        )
        instance_id = self.connection.execute(
            "SELECT instance_id FROM problem_instances"
        ).fetchone()["instance_id"]
        self.connection.execute(
            """
            INSERT INTO algorithm_configurations (
                configuration_id, campaign_id, algorithm, optimizer_version,
                parameters_json,
                parameters_sha256, budget_type, budget_evaluations,
                population_size, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "pso-fixture",
                "fixture",
                "PSO",
                "fixture-version",
                "{}",
                HASH,
                "evaluations",
                100,
                20,
                "2026-10-19T00:00:00Z",
            ),
        )
        self.connection.commit()
        return instance_id

    def test_migration_is_idempotent(self):
        self.assertEqual(current_schema_version(self.connection), 7)
        self.assertEqual(apply_migrations(self.connection), ())

    def test_expected_tables_exist(self):
        names = {
            row["name"]
            for row in self.connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
        }
        self.assertTrue(
            {
                "campaigns",
                "problem_instances",
                "algorithm_configurations",
                "runs",
                "metric_definitions",
                "campaign_metrics",
                "trace_points",
                "run_metric_values",
                "trace_metric_values",
                "run_attempts",
                "campaign_seal_waivers",
                "schema_migrations",
            }
            <= names
        )

    def test_foreign_keys_are_enforced(self):
        self.assertEqual(
            self.connection.execute("PRAGMA foreign_keys").fetchone()[0], 1
        )
        with self.assertRaises(sqlite3.IntegrityError):
            self.connection.execute(
                """
                INSERT INTO runs (
                    campaign_id, configuration_id, instance_id,
                    replica_index, status
                ) VALUES ('missing', 'missing', 999, 0, 'planned')
                """
            )

    def test_replica_identity_is_unique_per_configuration_and_instance(self):
        instance_id = self._insert_campaign_graph()
        values = ("fixture", "pso-fixture", instance_id, 0, "planned")
        sql = """
            INSERT INTO runs (
                campaign_id, configuration_id, instance_id,
                replica_index, status
            ) VALUES (?, ?, ?, ?, ?)
        """
        self.connection.execute(sql, values)
        with self.assertRaises(sqlite3.IntegrityError):
            self.connection.execute(sql, values)

    def test_run_cannot_use_configuration_from_another_campaign(self):
        instance_id = self._insert_campaign_graph()
        self.connection.execute(
            """
            INSERT INTO campaigns (
                campaign_id, name, config_json, config_sha256, code_commit,
                metric_registry_version, schema_version, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            ("other", "Other", "{}", HASH, "abc123", 1, 1, "2026-10-19T00:00:00Z"),
        )
        with self.assertRaises(sqlite3.IntegrityError):
            self.connection.execute(
                """
                INSERT INTO runs (
                    campaign_id, configuration_id, instance_id,
                    replica_index, status
                ) VALUES (?, ?, ?, ?, ?)
                """,
                ("other", "pso-fixture", instance_id, 0, "planned"),
            )

    def test_legacy_campaign_may_keep_seed_null(self):
        instance_id = self._insert_campaign_graph()
        self.connection.execute(
            """
            INSERT INTO runs (
                campaign_id, configuration_id, instance_id,
                replica_index, status
            ) VALUES (?, ?, ?, ?, ?)
            """,
            ("fixture", "pso-fixture", instance_id, 0, "planned"),
        )
        seed = self.connection.execute("SELECT random_seed FROM runs").fetchone()[0]
        self.assertIsNone(seed)

    def test_paired_campaign_enforces_replica_seed_formula(self):
        instance_id = self._insert_campaign_graph()
        self.connection.execute(
            """
            UPDATE campaigns
            SET base_seed = 42,
                seed_protocol = 'paired_by_replica_v1',
                rng_engine = 'numpy_seedsequence_pcg64_v1'
            WHERE campaign_id = 'fixture'
            """
        )
        sql = """
            INSERT INTO runs (
                campaign_id, configuration_id, instance_id,
                replica_index, random_seed, status
            ) VALUES ('fixture', 'pso-fixture', ?, 0, ?, 'planned')
        """
        with self.assertRaisesRegex(sqlite3.IntegrityError, "base_seed"):
            self.connection.execute(sql, (instance_id, 43))
        self.connection.execute(sql, (instance_id, 42))

    def test_metric_value_requires_exactly_one_typed_value(self):
        instance_id = self._insert_campaign_graph()
        self.connection.execute(
            """
            INSERT INTO runs (
                campaign_id, configuration_id, instance_id,
                replica_index, status
            ) VALUES (?, ?, ?, ?, ?)
            """,
            ("fixture", "pso-fixture", instance_id, 0, "planned"),
        )
        run_id = self.connection.execute("SELECT run_id FROM runs").fetchone()[0]
        self.connection.execute(
            "INSERT INTO metric_definitions VALUES (?, ?, ?, ?)",
            ("objective_best", 1, "{}", HASH),
        )

        with self.assertRaises(sqlite3.IntegrityError):
            self.connection.execute(
                """
                INSERT INTO run_metric_values (
                    run_id, metric_id, metric_version, value_real, value_text
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (run_id, "objective_best", 1, 1.0, "duplicate"),
            )

        self.connection.execute(
            """
            INSERT INTO run_metric_values (
                run_id, metric_id, metric_version, value_real
            ) VALUES (?, ?, ?, ?)
            """,
            (run_id, "objective_best", 1, 1.0),
        )

    def test_observed_and_reconstructed_provenance_are_distinct(self):
        instance_id = self._insert_campaign_graph()
        self.connection.execute(
            """
            INSERT INTO runs (
                campaign_id, configuration_id, instance_id,
                replica_index, status
            ) VALUES (?, ?, ?, ?, ?)
            """,
            ("fixture", "pso-fixture", instance_id, 0, "planned"),
        )
        run_id = self.connection.execute("SELECT run_id FROM runs").fetchone()[0]
        self.connection.execute(
            "INSERT INTO metric_definitions VALUES (?, ?, ?, ?)",
            ("inertia_weight", 1, "{}", HASH),
        )
        self.connection.execute(
            """
            INSERT INTO trace_points (
                run_id, checkpoint_index, iteration_index, evaluations
            ) VALUES (?, 0, 0, 20)
            """,
            (run_id,),
        )
        self.connection.execute(
            """
            INSERT INTO trace_metric_values (
                run_id, checkpoint_index, metric_id, metric_version,
                provenance, value_real
            ) VALUES (?, 0, 'inertia_weight', 1, 'reconstructed', 0.9)
            """,
            (run_id,),
        )
        provenance = self.connection.execute(
            "SELECT provenance FROM trace_metric_values"
        ).fetchone()[0]
        self.assertEqual(provenance, "reconstructed")

    def test_registry_snapshots_are_immutable_and_idempotent(self):
        registry = load_metric_registry()
        expected_count = len(registry.metrics)
        self.assertEqual(
            sync_metric_definitions(self.connection, registry), expected_count
        )
        self.assertEqual(sync_metric_definitions(self.connection, registry), 0)
        count = self.connection.execute(
            "SELECT COUNT(*) FROM metric_definitions"
        ).fetchone()[0]
        self.assertEqual(count, expected_count)

    def test_campaign_metric_profile_is_persisted(self):
        self._insert_campaign_graph()
        registry = load_metric_registry()
        resolved = configure_campaign_metrics(
            self.connection, "fixture", registry, "fuzzy"
        )
        stored = self.connection.execute(
            """
            SELECT metric_id, required
            FROM campaign_metrics
            WHERE campaign_id = 'fixture'
            """
        ).fetchall()
        self.assertEqual(len(stored), len(resolved))
        required = {row["metric_id"] for row in stored if row["required"]}
        self.assertEqual(required, set(registry.required_metrics))

    def test_metric_selection_is_frozen_after_campaign_starts(self):
        self._insert_campaign_graph()
        self.connection.execute(
            "UPDATE campaigns SET status = 'running' WHERE campaign_id = 'fixture'"
        )
        with self.assertRaises(MigrationError):
            configure_campaign_metrics(
                self.connection, "fixture", load_metric_registry(), "minimal"
            )


if __name__ == "__main__":
    unittest.main()
