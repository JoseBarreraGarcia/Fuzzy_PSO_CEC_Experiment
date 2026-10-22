from dataclasses import dataclass
import json
from pathlib import Path
import tempfile
import unittest

import numpy as np

from afcs.core import ReplicaRandomStreams, SearchSpace
from afcs.experiments import ExperimentRunExecutor, RunBindingError
from afcs.metrics import load_metric_registry
from afcs.metrics import OptimizationTracePoint
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
    run_metadata: object
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
        self.problem = CallableProblem(
            ProblemMetadata(
                problem_id="sphere",
                family="test",
                search_space=SearchSpace.uniform(2, -5.0, 5.0),
                known_optimum=0.0,
            ),
            lambda candidate: sum(value * value for value in candidate),
        )
        self.config = LegacyPSORunConfig(population_size=4, max_iterations=2)
        self.policy = FixedInertia(0.6)
        metadata = LegacyCompatiblePSO(
            problem=self.problem,
            config=self.config,
            inertia_policy=self.policy,
            rng=np.random.default_rng(0),
        ).run_metadata
        instance_id = self.repository.add_problem_instance(
            "test", "sphere", 2, 0.0
        )
        self.repository.add_algorithm_configuration(
            "pso-fixed",
            "campaign",
            "PSO",
            metadata.optimizer.version,
            dict(metadata.parameters),
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

    def test_seeded_pso_result_and_initial_condition_hashes_are_persisted(self):
        self.connection.execute(
            """
            UPDATE campaigns
            SET base_seed = 42,
                seed_protocol = 'paired_by_replica_v1',
                rng_engine = 'numpy_seedsequence_pcg64_v1'
            WHERE campaign_id = 'campaign'
            """
        )
        self.connection.execute(
            "UPDATE runs SET random_seed = 42 WHERE run_id = ?", (self.run_id,)
        )
        self.connection.commit()
        optimizer = LegacyCompatiblePSO(
            problem=self.problem,
            config=self.config,
            inertia_policy=self.policy,
            random_streams=ReplicaRandomStreams(42),
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
        self.assertEqual(row["random_seed"], 42)
        self.assertEqual(len(row["initial_population_sha256"]), 64)
        self.assertEqual(len(row["initial_velocity_sha256"]), 64)
        self.assertEqual(json.loads(row["solution_json"]), result.best_position.tolist())
        self.assertEqual(row["objective_best"], result.best_objective)

    def test_optimizer_failure_is_persisted_and_reraised(self):
        metadata = self._matching_optimizer().run_metadata
        executor = ExperimentRunExecutor(self.repository, clock=Clock(1.0))
        with self.assertRaisesRegex(FloatingPointError, "synthetic failure"):
            executor.execute(self.run_id, FailingOptimizer(metadata))

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
            run_metadata = self._matching_optimizer().run_metadata

            def run(self):
                return InvalidResult()

        executor = ExperimentRunExecutor(self.repository, clock=Clock(1.0))
        with self.assertRaisesRegex(ValueError, "solution coordinate"):
            executor.execute(self.run_id, InvalidOptimizer())

        status = self.connection.execute(
            "SELECT status FROM runs WHERE run_id = ?", (self.run_id,)
        ).fetchone()[0]
        self.assertEqual(status, "failed")

    def test_plan_mismatch_is_rejected_before_run_starts(self):
        mismatched = LegacyCompatiblePSO(
            problem=self.problem,
            config=LegacyPSORunConfig(population_size=5, max_iterations=2),
            inertia_policy=self.policy,
            rng=np.random.default_rng(9),
        )
        with self.assertRaisesRegex(RunBindingError, "population size"):
            ExperimentRunExecutor(self.repository).execute(self.run_id, mismatched)

        status = self.connection.execute(
            "SELECT status FROM runs WHERE run_id = ?", (self.run_id,)
        ).fetchone()[0]
        self.assertEqual(status, "planned")

    def test_trace_and_final_result_are_persisted_atomically(self):
        @dataclass
        class ResultWithInvalidTrace:
            best_position: tuple[float, ...] = (0.0, 0.0)
            best_objective: float = 0.0
            evaluations: int = 12
            trace_points: tuple[OptimizationTracePoint, ...] = (
                OptimizationTracePoint(0, 0, 4, 0.01, {"objective_best": 1.0}),
                OptimizationTracePoint(1, 1, 8, 0.01, {"inertia_weight": 0.6}),
            )

        class InvalidTraceOptimizer:
            run_metadata = self._matching_optimizer().run_metadata

            def run(self):
                return ResultWithInvalidTrace()

        with self.assertRaisesRegex(Exception, "not selected"):
            ExperimentRunExecutor(self.repository).execute(
                self.run_id, InvalidTraceOptimizer()
            )

        trace_count = self.connection.execute(
            "SELECT COUNT(*) FROM trace_points WHERE run_id = ?", (self.run_id,)
        ).fetchone()[0]
        status = self.connection.execute(
            "SELECT status FROM runs WHERE run_id = ?", (self.run_id,)
        ).fetchone()[0]
        self.assertEqual(trace_count, 0)
        self.assertEqual(status, "failed")

    def _matching_optimizer(self):
        return LegacyCompatiblePSO(
            problem=self.problem,
            config=self.config,
            inertia_policy=self.policy,
            rng=np.random.default_rng(5),
        )


if __name__ == "__main__":
    unittest.main()
