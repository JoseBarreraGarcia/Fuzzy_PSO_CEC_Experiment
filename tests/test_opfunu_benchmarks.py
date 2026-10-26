from __future__ import annotations

import unittest

import numpy as np

from afcs.problems.benchmarks import OpfunuCECProblem, opfunu_version


class TestOpfunuCECProblem(unittest.TestCase):
    def test_metadata_identifies_suite_function_implementation_and_version(self):
        problem = OpfunuCECProblem(2014, 1, 10)

        self.assertEqual(problem.metadata.family, "OPFUNU_CEC")
        self.assertEqual(problem.metadata.problem_id, "F1CEC2014_OPFUNU")
        self.assertEqual(problem.metadata.known_optimum, 100.0)
        self.assertEqual(problem.metadata.parameters["suite"], "CEC2014")
        self.assertEqual(problem.metadata.parameters["function_number"], 1)
        self.assertEqual(
            problem.metadata.parameters["implementation_version"], opfunu_version()
        )

    def test_evaluation_at_packaged_global_solution_matches_known_optimum(self):
        import opfunu.cec_based as cec_based

        raw = cec_based.F12014(ndim=10)
        problem = OpfunuCECProblem(2014, 1, 10)
        observed = problem.evaluate(np.asarray(raw.x_global)).objective

        self.assertAlmostEqual(observed, problem.metadata.known_optimum, places=8)

    def test_missing_function_and_unsupported_dimension_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "does not expose"):
            OpfunuCECProblem(2014, 999, 10)
        with self.assertRaisesRegex(ValueError, "does not support dimension"):
            OpfunuCECProblem(2015, 1, 20)


if __name__ == "__main__":
    unittest.main()
