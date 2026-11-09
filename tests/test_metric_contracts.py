import json
import sqlite3
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from afcs.analysis import AnalysisExportError, export_campaign_csv
from afcs.experiments import (
    CampaignPlanner,
    ExperimentRunExecutor,
    OptimizerFactory,
    parse_campaign_config,
)
from afcs.metrics import MetricRegistryError, load_metric_registry
from afcs.persistence import (
    ExperimentRepository,
    RepositoryError,
    apply_migrations,
    audit_campaign_integrity,
    sync_metric_definitions,
)


class TestMetricContracts(unittest.TestCase):
    def setUp(self):
        self.connection = sqlite3.connect(":memory:")
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys=ON")
        self.addCleanup(self.connection.close)
        apply_migrations(self.connection)
        self.registry = load_metric_registry()
        self.repository = ExperimentRepository(self.connection, self.registry)

    def prepare(self, selection="minimal", campaign_id="metrics", replicas=1):
        self.repository.create_campaign(campaign_id, "Metrics", {}, "test", selection)
        instance = self.repository.add_problem_instance("test", "sphere", 2)
        self.repository.add_algorithm_configuration(
            campaign_id,
            campaign_id,
            "PSO",
            "test",
            {},
            "evaluations",
            budget_evaluations=8,
        )
        runs = [
            self.repository.plan_run(campaign_id, campaign_id, instance, index)
            for index in range(replicas)
        ]
        self.repository.start_campaign(campaign_id)
        run = runs[0]
        self.repository.start_run(run)
        return run

    def test_historical_definitions_remain_readable_but_are_not_selectable(self):
        historical = {"legacy_gap_percent", "legacy_rdp_percent"}
        self.assertTrue(historical <= self.registry.metrics.keys())
        self.assertFalse(historical.intersection(self.registry.resolve("all")))
        for metric in historical:
            for selection in ([metric], {"include": [metric]}):
                with self.subTest(selection=selection):
                    with self.assertRaisesRegex(MetricRegistryError, "not available"):
                        self.registry.resolve(selection)
                    with self.assertRaisesRegex(MetricRegistryError, "not available"):
                        self.repository.create_campaign(
                            "invalid", "invalid", {}, "test", selection
                        )
        self.assertEqual(
            self.connection.execute("SELECT COUNT(*) FROM campaigns").fetchone()[0], 0
        )
        raw = json.loads(
            Path("config")
            .joinpath("campaigns", "cec2017_pso_v2.example.json")
            .read_text(encoding="utf-8")
        )
        raw["campaign"]["metrics"] = ["legacy_gap_percent"]
        with self.assertRaisesRegex(ValueError, "not available"):
            parse_campaign_config(raw, code_commit="test")

    def test_registry_drift_is_rejected_before_start_or_write(self):
        run = self.prepare()
        definitions = dict(self.registry.metrics)
        definitions["objective_best"] = replace(
            definitions["objective_best"], version=2, unit="changed"
        )
        newer = replace(self.registry, metrics=definitions)
        sync_metric_definitions(self.connection, newer)
        self.connection.commit()
        repository = ExperimentRepository(self.connection, newer)
        for operation in (
            lambda: repository.selected_metric_ids("metrics"),
            lambda: repository.record_trace(run, 0, 0, 8, {"objective_best": 1.0}),
            lambda: repository.complete_run(
                run, 1.0, [0.0, 0.0], 8, 0.01, metrics={"objective_best": 1.0}
            ),
        ):
            with self.assertRaisesRegex(RepositoryError, "definition mismatch"):
                operation()
        self.assertEqual(
            self.connection.execute("SELECT COUNT(*) FROM trace_points").fetchone()[0],
            0,
        )
        self.assertEqual(self.repository.run_status(run), "running")

    def test_same_version_changed_definition_is_also_rejected(self):
        run = self.prepare()
        definitions = dict(self.registry.metrics)
        definitions["objective_best"] = replace(
            definitions["objective_best"], unit="changed"
        )
        repository = ExperimentRepository(
            self.connection, replace(self.registry, metrics=definitions)
        )
        with self.assertRaisesRegex(RepositoryError, "definition mismatch"):
            repository.complete_run(
                run, 1.0, [0.0, 0.0], 8, 0.01, metrics={"objective_best": 1.0}
            )

    def test_missing_objective_is_rejected_without_fabrication_or_partial_completion(
        self,
    ):
        run = self.prepare()
        with self.assertRaisesRegex(RepositoryError, "required.*objective_best"):
            self.repository.complete_run(run, 1.0, [0.0, 0.0], 8, 0.01)
        self.assertEqual(self.repository.run_status(run), "running")
        self.assertEqual(
            self.connection.execute(
                "SELECT COUNT(*) FROM run_metric_values"
            ).fetchone()[0],
            0,
        )
        with self.assertRaisesRegex(RepositoryError, "required.*objective_best"):
            self.repository.record_trace(run, 0, 0, 8, {})
        self.assertEqual(
            self.connection.execute("SELECT COUNT(*) FROM trace_points").fetchone()[0],
            0,
        )

    def test_structural_fields_are_not_duplicated_and_inapplicable_metrics_stay_absent(
        self,
    ):
        run = self.prepare("all")
        self.repository.complete_run(
            run, 1.0, [0.0, 0.0], 8, 0.01, metrics={"objective_best": 1.0}
        )
        self.repository.record_completed_run_metrics(
            run, {"persistence_total_seconds": 0.01, "run_wall_total_seconds": 0.02}
        )
        report = audit_campaign_integrity(self.connection, "metrics")
        self.assertTrue(report.is_valid, report.issues)
        metrics = self.connection.execute(
            "SELECT metric_id FROM run_metric_values"
        ).fetchall()
        self.assertEqual(
            {row[0] for row in metrics},
            {"objective_best", "persistence_total_seconds", "run_wall_total_seconds"},
        )

    def test_missing_required_custom_metric_is_checked_from_persisted_contract(self):
        self.registry = replace(
            self.registry,
            required_metrics=self.registry.required_metrics + ("objective_mean",),
        )
        self.repository = ExperimentRepository(self.connection, self.registry)
        run = self.prepare()
        with self.assertRaisesRegex(RepositoryError, "required.*objective_mean"):
            self.repository.record_trace(run, 0, 0, 8, {"objective_best": 1.0})

    def test_sql_version_mismatch_is_detected_by_auditor_and_export(self):
        run = self.prepare()
        self.repository.record_trace(run, 0, 0, 8, {"objective_best": 1.0})
        self.repository.complete_run(
            run, 1.0, [0.0, 0.0], 8, 0.01, metrics={"objective_best": 1.0}
        )
        definitions = dict(self.registry.metrics)
        definitions["objective_best"] = replace(
            definitions["objective_best"], version=2
        )
        sync_metric_definitions(
            self.connection, replace(self.registry, metrics=definitions)
        )
        for table in ("run_metric_values", "trace_metric_values"):
            self.connection.execute(
                f"UPDATE {table} SET metric_version=2 WHERE metric_id='objective_best'"
            )
        self.connection.commit()
        issues = audit_campaign_integrity(self.connection, "metrics").issues
        self.assertEqual(
            sum(issue.code == "metric_version_mismatch" for issue in issues), 2
        )
        with tempfile.TemporaryDirectory() as directory:
            runs = Path(directory) / "runs.csv"
            with self.assertRaisesRegex(AnalysisExportError, "metric_version_mismatch"):
                export_campaign_csv(
                    self.connection, "metrics", runs, Path(directory) / "traces.csv"
                )
            self.assertFalse(runs.exists())

    def test_missing_observation_blocks_audit_export_and_seal_even_with_waiver(self):
        run = self.prepare(replicas=2)
        self.repository.record_trace(run, 0, 0, 8, {"objective_best": 1.0})
        self.repository.complete_run(
            run, 1.0, [0.0, 0.0], 8, 0.01, metrics={"objective_best": 1.0}
        )
        failed = self.repository.run_ids_by_status("metrics", "planned")[0]
        self.repository.start_run(failed)
        self.repository.fail_run(failed, "SyntheticFailure", "No result")
        self.repository.finish_campaign("metrics")
        self.connection.execute("DELETE FROM run_metric_values")
        self.connection.execute("DELETE FROM trace_metric_values")
        self.connection.commit()
        issues = audit_campaign_integrity(self.connection, "metrics").issues
        self.assertIn("missing_required_metric", {issue.code for issue in issues})
        with self.assertRaisesRegex(RepositoryError, "required"):
            self.repository.seal_campaign(
                "metrics", waiver_reason="Failure acknowledged"
            )
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(AnalysisExportError, "required"):
                export_campaign_csv(
                    self.connection,
                    "metrics",
                    Path(directory) / "runs.csv",
                    Path(directory) / "traces.csv",
                )

    def test_partial_or_failed_run_does_not_require_fabricated_terminal_metrics(self):
        run = self.prepare()
        self.assertTrue(audit_campaign_integrity(self.connection, "metrics").is_valid)
        self.repository.fail_run(run, "SyntheticFailure", "No result was observed")
        self.assertTrue(audit_campaign_integrity(self.connection, "metrics").is_valid)
        self.assertEqual(
            self.connection.execute(
                "SELECT COUNT(*) FROM run_metric_values"
            ).fetchone()[0],
            0,
        )

    def test_bad_checkpoint_blocks_completion_before_mutating_an_external_transaction(
        self,
    ):
        run = self.prepare()
        self.repository.record_trace(run, 0, 0, 8, {"objective_best": 1.0})
        self.connection.execute("DELETE FROM trace_metric_values")
        with self.assertRaisesRegex(RepositoryError, "required.*objective_best"):
            self.repository.complete_run(
                run, 1.0, [0.0, 0.0], 8, 0.01, metrics={"objective_best": 1.0}
            )
        self.assertTrue(self.connection.in_transaction)
        self.assertEqual(self.repository.run_status(run), "running")
        self.assertEqual(
            self.connection.execute(
                "SELECT status FROM run_attempts WHERE run_id=?", (run,)
            ).fetchone()[0],
            "running",
        )
        self.assertEqual(
            self.connection.execute(
                "SELECT COUNT(*) FROM run_metric_values"
            ).fetchone()[0],
            0,
        )
        self.connection.rollback()
        self.assertEqual(
            self.connection.execute(
                "SELECT COUNT(*) FROM trace_metric_values"
            ).fetchone()[0],
            1,
        )

    def test_registry_drift_blocks_campaign_start_without_changing_planned_state(self):
        self.repository.create_campaign("planned", "Planned", {}, "test")
        instance = self.repository.add_problem_instance("test", "sphere", 2)
        self.repository.add_algorithm_configuration(
            "planned", "planned", "PSO", "test", {}, "evaluations", budget_evaluations=8
        )
        run = self.repository.plan_run("planned", "planned", instance, 0)
        definitions = dict(self.registry.metrics)
        definitions["objective_best"] = replace(
            definitions["objective_best"], version=2
        )
        repository = ExperimentRepository(
            self.connection, replace(self.registry, metrics=definitions)
        )
        with self.assertRaisesRegex(RepositoryError, "definition mismatch"):
            repository.start_campaign("planned")
        self.assertEqual(repository.campaign_status("planned"), "draft")
        self.assertEqual(repository.run_status(run), "planned")
        self.assertEqual(
            self.connection.execute("SELECT COUNT(*) FROM run_attempts").fetchone()[0],
            0,
        )

    def test_selected_definition_tampering_blocks_audit_export_and_writes(self):
        run = self.prepare()
        self.connection.execute(
            "UPDATE metric_definitions SET definition_sha256=? WHERE metric_id='objective_best'",
            ("0" * 64,),
        )
        self.connection.commit()
        with self.assertRaisesRegex(RepositoryError, "hash mismatch"):
            self.repository.record_trace(run, 0, 0, 8, {"objective_best": 1.0})
        report = audit_campaign_integrity(self.connection, "metrics")
        self.assertIn(
            "invalid_metric_contract", {issue.code for issue in report.issues}
        )
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(AnalysisExportError, "invalid_metric_contract"):
                export_campaign_csv(
                    self.connection,
                    "metrics",
                    Path(directory) / "runs.csv",
                    Path(directory) / "traces.csv",
                )

    def test_custom_required_metrics_respect_optimizer_fuzzy_and_initial_applicability(
        self,
    ):
        from afcs.persistence.metric_contracts import (
            required_value_ids,
            selected_metric_contract,
        )

        required = ("inertia_weight", "mutation_probability", "fuzzy_output_normalized")
        registry = replace(
            self.registry, required_metrics=self.registry.required_metrics + required
        )
        repository = ExperimentRepository(self.connection, registry)
        repository.create_campaign("applicable", "Applicable", {}, "test")
        contract = selected_metric_contract(self.connection, "applicable")
        ga = required_value_ids(
            contract, "iteration", algorithm="GA", parameters={}, iteration=1
        )
        self.assertNotIn("inertia_weight", ga)
        self.assertNotIn("fuzzy_output_normalized", ga)
        self.assertIn("mutation_probability", ga)
        pso = required_value_ids(
            contract, "iteration", algorithm="PSO", parameters={}, iteration=1
        )
        self.assertIn("inertia_weight", pso)
        self.assertNotIn("mutation_probability", pso)
        self.assertNotIn("fuzzy_output_normalized", pso)
        params = {"inertia_policy": {"policy_id": "fuzzy_inertia_mamdani"}}
        initial = required_value_ids(
            contract, "iteration", algorithm="PSO", parameters=params, iteration=0
        )
        inferred = required_value_ids(
            contract, "iteration", algorithm="PSO", parameters=params, iteration=1
        )
        self.assertNotIn("fuzzy_output_normalized", initial)
        self.assertNotIn("inertia_weight", initial)
        ga_initial = required_value_ids(
            contract, "iteration", algorithm="GA", parameters={}, iteration=0
        )
        self.assertNotIn("mutation_probability", ga_initial)
        self.assertIn("fuzzy_output_normalized", inferred)

    def test_builtin_pso_ga_and_fcs_materialize_objective_with_and_without_traces(self):
        for filename in (
            "cec2017_pso_v2.example.json",
            "real_coded_ga_v2.example.json",
            "cec2017_pso_fcs_overlap.example.json",
        ):
            for enabled in (False, True):
                raw = json.loads(
                    Path("config")
                    .joinpath("campaigns", filename)
                    .read_text(encoding="utf-8")
                )
                campaign_id = f"{filename}-{enabled}"
                raw["campaign"].update(id=campaign_id, replicas=1, metrics="all")
                raw["problems"] = [
                    {"family": "CLASSICAL", "functions": [1], "dimensions": [2]}
                ]
                raw["treatments"] = raw["treatments"][:1]
                raw["treatments"][0]["parameters"].update(
                    population_size=4, max_iterations=1
                )
                raw["trace"]["enabled"] = enabled
                loaded = parse_campaign_config(raw, code_commit="test")
                plan = CampaignPlanner(self.repository).persist(
                    loaded.campaign, loaded.treatments
                )
                self.repository.start_campaign(campaign_id)
                run = plan.run_ids[0]
                optimizer = OptimizerFactory().build(
                    self.repository.get_planned_run(run),
                    selected_metrics=self.repository.selected_metric_ids(campaign_id),
                )
                result = ExperimentRunExecutor(self.repository).execute(run, optimizer)
                row = self.connection.execute(
                    "SELECT value_real,provenance FROM run_metric_values "
                    "WHERE run_id=? AND metric_id='objective_best'",
                    (run,),
                ).fetchone()
                self.assertEqual(tuple(row), (result.best_objective, "observed"))
                self.assertEqual(len(result.trace_points), 2 if enabled else 0)
                report = audit_campaign_integrity(self.connection, campaign_id)
                self.assertTrue(report.is_valid, report.issues)
