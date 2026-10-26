from __future__ import annotations

import unittest

import numpy as np

from afcs.core import ReplicaRandomStreams
from afcs.problems.benchmarks import (
    CLASSICAL_FUNCTIONS,
    ClassicalBenchmarkProblem,
    create_classical_problem,
)
from Problem.Benchmark import Problem as legacy


class TestClassicalBenchmarkProblems(unittest.TestCase):
    def test_catalog_contains_all_functions_and_enforces_fixed_dimensions(self):
        self.assertEqual(tuple(CLASSICAL_FUNCTIONS), tuple(range(1, 24)))
        for number, expected in {
            14: 2, 15: 4, 16: 2, 17: 2, 18: 2,
            19: 3, 20: 6, 21: 4, 22: 4, 23: 4,
        }.items():
            with self.subTest(function=number):
                with self.assertRaisesRegex(ValueError, "requires dimension"):
                    ClassicalBenchmarkProblem(number, expected + 1)

    def test_deterministic_functions_match_legacy_implementation(self):
        generator = np.random.default_rng(20261026)
        for number, definition in CLASSICAL_FUNCTIONS.items():
            if definition.stochastic:
                continue
            dimension = definition.fixed_dimension or 7
            candidate = generator.uniform(
                definition.lower_bound, definition.upper_bound, size=dimension
            )
            observed = ClassicalBenchmarkProblem(number, dimension).evaluate(
                candidate
            ).objective
            expected = float(np.asarray(getattr(legacy, f"F{number}")(candidate)).item())
            with self.subTest(function=number):
                self.assertAlmostEqual(observed, expected, places=11)

    def test_f7_requires_explicit_reproducible_problem_stream(self):
        with self.assertRaisesRegex(ValueError, "noise_rng"):
            ClassicalBenchmarkProblem(7, 5)
        candidate = np.full(5, 0.25)
        first = ClassicalBenchmarkProblem(
            7, 5, noise_rng=ReplicaRandomStreams(42).generator("problem")
        )
        second = ClassicalBenchmarkProblem(
            7, 5, noise_rng=ReplicaRandomStreams(42).generator("problem")
        )
        self.assertEqual(
            first.evaluate(candidate).objective,
            second.evaluate(candidate).objective,
        )

    def test_factory_validates_identifier_and_metadata(self):
        problem = create_classical_problem("F8", 30)
        self.assertEqual(problem.metadata.problem_id, "F8")
        self.assertEqual(problem.metadata.family, "CLASSICAL")
        self.assertEqual(problem.metadata.known_optimum, -418.9829 * 30)
        self.assertEqual(problem.metadata.parameters["suite_version"], "legacy_classical_v1")
        with self.assertRaises(ValueError):
            create_classical_problem("F08", 30)


if __name__ == "__main__":
    unittest.main()
