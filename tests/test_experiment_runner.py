from dataclasses import dataclass
import json
from pathlib import Path
import tempfile
import unittest

import numpy as np

from afcs.core import SearchSpace
from afcs.experiments import ExperimentRunExecutor
from afcs.metrics import load_metric_registry
from afcs.optimizers.pso import FixedInertia, LegacyCompatiblePSO, LegacyPSORunConfig
from afcs.persistence import ExperimentRepository, initialize_v2_database
from afcs.problems import CallableProblem, ProblemMetadata


class Clock:
    def __init__(self, *values: float) -> None:
        self._values = iter(values)

    def __call__(self) -> float:
        return next(self._values)


@dataclass
class FailingOptimizer:
    message: str = "synthetic failure"

    def run(self):
        raise FloatingPointError(self.message)


class TestExperimentRunExecutor(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.connection = initialize_v2_database(
            Path(self.temp_dir.name) / "runner.db"
        )
        self.repository = ExperimentRepository(
            self.connection, load_metric_registry()
        )
        self.repository.create_campaign(
            "campaign",
            "Runner integration",
            {"purpose": "test"},
            "test-commit",
            "minimal",
        )
        instance_id = self.repository.add_problem_instance(
            "test", "sphere", 2, 0.0
        )
        self.repository.add_algorithm_configuration(
            "pso-fixed",
            "campaign",
            "PSO",
            {"inertia_policy": "fixed_inertia", "w": 0.6},
            "hybrid",
            budget_evaluations=12,
            budget_iterations=2,
            population_size=4,
        )
        self.run_id = self.repository.plan_run(
            "campaign", "pso-fixed", instance_id, replica_index=0
        )
        self.repository.start_campaign("campaign")

    def tearDown(self):
        self.connection.close()
        self.temp_dir.cleanup()

    def test_real_pso_result_is_persisted_without_seed_assignment(self):
        problem = CallableProblem(
            ProblemMetadata(
                problem_id="sphere",
                family="test",
                search_space=SearchSpace.uniform(2, -5.0, 5.0),
                known_optimum=0.0,
            ),
            lambda candidate: sum(value * value for value in candidate),
        )
        optimizer = LegacyCompatiblePSO(
            problem=problem,
            config=LegacyPSORunConfig(population_size=4, max_iterations=2),
            inertia_policy=FixedInertia(0.6),
            rng=np.random.default_rng(123),
        )

        result = ExperimentRunExecutor(
            self.repository, clock=Clock(10.0, 10.25)
        ).execute(self.run_id, optimizer)

        row = self.connection.execute(
            "SELECT * FROM runs WHERE run_id = ?", (self.run_id,)
        ).fetchone()
        self.assertEqual(row["status"], "completed")
        self.assertEqual(row["evaluations"], 12)
        self.assertEqual(row["runtime_total_seconds"], 0.25)
        self.assertIsNone(row["random_seed"])
        self.assertEqual(json.loads(row["solution_json"]), result.best_position.tolist())
        self.assertEqual(row["objective_best"], result.best_objective)

    def test_optimizer_failure_is_persisted_and_reraised(self):
        executor = ExperimentRunExecutor(self.repository, clock=Clock(1.0))
        with self.assertRaisesRegex(FloatingPointError, "synthetic failure"):
            executor.execute(self.run_id, FailingOptimizer())

        row = self.connection.execute(
            "SELECT status, error_type, error_message FROM runs WHERE run_id = ?",
            (self.run_id,),
        ).fetchone()
        self.assertEqual(
            tuple(row),
            ("failed", "FloatingPointError", "synthetic failure"),
        )

    def test_invalid_result_is_recorded_as_failure(self):
        @dataclass
        class InvalidResult:
            best_position: tuple[float, ...] = (0.0, float("nan"))
            best_objective: float = 0.0
            evaluations: int = 12

        class InvalidOptimizer:
            def run(self):
                return InvalidResult()

        executor = ExperimentRunExecutor(self.repository, clock=Clock(1.0))
        with self.assertRaisesRegex(ValueError, "solution coordinate"):
            executor.execute(self.run_id, InvalidOptimizer())

        status = self.connection.execute(
            "SELECT status FROM runs WHERE run_id = ?", (self.run_id,)
        ).fetchone()[0]
        self.assertEqual(status, "failed")


if __name__ == "__main__":
    unittest.main()
