import json
import sqlite3
import tempfile
import unittest
from contextlib import closing
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

from afcs.analysis import AnalysisExportError, export_campaign_csv
from afcs.experiments import (
    CampaignOrchestrator,
    CampaignPlanner,
    ExperimentRunExecutor,
    OptimizerFactory,
    parse_campaign_config,
)
from afcs.experiments.orchestration import _execute_persisted_run
from afcs.persistence import (
    ExperimentRepository,
    RepositoryError,
    apply_migrations,
    audit_campaign_integrity,
)


def configuration(campaign_id="integrity", metrics="minimal"):
    raw = json.loads(
        Path("config")
        .joinpath("campaigns", "cec2017_pso_v2.example.json")
        .read_text(encoding="utf-8")
    )
    raw["campaign"].update(id=campaign_id, replicas=1, metrics=metrics)
    raw["problems"] = [{"family": "CLASSICAL", "functions": [1], "dimensions": [2]}]
    raw["treatments"] = raw["treatments"][:1]
    raw["treatments"][0]["parameters"].update(population_size=4, max_iterations=1)
    return parse_campaign_config(raw, code_commit="test")


class TestExecutionIntegrity(unittest.TestCase):
    def setUp(self):
        self.connection = sqlite3.connect(":memory:")
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys=ON")
        self.addCleanup(self.connection.close)
        apply_migrations(self.connection)
        from afcs.metrics import load_metric_registry

        self.repository = ExperimentRepository(self.connection, load_metric_registry())

    def prepare(self, metrics="minimal"):
        loaded = configuration(metrics=metrics)
        plan = CampaignPlanner(self.repository).persist(
            loaded.campaign, loaded.treatments
        )
        self.repository.start_campaign("integrity")
        run = plan.run_ids[0]
        optimizer = OptimizerFactory().build(
            self.repository.get_planned_run(run),
            selected_metrics=self.repository.selected_metric_ids("integrity"),
        )
        return run, optimizer

    def execute(self, metrics="minimal"):
        run, optimizer = self.prepare(metrics)
        result = ExperimentRunExecutor(self.repository).execute(run, optimizer)
        return run, result

    def test_postcommit_clock_failure_preserves_result_but_blocks_export_finish_and_seal(
        self,
    ):
        run, optimizer = self.prepare("timing")
        with self.assertRaisesRegex(ValueError, "monotonic"):
            ExperimentRunExecutor(
                self.repository, persistence_clock=iter((10.0, 11.0, 9.0)).__next__
            ).execute(run, optimizer)
        row = self.connection.execute("SELECT * FROM runs").fetchone()
        self.assertEqual(row["status"], "completed")
        self.assertEqual(row["finalization_status"], "failed")
        self.assertEqual(row["finalization_error_type"], "ValueError")
        self.assertIsNotNone(row["objective_best"])
        self.assertEqual(
            self.connection.execute("SELECT status FROM run_attempts").fetchone()[0],
            "completed",
        )
        self.assertIn(
            "run_finalization_failed",
            {
                issue.code
                for issue in audit_campaign_integrity(
                    self.connection, "integrity"
                ).issues
            },
        )
        with self.assertRaises(RepositoryError):
            self.repository.finish_campaign("integrity")
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(AnalysisExportError):
                export_campaign_csv(
                    self.connection,
                    "integrity",
                    Path(directory) / "runs.csv",
                    Path(directory) / "traces.csv",
                )
        self.connection.execute("UPDATE campaigns SET status='completed'")
        self.connection.commit()
        with self.assertRaises(RepositoryError):
            self.repository.seal_campaign("integrity")

    def test_postcommit_write_failure_is_structured_without_rerunning_optimizer(self):
        run, optimizer = self.prepare("timing")
        with patch.object(
            self.repository,
            "record_completed_run_metrics",
            side_effect=RuntimeError("postcommit write failure"),
        ):
            with self.assertRaisesRegex(RuntimeError, "postcommit"):
                ExperimentRunExecutor(self.repository).execute(run, optimizer)
        row = self.connection.execute("SELECT * FROM runs").fetchone()
        self.assertEqual(
            (row["status"], row["finalization_status"]), ("completed", "failed")
        )
        self.assertEqual(row["finalization_error_message"], "postcommit write failure")
        with self.assertRaises(RepositoryError):
            CampaignOrchestrator(self.repository).execute_pending("integrity")
        self.assertEqual(
            self.connection.execute("SELECT COUNT(*) FROM run_attempts").fetchone()[0],
            1,
        )

    def test_interruption_after_result_commit_remains_pending_not_success(self):
        run, optimizer = self.prepare("timing")
        clock = iter((1.0, 2.0))

        def interrupted_clock():
            try:
                return next(clock)
            except StopIteration:
                raise KeyboardInterrupt()

        with self.assertRaises(KeyboardInterrupt):
            ExperimentRunExecutor(
                self.repository, persistence_clock=interrupted_clock
            ).execute(run, optimizer)
        self.assertEqual(
            self.connection.execute("SELECT finalization_status FROM runs").fetchone()[
                0
            ],
            "pending",
        )
        with self.assertRaises(RepositoryError):
            self.repository.finish_campaign("integrity")

    def test_successful_finalization_is_explicit_and_sealed_metrics_are_immutable(self):
        run, _ = self.execute("timing")
        self.assertEqual(
            self.connection.execute("SELECT finalization_status FROM runs").fetchone()[
                0
            ],
            "completed",
        )
        self.repository.finish_campaign("integrity")
        self.repository.seal_campaign("integrity")
        with self.assertRaisesRegex(RepositoryError, "sealed"):
            self.repository.record_completed_run_metrics(run, {"objective_best": 99.0})
        with self.assertRaises(RepositoryError):
            self.repository.fail_run(run, "Error", "must not modify sealed evidence")
        self.assertTrue(audit_campaign_integrity(self.connection, "integrity").is_valid)

    def test_preparation_failure_creates_failed_attempt_and_is_not_retried(self):
        loaded = configuration()
        CampaignPlanner(self.repository).persist(loaded.campaign, loaded.treatments)
        calls = []

        def unavailable(plan, selected):
            calls.append(plan.run_id)
            raise RuntimeError("synthetic resource unavailable")

        orchestrator = CampaignOrchestrator(
            self.repository, optimizer_factory=OptimizerFactory({"PSO": unavailable})
        )
        with self.assertRaisesRegex(RuntimeError, "resource"):
            orchestrator.execute_pending("integrity")
        row = self.connection.execute("SELECT * FROM runs").fetchone()
        self.assertEqual(
            (row["status"], row["failure_phase"]), ("failed", "preparation")
        )
        attempt = self.connection.execute("SELECT * FROM run_attempts").fetchone()
        self.assertEqual(
            (attempt["status"], attempt["failure_phase"]), ("failed", "preparation")
        )
        self.assertEqual(orchestrator.execute_pending("integrity").failed, 1)
        self.assertEqual(len(calls), 1)

    def test_worker_preparation_failure_uses_the_same_auditable_path(self):
        run, _ = self.prepare()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "worker.db"
            destination = sqlite3.connect(path)
            self.connection.backup(destination)
            destination.close()
            with patch.object(
                OptimizerFactory, "build", side_effect=RuntimeError("worker resource")
            ):
                with self.assertRaisesRegex(RuntimeError, "worker resource"):
                    _execute_persisted_run(path, "integrity", run)
            with closing(sqlite3.connect(path)) as reader:
                self.assertEqual(
                    reader.execute("SELECT status,failure_phase FROM runs").fetchone(),
                    ("failed", "preparation"),
                )
                self.assertEqual(
                    reader.execute(
                        "SELECT status,failure_phase FROM run_attempts"
                    ).fetchone(),
                    ("failed", "preparation"),
                )

    def test_wrong_dimension_is_failure_before_result_commit(self):
        run, optimizer = self.prepare()
        result = optimizer.run()
        fake = type(
            "FakeOptimizer",
            (),
            {
                "run_metadata": optimizer.run_metadata,
                "run": lambda self: replace(result, best_position=(0.0,)),
            },
        )()
        with self.assertRaisesRegex(ValueError, "dimension"):
            ExperimentRunExecutor(self.repository).execute(run, fake)
        row = self.connection.execute("SELECT * FROM runs").fetchone()
        self.assertEqual(
            (row["status"], row["failure_phase"]), ("failed", "result_validation")
        )
        self.assertIsNone(row["solution_json"])

    def test_direct_completion_rejects_bad_solution_without_mutation(self):
        run, _ = self.prepare()
        self.repository.start_run(run)
        for solution in ([0.0], [0.0, float("inf")], [[0.0], [0.0]], [True, 0.0]):
            with self.subTest(solution=solution):
                with self.assertRaises(RepositoryError):
                    self.repository.complete_run(
                        run, 0.0, solution, 8, 0.01, metrics={"objective_best": 0.0}
                    )
                self.assertEqual(self.repository.run_status(run), "running")

    def test_trace_worsening_is_rejected_for_both_directions(self):
        for direction, first, worse in (
            ("minimize", 1.0, 100.0),
            ("maximize", 100.0, 1.0),
        ):
            with self.subTest(direction=direction):
                if direction == "minimize":
                    run, _ = self.prepare()
                else:
                    self.connection.execute("DELETE FROM trace_metric_values")
                    self.connection.execute("DELETE FROM trace_points")
                    self.connection.execute(
                        "UPDATE problem_instances SET direction='maximize'"
                    )
                    self.connection.commit()
                if direction == "minimize":
                    self.repository.start_run(run)
                self.repository.record_trace(run, 0, 0, 4, {"objective_best": first})
                with self.assertRaisesRegex(RepositoryError, "best-so-far"):
                    self.repository.record_trace(
                        run, 1, 1, 8, {"objective_best": worse}
                    )

    def test_final_trace_must_equal_result_and_reach_final_budget_when_enabled(self):
        run, _ = self.prepare()
        self.repository.start_run(run)
        self.repository.record_trace(run, 0, 0, 4, {"objective_best": 1.0})
        with self.assertRaises(RepositoryError):
            self.repository.complete_run(
                run, 0.0, [0.0, 0.0], 8, 0.01, metrics={"objective_best": 0.0}
            )
        self.repository.record_trace(run, 1, 1, 8, {"objective_best": 1.0})
        with self.assertRaisesRegex(RepositoryError, "Final.*objective"):
            self.repository.complete_run(
                run, 0.0, [0.0, 0.0], 8, 0.01, metrics={"objective_best": 0.0}
            )
        self.assertEqual(self.repository.run_status(run), "running")

    def test_sql_contradiction_blocks_audit_export_and_seal(self):
        self.execute()
        self.connection.execute(
            "UPDATE trace_metric_values SET value_real=1e100 "
            "WHERE metric_id='objective_best' AND checkpoint_index=1"
        )
        self.connection.commit()
        issues = audit_campaign_integrity(self.connection, "integrity").issues
        self.assertIn("trace_objective_order", {issue.code for issue in issues})
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(AnalysisExportError):
                export_campaign_csv(
                    self.connection,
                    "integrity",
                    Path(directory) / "runs.csv",
                    Path(directory) / "traces.csv",
                )
        self.repository.finish_campaign("integrity")
        with self.assertRaises(RepositoryError):
            self.repository.seal_campaign("integrity")

    def test_missing_attempt_is_not_validated_or_waived(self):
        self.execute()
        self.connection.execute("DELETE FROM run_attempts")
        self.connection.commit()
        report = audit_campaign_integrity(self.connection, "integrity")
        self.assertIn(
            "missing_execution_attempt", {issue.code for issue in report.issues}
        )
        self.repository.finish_campaign("integrity")
        with self.assertRaisesRegex(RepositoryError, "integrity"):
            self.repository.seal_campaign("integrity")

    def test_waiver_cannot_override_missing_failed_attempt(self):
        run, _ = self.prepare()
        self.repository.start_run(run)
        self.repository.fail_run(run, "RuntimeError", "synthetic failure")
        self.connection.execute("DELETE FROM run_attempts")
        self.connection.commit()
        self.repository.finish_campaign("integrity")
        with self.assertRaisesRegex(RepositoryError, "integrity"):
            self.repository.seal_campaign(
                "integrity", waiver_reason="accepted failure, not corruption"
            )
        self.assertEqual(
            self.connection.execute(
                "SELECT COUNT(*) FROM campaign_seal_waivers"
            ).fetchone()[0],
            0,
        )
        self.assertEqual(self.repository.campaign_status("integrity"), "completed")

    def test_planned_cancellation_needs_no_execution_attempt(self):
        run, _ = self.prepare()
        self.repository.cancel_run("integrity", run, "approved exclusion")
        self.repository.finish_campaign("integrity")
        self.repository.seal_campaign("integrity", waiver_reason="accepted exclusion")
        self.assertTrue(audit_campaign_integrity(self.connection, "integrity").is_valid)
        self.assertEqual(
            self.connection.execute("SELECT COUNT(*) FROM run_attempts").fetchone()[0],
            0,
        )

    def test_postcommit_values_cannot_replace_the_scientific_result(self):
        run, _ = self.prepare("timing")
        self.repository.start_run(run)
        self.repository.record_trace(run, 0, 0, 8, {"objective_best": 1.0})
        self.repository.complete_run(
            run, 1.0, [0.0, 0.0], 8, 0.01, metrics={"objective_best": 1.0}
        )
        for metrics in (
            {"objective_best": 100.0},
            {"persistence_total_seconds": 0.01},
            {"persistence_total_seconds": -0.01, "run_wall_total_seconds": 0.02},
            {"persistence_total_seconds": 0.03, "run_wall_total_seconds": 0.02},
        ):
            with self.subTest(metrics=metrics):
                with self.assertRaises(RepositoryError):
                    self.repository.record_completed_run_metrics(run, metrics)
                self.assertEqual(
                    self.connection.execute(
                        "SELECT finalization_status FROM runs"
                    ).fetchone()[0],
                    "pending",
                )
                self.assertEqual(
                    self.connection.execute(
                        "SELECT COUNT(*) FROM run_metric_values"
                    ).fetchone()[0],
                    1,
                )
        self.repository.record_completed_run_metrics(
            run, {"persistence_total_seconds": 0.01, "run_wall_total_seconds": 0.02}
        )
        with self.assertRaises(RepositoryError):
            self.repository.record_completed_run_metrics(
                run, {"persistence_total_seconds": 0.01, "run_wall_total_seconds": 0.02}
            )

    def test_maximization_equality_and_improvement_are_valid(self):
        run, _ = self.prepare()
        self.connection.execute("UPDATE problem_instances SET direction='maximize'")
        self.connection.commit()
        self.repository.start_run(run)
        self.repository.record_trace(run, 0, 0, 4, {"objective_best": 1.0})
        self.repository.record_trace(run, 1, 1, 6, {"objective_best": 1.0})
        self.repository.record_trace(run, 2, 2, 8, {"objective_best": 2.0})
        self.repository.complete_run(
            run, 2.0, [0.0, 0.0], 8, 0.01, metrics={"objective_best": 2.0}
        )
        self.assertTrue(audit_campaign_integrity(self.connection, "integrity").is_valid)

    def test_transaction_rolls_back_interrupt_without_discarding_attempt(self):
        run, _ = self.prepare()
        self.repository.start_run(run)
        with self.assertRaises(KeyboardInterrupt):
            with self.repository.transaction():
                self.repository.record_trace(run, 0, 0, 4, {"objective_best": 1.0})
                raise KeyboardInterrupt()
        self.assertFalse(self.connection.in_transaction)
        self.assertEqual(
            self.connection.execute("SELECT COUNT(*) FROM trace_points").fetchone()[0],
            0,
        )
        self.assertEqual(self.repository.run_status(run), "running")

    def test_executor_rejects_caller_transaction_before_execution_without_committing_it(
        self,
    ):
        run, optimizer = self.prepare()
        self.connection.execute("UPDATE campaigns SET notes='caller-owned'")
        with self.assertRaisesRegex(RepositoryError, "caller transaction"):
            ExperimentRunExecutor(self.repository).execute(run, optimizer)
        self.assertTrue(self.connection.in_transaction)
        self.assertEqual(self.repository.run_status(run), "planned")
        self.assertEqual(
            self.connection.execute("SELECT COUNT(*) FROM run_attempts").fetchone()[0],
            0,
        )
        self.connection.rollback()
        self.assertIsNone(
            self.connection.execute("SELECT notes FROM campaigns").fetchone()[0]
        )

    def test_sql_invalid_solution_and_timing_block_export(self):
        self.execute("timing")
        self.connection.execute("UPDATE runs SET solution_json='[0]'")
        self.connection.execute(
            "UPDATE run_metric_values SET value_real=-1 WHERE metric_id='persistence_total_seconds'"
        )
        self.connection.commit()
        codes = {
            issue.code
            for issue in audit_campaign_integrity(self.connection, "integrity").issues
        }
        self.assertTrue(
            {"invalid_completed_solution", "invalid_post_run_timing"} <= codes
        )
        with self.assertRaises(RepositoryError):
            self.repository.finish_campaign("integrity")
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(AnalysisExportError):
                export_campaign_csv(
                    self.connection,
                    "integrity",
                    Path(directory) / "runs.csv",
                    Path(directory) / "traces.csv",
                )

    def test_sql_nonnumeric_trace_is_an_integrity_issue_not_an_auditor_crash(self):
        self.execute()
        self.connection.execute(
            "UPDATE trace_metric_values SET value_real='invalid' "
            "WHERE metric_id='objective_best' AND checkpoint_index=0"
        )
        self.connection.commit()
        codes = {
            issue.code
            for issue in audit_campaign_integrity(self.connection, "integrity").issues
        }
        self.assertIn("trace_objective_nonfinite", codes)
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(AnalysisExportError):
                export_campaign_csv(
                    self.connection,
                    "integrity",
                    Path(directory) / "runs.csv",
                    Path(directory) / "traces.csv",
                )

    def test_pending_or_absent_selected_timing_is_not_a_valid_completion(self):
        run, optimizer = self.prepare("timing")
        result = optimizer.run()
        self.repository.start_run(run)
        for point in result.trace_points:
            self.repository.record_trace(
                run,
                point.checkpoint_index,
                point.iteration_index,
                point.evaluations,
                point.metrics,
            )
        metrics = {
            key: value
            for key, value in result.run_metrics.items()
            if key in self.repository.selected_metric_ids("integrity")
        }
        self.repository.complete_run(
            run,
            result.best_objective,
            result.best_position.tolist(),
            8,
            0.01,
            metrics=metrics,
        )
        self.assertEqual(
            self.connection.execute("SELECT finalization_status FROM runs").fetchone()[
                0
            ],
            "pending",
        )
        self.assertFalse(
            audit_campaign_integrity(self.connection, "integrity").is_valid
        )
        with self.assertRaises(RepositoryError):
            self.repository.finish_campaign("integrity")
        self.repository.record_completed_run_metrics(
            run, {"persistence_total_seconds": 0.01, "run_wall_total_seconds": 0.02}
        )
        self.assertTrue(audit_campaign_integrity(self.connection, "integrity").is_valid)
