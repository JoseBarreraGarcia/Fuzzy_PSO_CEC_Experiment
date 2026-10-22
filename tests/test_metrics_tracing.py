from __future__ import annotations

import unittest

import numpy as np

from Diversity.Codes.diversityDimention import diversity_per_dimension
from Diversity.Codes.hussainDiversity import diversidadHussain
from Diversity.Codes.populationEntropy import population_entropy
from afcs.metrics import (
    PSOTraceCollector,
    TraceSampling,
    diversity_per_dimension_v1,
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

    def test_hussain_v1_matches_legacy_formula_exactly(self) -> None:
        self.assertEqual(
            hussain_diversity_v1(self.population),
            diversidadHussain(self.population),
        )

    def test_dimension_diversity_v1_matches_legacy_formula(self) -> None:
        expected = diversity_per_dimension(self.population)
        observed = diversity_per_dimension_v1(self.population)
        np.testing.assert_allclose(observed[0], expected[0])
        np.testing.assert_allclose(observed[1:], expected[1:])

    def test_entropy_v1_matches_legacy_formula(self) -> None:
        lower = np.full(3, -10.0)
        upper = np.full(3, 10.0)
        expected = population_entropy(
            self.population, bins=20, lb=lower, ub=upper
        )
        observed = population_entropy_v1(
            self.population,
            bins=20,
            lower_bounds=lower,
            upper_bounds=upper,
        )
        self.assertAlmostEqual(observed[0], expected[0])
        np.testing.assert_allclose(observed[1], expected[1])

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
            iteration=0,
            evaluations=4,
            positions=self.population,
            objective_values=objectives,
            best_objective=3.0,
            elapsed_seconds=0.01,
            inertia_weight=None,
        )
        collector.observe(
            iteration=1,
            evaluations=8,
            positions=self.population,
            objective_values=objectives,
            best_objective=3.0,
            elapsed_seconds=0.02,
            inertia_weight=0.6,
        )

        self.assertNotIn("inertia_weight", collector.points[0].metrics)
        self.assertEqual(collector.points[1].metrics["inertia_weight"], 0.6)

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
