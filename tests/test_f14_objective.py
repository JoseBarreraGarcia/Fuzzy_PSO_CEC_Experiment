import unittest

import numpy as np

from Problem.Benchmark.Problem import F14, _F14_WEIGHTS


class TestF14Objective(unittest.TestCase):
    def test_weights_are_canonical(self):
        self.assertEqual(_F14_WEIGHTS, tuple(range(1, 26)))

    def test_values_at_all_25_benchmark_centers(self):
        coordinates = (-32, -16, 0, 16, 32)
        centers = [(x, y) for y in coordinates for x in coordinates]
        weights = np.arange(1, 26, dtype=float)

        for center_index, center in enumerate(centers):
            distances = np.sum((np.asarray(center) - np.asarray(centers)) ** 6, axis=1)
            expected = 1.0 / (1.0 / 500.0 + np.sum(1.0 / (weights + distances)))
            with self.subTest(center=center):
                self.assertAlmostEqual(float(F14(np.asarray(center))), expected, places=11)

    def test_known_global_minimum_value(self):
        minimizer = np.array([-31.97850818, -31.97849828])
        self.assertAlmostEqual(float(F14(minimizer)), 0.998003837794635, places=8)


if __name__ == "__main__":
    unittest.main()