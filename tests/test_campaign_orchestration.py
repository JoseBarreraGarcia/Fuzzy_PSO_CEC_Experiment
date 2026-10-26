from __future__ import annotations

import json
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
import tempfile
import unittest

from afcs.experiments import (
    CampaignOrchestrator,
    CampaignRecoveryRequired,
    ExperimentRunExecutor,
    OptimizerFactory,
    SequentialCampaignOrchestrator,
    parse_campaign_config,
)
from afcs.metrics import load_metric_registry
from afcs.persistence import (
    ExperimentRepository,
    RepositoryError,
    initialize_v2_database,
)
from afcs.experiments.cli import campaign_preview, main


EXAMPLE_PATH = Path("config/campaigns/cec2017_pso_v2.example.json")
FUZZY_EXAMPLE_PATH = Path(
    "config/campaigns/cec2017_pso_fcs_overlap.example.json"
)


def _smoke_config(
    campaign_id: str = "smoke", metrics: str = "minimal", parallel_workers: int = 1
):
    raw = json.loads(EXAMPLE_PATH.read_text(encoding="utf-8"))
    raw["campaign"].update(
        {"id": campaign_id, "name": "Sequential smoke", "replicas": 2, "metrics": metrics}
    )
    raw["problems"] = [
        {"family": "CEC2017", "functions": [1], "dimensions": [10]}
    ]
    raw["execution"]["parallel_workers"] = parallel_workers
    for treatment in raw["treatments"]:
        treatment["parameters"].update(
            {"population_size": 4, "max_iterations": 2}
        )
    return parse_campaign_config(raw, code_commit="test-commit")


class TestSequentialCampaignOrchestrator(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.connection = initialize_v2_database(
            Path(self.temp_dir.name) / "campaign.db"
        )
        self.repository = ExperimentRepository(
            self.connection, load_metric_registry()
        )

    def tearDown(self) -> None:
        self.connection.close()
        self.temp_dir.cleanup()

    def test_plan_and_execute_smoke_campaign_end_to_end(self) -> None:
        loaded = _smoke_config(metrics="optimizer")
        orchestrator = SequentialCampaignOrchestrator(self.repository)

        summary = orchestrator.plan_and_execute(loaded)

        self.assertEqual(summary.executed_now, 4)
        self.assertEqual(summary.completed, 4)
        self.assertEqual(summary.failed, 0)
        self.assertEqual(summary.campaign_status, "completed")
        rows = self.connection.execute(
            """
            SELECT r.random_seed, r.evaluations, r.initial_population_sha256,
                   ac.optimizer_version
            FROM runs AS r
            JOIN algorithm_configurations AS ac
              ON ac.configuration_id = r.configuration_id
             AND ac.campaign_id = r.campaign_id
            ORDER BY r.configuration_id, r.replica_index
            """
        ).fetchall()
        self.assertEqual([row["random_seed"] for row in rows], [42, 43, 42, 43])
        self.assertTrue(all(row["evaluations"] == 12 for row in rows))
        self.assertTrue(all(len(row["initial_population_sha256"]) == 64 for row in rows))
        self.assertTrue(
            all(row["optimizer_version"] == "2.0.0a0-legacy-compatible" for row in rows)
        )
        trace_rows = self.connection.execute(
            """
            SELECT tp.run_id, tp.checkpoint_index, tp.iteration_index,
                   tp.evaluations
            FROM trace_points AS tp
            ORDER BY tp.run_id, tp.checkpoint_index
            """
        ).fetchall()
        self.assertEqual(len(trace_rows), 12)
        first_run_id = trace_rows[0]["run_id"]
        first_run = [row for row in trace_rows if row["run_id"] == first_run_id]
        self.assertEqual(
            [(row["iteration_index"], row["evaluations"]) for row in first_run],
            [(0, 4), (1, 8), (2, 12)],
        )
        inertia_rows = self.connection.execute(
            """
            SELECT checkpoint_index FROM trace_metric_values
            WHERE run_id = ? AND metric_id = 'inertia_weight'
            ORDER BY checkpoint_index
            """,
            (first_run_id,),
        ).fetchall()
        self.assertEqual([row["checkpoint_index"] for row in inertia_rows], [1, 2])

        repeated = orchestrator.execute_pending("smoke")
        self.assertEqual(repeated.executed_now, 0)
        self.assertEqual(repeated.completed, 4)

    def test_resume_executes_only_remaining_planned_runs(self) -> None:
        orchestrator = SequentialCampaignOrchestrator(self.repository)
        persisted = orchestrator.plan(_smoke_config("resume"))
        self.repository.start_campaign("resume")
        first_id = persisted.run_ids[0]
        plan = self.repository.get_planned_run(first_id)
        ExperimentRunExecutor(self.repository).execute(
            first_id, OptimizerFactory().build(plan)
        )

        summary = orchestrator.execute_pending("resume")

        self.assertEqual(summary.executed_now, 3)
        self.assertEqual(summary.completed, 4)
        self.assertEqual(summary.campaign_status, "completed")

    def test_parallel_execution_matches_sequential_scientific_results(self) -> None:
        sequential = CampaignOrchestrator(self.repository).plan_and_execute(
            _smoke_config("sequential-reference", parallel_workers=1)
        )
        self.assertEqual(sequential.completed, 4)
        sequential_rows = self.connection.execute(
            """
            SELECT r.replica_index, ac.configuration_id, r.objective_best,
                   r.solution_json, r.evaluations, r.initial_population_sha256,
                   r.initial_velocity_sha256
            FROM runs AS r JOIN algorithm_configurations AS ac
              ON ac.configuration_id = r.configuration_id
            WHERE r.campaign_id = 'sequential-reference'
            ORDER BY ac.configuration_id, r.replica_index
            """
        ).fetchall()
        sequential_trace = self.connection.execute(
            """
            SELECT r.replica_index, r.configuration_id, tp.checkpoint_index,
                   tp.iteration_index, tp.evaluations, tmv.metric_id,
                   tmv.value_real, tmv.value_integer, tmv.value_text, tmv.value_json
            FROM trace_points AS tp
            JOIN runs AS r ON r.run_id = tp.run_id
            LEFT JOIN trace_metric_values AS tmv
              ON tmv.run_id = tp.run_id
             AND tmv.checkpoint_index = tp.checkpoint_index
            WHERE r.campaign_id = 'sequential-reference'
            ORDER BY r.configuration_id, r.replica_index,
                     tp.checkpoint_index, tmv.metric_id
            """
        ).fetchall()

        parallel_connection = initialize_v2_database(
            Path(self.temp_dir.name) / "parallel.db"
        )
        try:
            parallel_repository = ExperimentRepository(
                parallel_connection, load_metric_registry()
            )
            parallel = CampaignOrchestrator(parallel_repository).plan_and_execute(
                _smoke_config("parallel-reference", parallel_workers=2)
            )
            self.assertEqual(parallel.completed, 4)
            parallel_rows = parallel_connection.execute(
                """
                SELECT r.replica_index, ac.configuration_id, r.objective_best,
                       r.solution_json, r.evaluations, r.initial_population_sha256,
                       r.initial_velocity_sha256
                FROM runs AS r JOIN algorithm_configurations AS ac
                  ON ac.configuration_id = r.configuration_id
                WHERE r.campaign_id = 'parallel-reference'
                ORDER BY ac.configuration_id, r.replica_index
                """
            ).fetchall()
            self.assertEqual(
                [tuple(row) for row in parallel_rows],
                [tuple(row) for row in sequential_rows],
            )
            parallel_trace = parallel_connection.execute(
                """
                SELECT r.replica_index, r.configuration_id, tp.checkpoint_index,
                       tp.iteration_index, tp.evaluations, tmv.metric_id,
                       tmv.value_real, tmv.value_integer, tmv.value_text, tmv.value_json
                FROM trace_points AS tp
                JOIN runs AS r ON r.run_id = tp.run_id
                LEFT JOIN trace_metric_values AS tmv
                  ON tmv.run_id = tp.run_id
                 AND tmv.checkpoint_index = tp.checkpoint_index
                WHERE r.campaign_id = 'parallel-reference'
                ORDER BY r.configuration_id, r.replica_index,
                         tp.checkpoint_index, tmv.metric_id
                """
            ).fetchall()
            self.assertEqual(
                [tuple(row) for row in parallel_trace],
                [tuple(row) for row in sequential_trace],
            )
        finally:
            parallel_connection.close()

    def test_fuzzy_campaign_executes_and_persists_controller_diagnostics(self) -> None:
        raw = json.loads(FUZZY_EXAMPLE_PATH.read_text(encoding="utf-8"))
        raw["campaign"].update({"id": "fuzzy-smoke", "replicas": 1})
        raw["treatments"] = [raw["treatments"][0]]
        raw["treatments"][0]["parameters"].update(
            {"population_size": 4, "max_iterations": 2}
        )
        loaded = parse_campaign_config(raw, code_commit="test-commit")

        summary = SequentialCampaignOrchestrator(
            self.repository
        ).plan_and_execute(loaded)

        self.assertEqual(summary.completed, 1)
        self.assertEqual(summary.failed, 0)
        recorded = self.connection.execute(
            """
            SELECT metric_id, checkpoint_index
            FROM trace_metric_values
            WHERE metric_id IN (
                'progress_ratio', 'fuzzy_input_diversity',
                'fuzzy_boundary_event_count', 'fuzzy_no_activation_count',
                'fuzzy_fallback_count'
            )
            ORDER BY metric_id, checkpoint_index
            """
        ).fetchall()
        by_metric = {}
        for row in recorded:
            by_metric.setdefault(row["metric_id"], []).append(
                row["checkpoint_index"]
            )
        self.assertEqual(
            set(by_metric),
            {
                "progress_ratio",
                "fuzzy_input_diversity",
                "fuzzy_boundary_event_count",
                "fuzzy_no_activation_count",
                "fuzzy_fallback_count",
            },
        )
        self.assertTrue(all(points == [1, 2] for points in by_metric.values()))
        run_metrics = self.connection.execute(
            """
            SELECT metric_id, value_real, value_integer
            FROM run_metric_values
            WHERE metric_id LIKE 'fuzzy_%'
            """
        ).fetchall()
        persisted = {row["metric_id"]: row for row in run_metrics}
        self.assertEqual(persisted["fuzzy_inference_call_count"]["value_integer"], 2)
        self.assertEqual(persisted["fuzzy_evaluated_rule_count"]["value_integer"], 18)
        self.assertEqual(persisted["fuzzy_skipped_rule_count"]["value_integer"], 0)
        self.assertGreaterEqual(
            persisted["fuzzy_runtime_total_seconds"]["value_real"], 0.0
        )
        self.assertEqual(persisted["fuzzy_no_activation_count"]["value_integer"], 0)
        self.assertEqual(persisted["fuzzy_fallback_count"]["value_integer"], 0)

    def test_classical_deterministic_and_stochastic_functions_execute(self) -> None:
        raw = json.loads(EXAMPLE_PATH.read_text(encoding="utf-8"))
        raw["campaign"].update(
            {"id": "classical-smoke", "replicas": 1, "metrics": "minimal"}
        )
        raw["problems"] = [
            {"family": "CLASSICAL", "functions": [1, 7], "dimensions": [5]}
        ]
        for treatment in raw["treatments"]:
            treatment["parameters"].update(
                {"population_size": 4, "max_iterations": 1}
            )

        summary = CampaignOrchestrator(self.repository).plan_and_execute(
            parse_campaign_config(raw, code_commit="test-commit")
        )

        self.assertEqual(summary.completed, 4)
        rows = self.connection.execute(
            """
            SELECT pi.problem_family, pi.name, r.random_seed, r.evaluations
            FROM runs AS r
            JOIN problem_instances AS pi ON pi.instance_id = r.instance_id
            WHERE r.campaign_id = 'classical-smoke'
            ORDER BY pi.name, r.configuration_id
            """
        ).fetchall()
        self.assertEqual({row["problem_family"] for row in rows}, {"CLASSICAL"})
        self.assertEqual({row["name"] for row in rows}, {"F1", "F7"})
        self.assertTrue(all(row["random_seed"] == 42 for row in rows))
        self.assertTrue(all(row["evaluations"] == 8 for row in rows))

    def test_stale_running_run_requires_explicit_recovery(self) -> None:
        orchestrator = SequentialCampaignOrchestrator(self.repository)
        persisted = orchestrator.plan(_smoke_config("stale"))
        self.repository.start_campaign("stale")
        self.repository.start_run(persisted.run_ids[0])

        with self.assertRaisesRegex(CampaignRecoveryRequired, "explicit recovery"):
            orchestrator.execute_pending("stale")

        recovered = orchestrator.recover_interrupted(
            "stale",
            (persisted.run_ids[0],),
            "test process was intentionally interrupted",
        )
        self.assertEqual(recovered.running, 0)
        self.assertEqual(recovered.planned, 4)

        completed = orchestrator.execute_pending("stale")
        self.assertEqual(completed.completed, 4)
        self.assertEqual(completed.campaign_status, "completed")

    def test_recovery_of_multiple_runs_is_atomic(self) -> None:
        orchestrator = SequentialCampaignOrchestrator(self.repository)
        persisted = orchestrator.plan(_smoke_config("atomic-recovery"))
        self.repository.start_campaign("atomic-recovery")
        self.repository.start_run(persisted.run_ids[0])

        with self.assertRaises(RepositoryError):
            orchestrator.recover_interrupted(
                "atomic-recovery",
                (persisted.run_ids[0], persisted.run_ids[1]),
                "atomic recovery test",
            )

        statuses = self.connection.execute(
            "SELECT status FROM runs ORDER BY run_id"
        ).fetchall()
        self.assertEqual(statuses[0]["status"], "running")
        self.assertEqual(statuses[1]["status"], "planned")

    def test_multiple_run_cancellation_is_not_executed(self) -> None:
        orchestrator = SequentialCampaignOrchestrator(self.repository)
        persisted = orchestrator.plan(_smoke_config("cancel-runs"))
        self.repository.start_campaign("cancel-runs")
        self.repository.start_run(persisted.run_ids[0])

        summary = orchestrator.cancel_runs(
            "cancel-runs",
            (persisted.run_ids[0], persisted.run_ids[1]),
            "operator reduced the validated scope",
        )
        self.assertEqual(summary.cancelled, 2)
        self.assertEqual(summary.running, 0)
        completed = orchestrator.execute_pending("cancel-runs")
        self.assertEqual(completed.completed, 2)
        self.assertEqual(completed.cancelled, 2)
        self.assertEqual(completed.campaign_status, "completed")

    def test_preview_is_read_only_and_reports_budget(self) -> None:
        preview = campaign_preview(_smoke_config("preview"))

        self.assertEqual(preview["summary"]["total_runs"], 4)
        self.assertEqual(preview["summary"]["total_evaluations"], 48)
        self.assertEqual(preview["randomness"]["base_seed"], 42)
        self.assertEqual(preview["trace"]["every_iterations"], 1)

    def test_cli_separates_preview_plan_and_run(self) -> None:
        raw = json.loads(EXAMPLE_PATH.read_text(encoding="utf-8"))
        raw["campaign"].update(
            {"id": "cli-smoke", "replicas": 1, "metrics": "minimal"}
        )
        raw["problems"] = [
            {"family": "CEC2017", "functions": [1], "dimensions": [10]}
        ]
        raw["treatments"] = [raw["treatments"][0]]
        raw["treatments"][0]["parameters"].update(
            {"population_size": 4, "max_iterations": 1}
        )
        config_path = Path(self.temp_dir.name) / "smoke.json"
        config_path.write_text(json.dumps(raw), encoding="utf-8")
        database_path = Path(self.temp_dir.name) / "cli.db"
        output = StringIO()

        with redirect_stdout(output):
            self.assertEqual(
                main(
                    [
                        "plan",
                        "--config",
                        str(config_path),
                        "--code-commit",
                        "test-commit",
                        "--database",
                        str(database_path),
                    ]
                ),
                0,
            )
        self.assertEqual(json.loads(output.getvalue())["planned_runs"], 1)

        cli_connection = initialize_v2_database(database_path)
        try:
            cli_repository = ExperimentRepository(
                cli_connection, load_metric_registry()
            )
            cli_repository.start_campaign("cli-smoke")
            run_id = cli_repository.run_ids_by_status("cli-smoke", "planned")[0]
            cli_repository.start_run(run_id)
        finally:
            cli_connection.close()

        output = StringIO()
        with redirect_stdout(output):
            self.assertEqual(
                main(
                    [
                        "recover",
                        "--database",
                        str(database_path),
                        "--campaign-id",
                        "cli-smoke",
                        "--run-id",
                        str(run_id),
                        "--reason",
                        "intentional CLI recovery test",
                    ]
                ),
                0,
            )
        recovered = json.loads(output.getvalue())
        self.assertEqual(recovered["planned"], 1)
        self.assertEqual(recovered["running"], 0)

        output = StringIO()
        with redirect_stdout(output):
            self.assertEqual(
                main(
                    [
                        "run",
                        "--database",
                        str(database_path),
                        "--campaign-id",
                        "cli-smoke",
                    ]
                ),
                0,
            )
        self.assertEqual(json.loads(output.getvalue())["completed"], 1)

        output = StringIO()
        with redirect_stdout(output):
            self.assertEqual(
                main(
                    [
                        "audit",
                        "--database",
                        str(database_path),
                        "--campaign-id",
                        "cli-smoke",
                    ]
                ),
                0,
            )
        audit = json.loads(output.getvalue())
        self.assertTrue(audit["is_valid"])
        self.assertEqual(audit["run_count"], 1)


if __name__ == "__main__":
    unittest.main()
