import unittest
import warnings
import sys
from pathlib import Path

import numpy as np

SRC = Path(__file__).resolve().parents[1] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from afcs.problems.benchmarks.cec2017 import composition, functions, transforms
from afcs.problems.benchmarks.cec2017.problem import CEC2017Problem
from Problem.Benchmark.Problem import fitness


EXPERIMENT_DIMENSIONS = (10, 30, 50, 100)
OFFICIAL_FUNCTION_NUMBERS = tuple(i for i in range(1, 31) if i != 2)


class TestCEC2017CompositionWeights(unittest.TestCase):
    def test_exact_centres_have_finite_one_hot_weights(self):
        raw = np.array([[np.inf, 2.0, 1.0], [1.0, np.inf, np.inf]])
        weights = composition._normalise_weights(raw)
        np.testing.assert_array_equal(weights[0], [1.0, 0.0, 0.0])
        np.testing.assert_array_equal(weights[1], [0.0, 0.5, 0.5])

    def test_zero_underflow_row_uses_uniform_weights(self):
        weights = composition._normalise_weights(np.zeros((1, 4)))
        np.testing.assert_array_equal(weights, np.full((1, 4), 0.25))

    def test_all_compositions_are_finite_at_every_shift_centre(self):
        for dimension in EXPERIMENT_DIMENSIONS:
            for function_number in range(21, 31):
                fn = functions.all_functions[function_number - 1]
                shifts = transforms.shifts_cf[function_number - 21]
                for centre_index in range(10):
                    x = shifts[centre_index, :dimension].reshape(1, -1)
                    with self.subTest(
                        function=function_number,
                        dimension=dimension,
                        centre=centre_index,
                    ):
                        with warnings.catch_warnings():
                            warnings.simplefilter("error", RuntimeWarning)
                            value = fn(x)
                        self.assertTrue(np.all(np.isfinite(value)))

    def test_compositions_are_finite_near_first_shift_centre(self):
        epsilons = (np.finfo(float).eps, 1e-12, 1e-8, 1e-4)
        for dimension in (30, 50):
            for function_number in range(21, 31):
                fn = functions.all_functions[function_number - 1]
                centre = transforms.shifts_cf[function_number - 21][0, :dimension]
                points = [centre]
                for epsilon in epsilons:
                    delta = np.zeros(dimension)
                    delta[0] = epsilon
                    points.extend((centre + delta, centre - delta))
                values = fn(np.asarray(points))
                with self.subTest(function=function_number, dimension=dimension):
                    self.assertTrue(np.all(np.isfinite(values)))


class TestCEC2017Suite(unittest.TestCase):
    def test_all_official_functions_are_finite_and_deterministic(self):
        rng = np.random.default_rng(20261019)
        for dimension in EXPERIMENT_DIMENSIONS:
            points = rng.uniform(-100.0, 100.0, size=(3, dimension))
            for function_number in OFFICIAL_FUNCTION_NUMBERS:
                fn = functions.all_functions[function_number - 1]
                with self.subTest(function=function_number, dimension=dimension):
                    first = fn(points.copy())
                    second = fn(points.copy())
                    self.assertTrue(np.all(np.isfinite(first)))
                    np.testing.assert_array_equal(first, second)

    def test_dispatcher_accepts_supported_dimension(self):
        value = fitness("F21CEC2017", np.zeros(30))
        self.assertTrue(np.isfinite(value))

    def test_dispatcher_rejects_deprecated_f2(self):
        with self.assertRaisesRegex(ValueError, "retirada"):
            fitness("F2CEC2017", np.zeros(30))

    def test_dispatcher_rejects_unsupported_dimension(self):
        with self.assertRaisesRegex(ValueError, "Dimension CEC2017 no admitida"):
            fitness("F1CEC2017", np.zeros(7))

    def test_dispatcher_rejects_non_finite_input(self):
        point = np.zeros(30)
        point[0] = np.nan
        with self.assertRaisesRegex(ValueError, "NaN o infinitas"):
            fitness("F1CEC2017", point)

    def test_v2_adapter_matches_raw_implementation(self):
        rng = np.random.default_rng(20261019)
        for dimension in EXPERIMENT_DIMENSIONS:
            point = rng.uniform(-100.0, 100.0, size=dimension)
            for function_number in OFFICIAL_FUNCTION_NUMBERS:
                with self.subTest(function=function_number, dimension=dimension):
                    problem = CEC2017Problem(function_number, dimension)
                    raw = functions.all_functions[function_number - 1](
                        point.reshape(1, -1)
                    )[0]
                    self.assertEqual(problem.evaluate(point).objective, float(raw))

    def test_v2_adapter_declares_identity_domain_and_optimum(self):
        problem = CEC2017Problem(21, 30)
        self.assertEqual(problem.metadata.problem_id, "F21CEC2017")
        self.assertEqual(problem.metadata.family, "CEC2017")
        self.assertEqual(problem.metadata.dimension, 30)
        self.assertEqual(problem.metadata.known_optimum, 2100.0)
        self.assertTrue(problem.metadata.search_space.contains(np.zeros(30)))

    def test_v2_adapter_rejects_f2_dimension_and_non_finite_input(self):
        with self.assertRaisesRegex(ValueError, "F2"):
            CEC2017Problem(2, 30)
        with self.assertRaisesRegex(ValueError, "dimension"):
            CEC2017Problem(1, 7)
        problem = CEC2017Problem(1, 30)
        point = np.zeros(30)
        point[0] = np.inf
        with self.assertRaisesRegex(ValueError, "finite"):
            problem.evaluate(point)


if __name__ == "__main__":
    unittest.main()
