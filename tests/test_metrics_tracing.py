from __future__ import annotations

import unittest

import numpy as np

from afcs.metrics import (
    OptimizationObservation,
    OptimizationTraceCollector,
    PopulationObservation,
    PSOTraceCollector,
    TraceSampling,
    diversity_per_dimension_v1,
    exploration_exploitation_v1,
    hussain_diversity_v1,
    population_entropy_v1,
)


class TestVersionedPopulationMetrics(unittest.TestCase):
    def setUp(self) -> None:
        self.population = np.array(
            [
                [-4.0, 1.0, 3.0],
                [2.0, -1.0, 5.0],
                [7.0, 4.0, -2.0],
                [1.0, 0.0, 8.0],
            ]
        )

    def test_hussain_v1_preserves_recorded_legacy_value(self) -> None:
        self.assertEqual(hussain_diversity_v1(self.population), 2.5)

    def test_dimension_diversity_v1_preserves_recorded_legacy_values(self) -> None:
        observed = diversity_per_dimension_v1(self.population)
        np.testing.assert_allclose(observed[0], [3.0, 1.5, 3.0])
        np.testing.assert_allclose(observed[1:], [2.5, 1.5, 3.0])

    def test_entropy_v1_preserves_recorded_legacy_values(self) -> None:
        lower = np.full(3, -10.0)
        upper = np.full(3, 10.0)
        observed = population_entropy_v1(
            self.population,
            bins=20,
            lower_bounds=lower,
            upper_bounds=upper,
        )
        self.assertAlmostEqual(observed[0], 0.8112781244591328)
        np.testing.assert_allclose(observed[1], [0.8112781244591328] * 3)

    def test_diversity_metrics_handle_constant_and_singleton_populations(self):
        for population in (
            np.full((4, 3), 2.0),
            np.array([[2.0, -3.0, 5.0]]),
        ):
            with self.subTest(population=population):
                self.assertEqual(hussain_diversity_v1(population), 0.0)
                dimensions = diversity_per_dimension_v1(population)
                np.testing.assert_array_equal(dimensions[0], np.zeros(3))
                self.assertEqual(dimensions[1:], (0.0, 0.0, 0.0))
                for bounded in (False, True):
                    entropy, coordinates = population_entropy_v1(
                        population,
                        lower_bounds=np.full(3, -10.0) if bounded else None,
                        upper_bounds=np.full(3, 10.0) if bounded else None,
                    )
                    self.assertEqual(entropy, 0.0)
                    np.testing.assert_array_equal(coordinates, np.zeros(3))

    def test_global_diversity_uses_mean_while_dimension_metric_uses_median(self):
        population = np.array([[0.0], [0.0], [9.0]])
        self.assertEqual(hussain_diversity_v1(population), 4.0)
        observed = diversity_per_dimension_v1(population)
        np.testing.assert_array_equal(observed[0], [3.0])
        self.assertEqual(observed[1:], (3.0, 3.0, 3.0))
        self.assertEqual(hussain_diversity_v1(np.array([[0.0], [1.0], [1.0]])), 0.444)

    def test_exploration_exploitation_preserves_percentages_and_zero_case(self):
        self.assertEqual(exploration_exploitation_v1(1.0, 3.0), (33.33, 66.67))
        self.assertEqual(exploration_exploitation_v1(3.0, 3.0), (100.0, 0.0))
        self.assertEqual(exploration_exploitation_v1(0.0, 3.0), (0.0, 100.0))
        self.assertEqual(exploration_exploitation_v1(0.0, 0.0), (0.0, 0.0))

    def test_population_metrics_reject_invalid_observations(self):
        for population in (
            np.array([]),
            np.empty((0, 3)),
            np.empty((3, 0)),
            np.ones(3),
            np.array([[np.nan]]),
            np.array([[np.inf]]),
        ):
            for metric in (
                hussain_diversity_v1,
                diversity_per_dimension_v1,
                population_entropy_v1,
            ):
                with self.subTest(metric=metric.__name__, population=population):
                    with self.assertRaises(ValueError):
                        metric(population)

    def test_checkpoint_zero_has_no_unapplied_inertia(self) -> None:
        collector = PSOTraceCollector(
            selected_metrics=(
                "iteration_index",
                "evaluations",
                "objective_best",
                "inertia_weight",
            ),
            sampling=TraceSampling(),
            maximum_iteration=2,
            lower_bounds=(-10.0, -10.0, -10.0),
            upper_bounds=(10.0, 10.0, 10.0),
        )
        objectives = np.array([5.0, 3.0, 8.0, 4.0])

        collector.observe(
            observation=OptimizationObservation(0, 4, 3.0, 0.01),
            population=PopulationObservation(self.population, objectives),
            inertia_weight=None,
        )
        collector.observe(
            observation=OptimizationObservation(1, 8, 3.0, 0.02),
            population=PopulationObservation(self.population, objectives),
            inertia_weight=0.6,
        )

        self.assertNotIn("inertia_weight", collector.points[0].metrics)
        self.assertEqual(collector.points[1].metrics["inertia_weight"], 0.6)

    def test_method_neutral_collector_needs_no_population_or_pso_fields(self):
        collector = OptimizationTraceCollector(
            selected_metrics=(
                "iteration_index",
                "evaluations",
                "objective_best",
            ),
            sampling=TraceSampling(),
            maximum_iteration=1,
        )
        collector.observe(observation=OptimizationObservation(0, 4, 3.0, 0.01))

        self.assertEqual(
            dict(collector.points[0].metrics),
            {
                "iteration_index": 0,
                "objective_best": 3.0,
                "evaluations": 4,
            },
        )

    def test_population_metrics_are_available_without_pso_metrics(self):
        collector = OptimizationTraceCollector(
            selected_metrics=("objective_mean", "objective_std"),
            sampling=TraceSampling(),
            maximum_iteration=0,
        )
        objectives = np.array([5.0, 3.0, 8.0, 4.0])
        collector.observe(
            observation=OptimizationObservation(0, 4, 3.0, 0.01),
            population=PopulationObservation(self.population, objectives),
        )

        self.assertEqual(collector.points[0].metrics["objective_mean"], 5.0)
        self.assertAlmostEqual(
            collector.points[0].metrics["objective_std"],
            float(np.std(objectives)),
        )

    def test_pso_collector_preserves_method_neutral_observe_contract(self):
        collector: OptimizationTraceCollector = PSOTraceCollector(
            selected_metrics=("objective_best", "evaluations", "inertia_weight"),
            sampling=TraceSampling(),
            maximum_iteration=0,
            lower_bounds=(-5.0,),
            upper_bounds=(5.0,),
        )
        collector.observe(observation=OptimizationObservation(0, 4, 3.0, 0.01))
        self.assertEqual(
            dict(collector.points[0].metrics),
            {"objective_best": 3.0, "evaluations": 4},
        )

    def test_sampling_always_includes_final_iteration(self) -> None:
        sampling = TraceSampling(every_iterations=2)
        self.assertTrue(sampling.includes(0, 5))
        self.assertFalse(sampling.includes(1, 5))
        self.assertTrue(sampling.includes(2, 5))
        self.assertFalse(sampling.includes(3, 5))
        self.assertTrue(sampling.includes(4, 5))
        self.assertTrue(sampling.includes(5, 5))


if __name__ == "__main__":
    unittest.main()
