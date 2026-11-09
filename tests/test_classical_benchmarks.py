from __future__ import annotations

import unittest

import numpy as np

from afcs.core import ReplicaRandomStreams
from afcs.problems.benchmarks import (
    CLASSICAL_FUNCTIONS,
    ClassicalBenchmarkProblem,
    create_classical_problem,
)

# Captured from Problem.py (blob 9f925a2fef10226af0aafbad5a69a16837637809)
# with default_rng(20261026), canonical bounds and fixed_dimension or 7.
LEGACY_OBJECTIVES = {
    1: 23029.451183434478,
    2: 71198.77613836648,
    3: 584098.8603744708,
    4: 86.94844022201652,
    5: 54863853.2588819,
    6: 15263.828952541406,
    8: -324.1721085454639,
    9: 59.49640148093347,
    10: 20.759418442778497,
    11: 296.92795705699064,
    12: 441630967.8573816,
    13: 755874298.261812,
    14: 499.998573713464,
    15: 68.33212856643175,
    16: 1302.468090789247,
    17: 34.866052600080444,
    18: 22241.358551824673,
    19: -0.6716413132915737,
    20: -0.005875070281369483,
    21: -0.15715780707905902,
    22: -0.16372457823545797,
    23: -0.16366019985945457,
}


class TestClassicalBenchmarkProblems(unittest.TestCase):
    def test_catalog_contains_all_functions_and_enforces_fixed_dimensions(self):
        self.assertEqual(tuple(CLASSICAL_FUNCTIONS), tuple(range(1, 24)))
        for number, expected in {
            14: 2,
            15: 4,
            16: 2,
            17: 2,
            18: 2,
            19: 3,
            20: 6,
            21: 4,
            22: 4,
            23: 4,
        }.items():
            with self.subTest(function=number):
                with self.assertRaisesRegex(ValueError, "requires dimension"):
                    ClassicalBenchmarkProblem(number, expected + 1)

    def test_deterministic_functions_match_captured_legacy_objectives(self):
        self.assertEqual(
            set(LEGACY_OBJECTIVES),
            {
                number
                for number, definition in CLASSICAL_FUNCTIONS.items()
                if not definition.stochastic
            },
        )
        generator = np.random.default_rng(20261026)
        for number, definition in CLASSICAL_FUNCTIONS.items():
            if definition.stochastic:
                continue
            dimension = definition.fixed_dimension or 7
            candidate = generator.uniform(
                definition.lower_bound, definition.upper_bound, size=dimension
            )
            observed = (
                ClassicalBenchmarkProblem(number, dimension)
                .evaluate(candidate)
                .objective
            )
            expected = LEGACY_OBJECTIVES[number]
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
        self.assertEqual(
            problem.metadata.parameters["suite_version"], "legacy_classical_v1"
        )
        with self.assertRaises(ValueError):
            create_classical_problem("F08", 30)


if __name__ == "__main__":
    unittest.main()
