import unittest

import numpy as np

from afcs.core import OptimizationDirection, ReplicaRandomStreams, SearchSpace
from afcs.metrics import PSOTraceCollector, TraceSampling
from afcs.optimizers.pso import (
    FixedInertia,
    FuzzyInertiaPolicy,
    LegacyCompatiblePSO,
    LegacyLinearInertia,
    LegacyPSORunConfig,
)
from afcs.problems import CallableProblem, ProblemMetadata


def sphere_problem(
    direction: OptimizationDirection = OptimizationDirection.MINIMIZE,
) -> CallableProblem:
    sign = 1.0 if direction is OptimizationDirection.MINIMIZE else -1.0
    return CallableProblem(
        ProblemMetadata(
            problem_id="sphere-2d",
            family="test",
            search_space=SearchSpace.uniform(2, -5.0, 5.0),
            direction=direction,
        ),
        lambda candidate: sign * sum(value * value for value in candidate),
    )


class TestPSOInMemory(unittest.TestCase):
    def test_component_times_are_measured_at_explicit_boundaries(self):
        class StepClock:
            def __init__(self):
                self.value = -0.1

            def __call__(self):
                self.value += 0.1
                return self.value

        config = LegacyPSORunConfig(population_size=2, max_iterations=1)
        collector = PSOTraceCollector(
            selected_metrics=("objective_best",),
            sampling=TraceSampling(),
            maximum_iteration=1,
            lower_bounds=(-5.0, -5.0),
            upper_bounds=(5.0, 5.0),
        )
        result = LegacyCompatiblePSO(
            problem=sphere_problem(),
            config=config,
            inertia_policy=FixedInertia(0.7),
            rng=np.random.default_rng(123),
            trace_collector=collector,
            component_clock=StepClock(),
        ).run()

        self.assertAlmostEqual(
            result.run_metrics["problem_evaluation_total_seconds"], 0.4
        )
        self.assertAlmostEqual(
            result.run_metrics["metric_collection_total_seconds"], 0.2
        )

    def test_fixed_inertia_consumes_exact_budget_and_respects_bounds(self):
        config = LegacyPSORunConfig(population_size=4, max_iterations=3)
        result = LegacyCompatiblePSO(
            problem=sphere_problem(),
            config=config,
            inertia_policy=FixedInertia(0.7),
            rng=np.random.default_rng(12345),
        ).run()

        self.assertEqual(result.evaluations, 16)
        self.assertEqual(result.iterations, 3)
        self.assertEqual(result.inertia_history, (0.7, 0.7, 0.7))
        self.assertTrue(np.all(result.positions >= -5.0))
        self.assertTrue(np.all(result.positions <= 5.0))
        self.assertFalse(result.positions.flags.writeable)
        self.assertFalse(result.best_position.flags.writeable)

    def test_injected_generators_make_execution_reproducible(self):
        config = LegacyPSORunConfig(population_size=5, max_iterations=4)

        def execute() -> tuple[np.ndarray, float]:
            result = LegacyCompatiblePSO(
                problem=sphere_problem(),
                config=config,
                inertia_policy=FixedInertia(0.5),
                rng=np.random.default_rng(9876),
            ).run()
            return result.positions, result.best_objective

        positions_a, best_a = execute()
        positions_b, best_b = execute()
        np.testing.assert_array_equal(positions_a, positions_b)
        self.assertEqual(best_a, best_b)

    def test_instrumentation_does_not_change_search_trajectory(self):
        config = LegacyPSORunConfig(population_size=5, max_iterations=4)
        baseline = LegacyCompatiblePSO(
            problem=sphere_problem(),
            config=config,
            inertia_policy=FixedInertia(0.5),
            random_streams=ReplicaRandomStreams(42),
        ).run()
        collector = PSOTraceCollector(
            selected_metrics=("objective_best", "diversity_hussain", "inertia_weight"),
            sampling=TraceSampling(),
            maximum_iteration=config.max_iterations,
            lower_bounds=(-5.0, -5.0),
            upper_bounds=(5.0, 5.0),
        )
        instrumented = LegacyCompatiblePSO(
            problem=sphere_problem(),
            config=config,
            inertia_policy=FixedInertia(0.5),
            random_streams=ReplicaRandomStreams(42),
            trace_collector=collector,
        ).run()

        np.testing.assert_array_equal(instrumented.positions, baseline.positions)
        self.assertEqual(instrumented.best_objective, baseline.best_objective)
        self.assertEqual(
            instrumented.initial_population_sha256,
            baseline.initial_population_sha256,
        )
        self.assertEqual(len(instrumented.trace_points), 5)

    def test_legacy_policy_reaches_historical_final_inertia(self):
        config = LegacyPSORunConfig(population_size=3, max_iterations=4)
        result = LegacyCompatiblePSO(
            problem=sphere_problem(),
            config=config,
            inertia_policy=LegacyLinearInertia(config.max_iterations),
            rng=np.random.default_rng(7),
        ).run()

        np.testing.assert_allclose(result.inertia_history, (0.7, 0.5, 0.3, 0.1))

    def test_pso_policies_share_initial_conditions_for_a_paired_replica(self):
        config = LegacyPSORunConfig(population_size=5, max_iterations=3)
        fixed = LegacyCompatiblePSO(
            problem=sphere_problem(),
            config=config,
            inertia_policy=FixedInertia(0.6),
            random_streams=ReplicaRandomStreams(42),
        ).run()
        linear = LegacyCompatiblePSO(
            problem=sphere_problem(),
            config=config,
            inertia_policy=LegacyLinearInertia(config.max_iterations),
            random_streams=ReplicaRandomStreams(42),
        ).run()

        self.assertEqual(
            fixed.initial_population_sha256, linear.initial_population_sha256
        )
        self.assertEqual(
            fixed.initial_velocity_sha256, linear.initial_velocity_sha256
        )

    def test_fuzzy_policy_uses_initial_population_then_persists_diagnostics(self):
        config = LegacyPSORunConfig(population_size=5, max_iterations=2)
        selected = (
            "iteration_index",
            "progress_ratio",
            "fuzzy_input_diversity",
            "fuzzy_boundary_event_count",
            "fuzzy_no_activation_count",
            "fuzzy_fallback_count",
            "inertia_weight",
        )
        collector = PSOTraceCollector(
            selected_metrics=selected,
            sampling=TraceSampling(),
            maximum_iteration=config.max_iterations,
            lower_bounds=(-5.0, -5.0),
            upper_bounds=(5.0, 5.0),
        )
        result = LegacyCompatiblePSO(
            problem=sphere_problem(),
            config=config,
            inertia_policy=FuzzyInertiaPolicy(
                max_iterations=config.max_iterations,
                granularity=3,
                rule_base="R1",
                overlap_mode="shared",
                overlap=0.0,
            ),
            random_streams=ReplicaRandomStreams(42),
            trace_collector=collector,
        ).run()

        self.assertNotIn("inertia_weight", result.trace_points[0].metrics)
        self.assertNotIn("progress_ratio", result.trace_points[0].metrics)
        first = result.trace_points[1].metrics
        self.assertEqual(first["progress_ratio"], 0.5)
        self.assertEqual(first["fuzzy_input_diversity"], 1.0)
        self.assertEqual(first["fuzzy_no_activation_count"], 0)
        self.assertEqual(first["fuzzy_fallback_count"], 0)
        self.assertIn("inertia_weight", first)

    def test_maximization_direction_is_supported(self):
        result = LegacyCompatiblePSO(
            problem=sphere_problem(OptimizationDirection.MAXIMIZE),
            config=LegacyPSORunConfig(population_size=4, max_iterations=2),
            inertia_policy=FixedInertia(0.6),
            rng=np.random.default_rng(21),
        ).run()
        self.assertAlmostEqual(
            result.best_objective, -float(np.sum(result.best_position**2))
        )
        self.assertGreaterEqual(
            result.best_objective, float(np.max(result.objective_values))
        )

    def test_legacy_velocity_rule_rejects_negative_first_upper_bound(self):
        problem = CallableProblem(
            ProblemMetadata(
                problem_id="negative-domain",
                family="test",
                search_space=SearchSpace.uniform(2, -5.0, -1.0),
            ),
            lambda candidate: sum(value * value for value in candidate),
        )
        optimizer = LegacyCompatiblePSO(
            problem=problem,
            config=LegacyPSORunConfig(population_size=2, max_iterations=1),
            inertia_policy=FixedInertia(0.5),
            rng=np.random.default_rng(1),
        )
        with self.assertRaisesRegex(ValueError, "legacy Vmax"):
            optimizer.run()


if __name__ == "__main__":
    unittest.main()
