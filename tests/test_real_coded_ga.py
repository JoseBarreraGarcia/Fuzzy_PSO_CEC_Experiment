from __future__ import annotations

import unittest

import numpy as np

from afcs.core import OptimizationDirection, ReplicaRandomStreams, SearchSpace
from afcs.metrics import TraceSampling
from afcs.optimizers.ga import GATraceCollector, RealCodedGA, RealCodedGARunConfig
from afcs.problems import CallableProblem, ProblemMetadata


def sphere_problem(
    direction: OptimizationDirection = OptimizationDirection.MINIMIZE,
    observed: list[float] | None = None,
) -> CallableProblem:
    sign = 1.0 if direction is OptimizationDirection.MINIMIZE else -1.0

    def evaluate(candidate):
        value = sign * float(np.sum(np.square(candidate)))
        if observed is not None:
            observed.append(value)
        return value

    return CallableProblem(
        ProblemMetadata(
            problem_id="sphere-3d",
            family="test",
            search_space=SearchSpace.uniform(3, -5.0, 5.0),
            direction=direction,
        ),
        evaluate,
    )


class TestRealCodedGA(unittest.TestCase):
    def test_exact_budget_bounds_and_elitism_for_even_and_odd_populations(self):
        for population_size in (4, 5):
            with self.subTest(population_size=population_size):
                initial_values: list[float] = []
                config = RealCodedGARunConfig(
                    population_size=population_size, max_iterations=4
                )
                result = RealCodedGA(
                    problem=sphere_problem(observed=initial_values),
                    config=config,
                    random_streams=ReplicaRandomStreams(42),
                ).run()

                self.assertEqual(result.evaluations, population_size * 5)
                self.assertEqual(result.evaluations, config.evaluation_budget)
                self.assertEqual(len(result.positions), population_size)
                self.assertTrue(np.all(result.positions >= -5.0))
                self.assertTrue(np.all(result.positions <= 5.0))
                self.assertLessEqual(result.best_objective, min(initial_values))
                self.assertEqual(
                    result.best_objective, float(np.min(result.objective_values))
                )
                self.assertFalse(result.positions.flags.writeable)
                self.assertFalse(result.best_position.flags.writeable)

    def test_maximization_direction_is_respected(self):
        initial_values: list[float] = []
        result = RealCodedGA(
            problem=sphere_problem(
                OptimizationDirection.MAXIMIZE, observed=initial_values
            ),
            config=RealCodedGARunConfig(population_size=5, max_iterations=3),
            random_streams=ReplicaRandomStreams(9),
        ).run()

        self.assertGreaterEqual(result.best_objective, max(initial_values))
        self.assertEqual(result.best_objective, float(np.max(result.objective_values)))

    def test_named_streams_make_run_and_initial_population_reproducible(self):
        config = RealCodedGARunConfig(population_size=6, max_iterations=3)

        def execute():
            return RealCodedGA(
                problem=sphere_problem(),
                config=config,
                random_streams=ReplicaRandomStreams(123),
            ).run()

        first, second = execute(), execute()
        np.testing.assert_array_equal(first.positions, second.positions)
        np.testing.assert_array_equal(first.best_position, second.best_position)
        self.assertEqual(first.best_objective, second.best_objective)
        self.assertEqual(
            first.initial_population_sha256, second.initial_population_sha256
        )

    def test_population_trace_records_effective_ga_parameters_without_pso_fields(self):
        config = RealCodedGARunConfig(population_size=4, max_iterations=2)
        collector = GATraceCollector(
            selected_metrics=(
                "objective_best",
                "objective_mean",
                "crossover_probability",
                "mutation_probability",
                "inertia_weight",
            ),
            sampling=TraceSampling(),
            maximum_iteration=config.max_iterations,
            lower_bounds=(-5.0, -5.0, -5.0),
            upper_bounds=(5.0, 5.0, 5.0),
        )
        result = RealCodedGA(
            problem=sphere_problem(),
            config=config,
            random_streams=ReplicaRandomStreams(42),
            trace_collector=collector,
        ).run()

        self.assertEqual(len(result.trace_points), 3)
        initial = result.trace_points[0].metrics
        first_generation = result.trace_points[1].metrics
        self.assertNotIn("crossover_probability", initial)
        self.assertNotIn("mutation_probability", initial)
        self.assertEqual(first_generation["crossover_probability"], 0.9)
        self.assertAlmostEqual(first_generation["mutation_probability"], 1 / 3)
        self.assertIn("objective_mean", first_generation)
        self.assertNotIn("inertia_weight", first_generation)

    def test_invalid_probabilities_and_operator_indices_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "crossover_probability"):
            RealCodedGARunConfig(4, 1, crossover_probability=1.1)
        with self.assertRaisesRegex(ValueError, "mutation_probability"):
            RealCodedGARunConfig(4, 1, mutation_probability=-0.1)
        with self.assertRaisesRegex(ValueError, "distribution_index"):
            RealCodedGARunConfig(4, 1, mutation_distribution_index=0)


if __name__ == "__main__":
    unittest.main()
