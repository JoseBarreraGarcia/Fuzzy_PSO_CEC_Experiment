from __future__ import annotations

import json
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
import tempfile
import unittest

from afcs.experiments import (
    CampaignRecoveryRequired,
    ExperimentRunExecutor,
    OptimizerFactory,
    SequentialCampaignOrchestrator,
    parse_campaign_config,
)
from afcs.metrics import load_metric_registry
from afcs.persistence import ExperimentRepository, initialize_v2_database
from afcs.experiments.cli import campaign_preview, main


EXAMPLE_PATH = Path("config/campaigns/cec2017_pso_v2.example.json")


def _smoke_config(campaign_id: str = "smoke", metrics: str = "minimal"):
    raw = json.loads(EXAMPLE_PATH.read_text(encoding="utf-8"))
    raw["campaign"].update(
        {"id": campaign_id, "name": "Sequential smoke", "replicas": 2, "metrics": metrics}
    )
    raw["problems"] = [
        {"family": "CEC2017", "functions": [1], "dimensions": [10]}
    ]
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

    def test_stale_running_run_requires_explicit_recovery(self) -> None:
        orchestrator = SequentialCampaignOrchestrator(self.repository)
        persisted = orchestrator.plan(_smoke_config("stale"))
        self.repository.start_campaign("stale")
        self.repository.start_run(persisted.run_ids[0])

        with self.assertRaisesRegex(CampaignRecoveryRequired, "explicit recovery"):
            orchestrator.execute_pending("stale")

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


if __name__ == "__main__":
    unittest.main()
