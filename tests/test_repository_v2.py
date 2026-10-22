import tempfile
from pathlib import Path
import unittest

from afcs.metrics import load_metric_registry
from afcs.persistence import (
    ExperimentRepository,
    RepositoryError,
    encode_metric_value,
    initialize_v2_database,
)


class TestExperimentRepository(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.connection = initialize_v2_database(
            Path(self.temp_dir.name) / "repository.db"
        )
        self.registry = load_metric_registry()
        self.repository = ExperimentRepository(self.connection, self.registry)

    def tearDown(self):
        self.connection.close()
        self.temp_dir.cleanup()

    def _prepare_run(self, selection="fuzzy", seed=None):
        self.repository.create_campaign(
            "campaign",
            "Synthetic campaign",
            {"metrics": selection},
            "abc123",
            selection,
            "2026-10-19T00:00:00Z",
        )
        instance_id = self.repository.add_problem_instance("BEN", "F1", 2, 0.0)
        self.repository.add_algorithm_configuration(
            "pso-fuzzy",
            "campaign",
            "PSO_FCS",
            {"w_set": "O1"},
            "hybrid",
            budget_evaluations=100,
            budget_iterations=4,
            population_size=20,
            created_at="2026-10-19T00:00:00Z",
        )
        run_id = self.repository.plan_run(
            "campaign", "pso-fuzzy", instance_id, 0, random_seed=seed
        )
        return run_id

    def test_complete_campaign_lifecycle(self):
        run_id = self._prepare_run(seed=None)
        self.repository.start_campaign("campaign", "2026-10-19T00:01:00Z")
        self.repository.start_run(run_id, "2026-10-19T00:01:01Z")
        self.repository.record_trace(
            run_id,
            checkpoint_index=0,
            iteration_index=0,
            evaluations=20,
            elapsed_seconds=0.01,
            metrics={
                "objective_best": 1.0,
                "diversity_hussain": 2.0,
                "inertia_weight": 0.9,
            },
        )
        self.repository.complete_run(
            run_id,
            objective_best=0.1,
            solution=[0.0, 0.0],
            evaluations=100,
            runtime_total_seconds=0.5,
            feasible=True,
            constraint_violation=0.0,
            metrics={"objective_best": 0.1},
            finished_at="2026-10-19T00:02:00Z",
        )
        self.repository.finish_campaign("campaign", "2026-10-19T00:02:01Z")
        self.repository.seal_campaign("campaign", "2026-10-19T00:02:02Z")

        campaign = self.connection.execute(
            "SELECT status, sealed_at FROM campaigns WHERE campaign_id = 'campaign'"
        ).fetchone()
        run = self.connection.execute(
            "SELECT status, random_seed, objective_best FROM runs WHERE run_id = ?",
            (run_id,),
        ).fetchone()
        self.assertEqual(campaign["status"], "sealed")
        self.assertIsNotNone(campaign["sealed_at"])
        self.assertEqual(run["status"], "completed")
        self.assertIsNone(run["random_seed"])
        self.assertEqual(run["objective_best"], 0.1)

    def test_unselected_metric_is_rejected_without_partial_trace(self):
        run_id = self._prepare_run(selection="minimal")
        self.repository.start_campaign("campaign")
        self.repository.start_run(run_id)
        with self.assertRaises(RepositoryError):
            self.repository.record_trace(
                run_id, 0, 0, 20, {"inertia_weight": 0.9}
            )
        count = self.connection.execute("SELECT COUNT(*) FROM trace_points").fetchone()[0]
        self.assertEqual(count, 0)

    def test_trace_budget_must_be_monotonic(self):
        run_id = self._prepare_run()
        self.repository.start_campaign("campaign")
        self.repository.start_run(run_id)
        self.repository.record_trace(run_id, 0, 0, 20, {"objective_best": 1.0})
        with self.assertRaises(RepositoryError):
            self.repository.record_trace(run_id, 1, 1, 19, {"objective_best": 0.9})

    def test_metric_scope_is_enforced(self):
        run_id = self._prepare_run()
        self.repository.start_campaign("campaign")
        self.repository.start_run(run_id)
        with self.assertRaises(RepositoryError):
            self.repository.complete_run(
                run_id,
                objective_best=0.1,
                solution=[0.0, 0.0],
                evaluations=100,
                runtime_total_seconds=0.5,
                metrics={"population_entropy": 0.2},
            )

    def test_registered_metric_type_is_enforced_without_partial_trace(self):
        run_id = self._prepare_run()
        self.repository.start_campaign("campaign")
        self.repository.start_run(run_id)
        with self.assertRaises(RepositoryError):
            self.repository.record_trace(
                run_id, 0, 0, 20, {"objective_best": {"not": "a float"}}
            )
        count = self.connection.execute("SELECT COUNT(*) FROM trace_points").fetchone()[0]
        self.assertEqual(count, 0)

    def test_campaign_cannot_finish_with_running_run(self):
        run_id = self._prepare_run()
        self.repository.start_campaign("campaign")
        self.repository.start_run(run_id)
        with self.assertRaises(RepositoryError):
            self.repository.finish_campaign("campaign")

    def test_no_runs_can_be_planned_after_campaign_starts(self):
        self._prepare_run()
        self.repository.start_campaign("campaign")
        instance_id = self.connection.execute(
            "SELECT instance_id FROM problem_instances"
        ).fetchone()[0]
        with self.assertRaises(RepositoryError):
            self.repository.plan_run("campaign", "pso-fuzzy", instance_id, 1)

    def test_failed_run_records_structured_error(self):
        run_id = self._prepare_run()
        self.repository.start_campaign("campaign")
        self.repository.start_run(run_id)
        self.repository.fail_run(run_id, "FloatingPointError", "non-finite fitness")
        row = self.connection.execute(
            "SELECT status, error_type, error_message FROM runs WHERE run_id = ?",
            (run_id,),
        ).fetchone()
        self.assertEqual(tuple(row), ("failed", "FloatingPointError", "non-finite fitness"))

    def test_metric_value_encoding_is_typed_and_rejects_non_finite(self):
        self.assertEqual(encode_metric_value(True).value_integer, 1)
        self.assertEqual(encode_metric_value(3).value_integer, 3)
        self.assertEqual(encode_metric_value(0.5).value_real, 0.5)
        self.assertEqual(encode_metric_value("ok").value_text, "ok")
        self.assertEqual(encode_metric_value({"rule": 1}).value_json, '{"rule":1}')
        with self.assertRaises(RepositoryError):
            encode_metric_value(float("nan"))


if __name__ == "__main__":
    unittest.main()
