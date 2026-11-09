import unittest

import numpy as np

from afcs.optimizers.pso import LegacyLinearInertia, PSOConfig, advance_swarm


class TestPSOMotionCharacterization(unittest.TestCase):
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

    def test_linear_pso_uses_documented_equation_and_distinct_random_matrices(self):
        expected_population, expected_velocity = self._expected_step(0.74, 10.0)
        step = advance_swarm(
            positions=self.population.copy(),
            velocities=self.velocity.copy(),
            personal_best=self.personal_best.copy(),
            global_best=self.global_best.copy(),
            inertia=LegacyLinearInertia(max_iterations=10).value_at(2),
            cognitive_random=self.r1,
            social_random=self.r2,
            maximum_velocity=1.0,
            config=PSOConfig(cognitive=2.0, social=2.0),
        )

        np.testing.assert_allclose(step.positions, expected_population)
        np.testing.assert_allclose(step.velocities, expected_velocity)

    def test_velocity_is_clipped_before_position_update(self):
        r1 = np.ones((2, 2))
        r2 = np.ones((2, 2))
        step = advance_swarm(
            positions=self.population.copy(),
            velocities=self.velocity.copy(),
            personal_best=np.full((2, 2), 100.0),
            global_best=np.full(2, 100.0),
            inertia=LegacyLinearInertia(max_iterations=10).value_at(1),
            cognitive_random=r1,
            social_random=r2,
            maximum_velocity=0.1,
        )

        np.testing.assert_allclose(step.velocities, np.full((2, 2), 0.1))
        np.testing.assert_allclose(step.positions, self.population + 0.1)


if __name__ == "__main__":
    unittest.main()
