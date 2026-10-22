import unittest
from unittest.mock import patch

import numpy as np

from Metaheuristics.Codes.PSO import iterarPSO
from Metaheuristics.Codes.PSO_FCS import iterarPSO_FCS


class StubFuzzyController:
    def __init__(self, inertia):
        self.inertia = inertia
        self.w_set = "O1"
        self.wMin = 0.1
        self.wMax = 0.9
        self.calls = []

    def compute_w(self, diversity_ratio, progress):
        self.calls.append((diversity_ratio, progress))
        return self.inertia


class TestLegacyPSOCharacterization(unittest.TestCase):
    def setUp(self):
        self.population = np.array([[1.0, 2.0], [-1.0, 0.0]])
        self.velocity = np.array([[0.2, -0.2], [0.5, 0.5]])
        self.personal_best = np.array([[0.5, 1.5], [-0.5, 1.0]])
        self.global_best = np.array([0.0, 0.0])
        self.r1 = np.full((2, 2), 0.25)
        self.r2 = np.full((2, 2), 0.50)

    def _expected_step(self, inertia, upper_bound):
        velocity = (
            inertia * self.velocity
            + 2.0 * self.r1 * (self.personal_best - self.population)
            + 2.0 * self.r2 * (self.global_best - self.population)
        )
        velocity = np.clip(velocity, -0.1 * upper_bound, 0.1 * upper_bound)
        return self.population + velocity, velocity

    def test_linear_pso_uses_documented_equation_and_random_matrix_order(self):
        expected_population, expected_velocity = self._expected_step(0.74, 10.0)
        with patch(
            "Metaheuristics.Codes.PSO.np.random.rand",
            side_effect=[self.r1.copy(), self.r2.copy()],
        ) as random_values:
            population, velocity = iterarPSO(
                maxIter=10,
                iter=2,
                dim=2,
                population=self.population.copy(),
                best=self.global_best.copy(),
                pBest=self.personal_best.copy(),
                vel=self.velocity.copy(),
                ub0=10.0,
            )

        np.testing.assert_allclose(population, expected_population)
        np.testing.assert_allclose(velocity, expected_velocity)
        self.assertEqual(random_values.call_count, 2)

    def test_fuzzy_pso_differs_only_by_inertia_and_diversity_observation(self):
        controller = StubFuzzyController(inertia=0.74)
        expected_population, expected_velocity = self._expected_step(0.74, 10.0)

        with (
            patch(
                "Metaheuristics.Codes.PSO_FCS.calculate_diversity",
                return_value=(2.0, 4.0, 50.0, 50.0),
            ),
            patch(
                "Metaheuristics.Codes.PSO_FCS.np.random.rand",
                side_effect=[self.r1.copy(), self.r2.copy()],
            ),
        ):
            population, velocity, maximum_diversity = iterarPSO_FCS(
                maxIter=10,
                iter=2,
                dim=2,
                population=self.population.copy(),
                best=self.global_best.copy(),
                pBest=self.personal_best.copy(),
                vel=self.velocity.copy(),
                ub0=10.0,
                maxDiversity=3.0,
                fcs=controller,
                w_set="O1",
            )

        np.testing.assert_allclose(population, expected_population)
        np.testing.assert_allclose(velocity, expected_velocity)
        self.assertEqual(maximum_diversity, 4.0)
        self.assertEqual(controller.calls, [(0.5, 0.2)])

    def test_velocity_is_clipped_before_position_update(self):
        r1 = np.ones((2, 2))
        r2 = np.ones((2, 2))
        with patch(
            "Metaheuristics.Codes.PSO.np.random.rand",
            side_effect=[r1, r2],
        ):
            population, velocity = iterarPSO(
                maxIter=10,
                iter=1,
                dim=2,
                population=self.population.copy(),
                best=np.full(2, 100.0),
                pBest=np.full((2, 2), 100.0),
                vel=self.velocity.copy(),
                ub0=1.0,
            )

        np.testing.assert_allclose(velocity, np.full((2, 2), 0.1))
        np.testing.assert_allclose(population, self.population + 0.1)


if __name__ == "__main__":
    unittest.main()

