from __future__ import annotations

import unittest

from afcs.core import Evaluation, OptimizationDirection, ReplicaRandomStreams, SearchSpace
from afcs.problems import CallableProblem, ProblemFactory, ProblemMetadata


class TestProblemFactory(unittest.TestCase):
    def setUp(self) -> None:
        self.streams = ReplicaRandomStreams(42)

    def test_default_factory_builds_all_supported_mathematical_families(self):
        factory = ProblemFactory()
        specifications = (
            ("CEC2017", 10, {"function_number": 1}, "F1CEC2017"),
            ("CLASSICAL", 5, {"function_number": 1}, "F1"),
            (
                "OPFUNU_CEC",
                10,
                {"suite_year": 2014, "function_number": 1},
                "F1CEC2014_OPFUNU",
            ),
        )

        for family, dimension, parameters, expected_id in specifications:
            with self.subTest(family=family):
                problem = factory.build(
                    family=family,
                    dimension=dimension,
                    parameters=parameters,
                    random_streams=self.streams,
                )
                self.assertEqual(problem.metadata.problem_id, expected_id)
                self.assertEqual(problem.metadata.family, family)

    def test_stochastic_problem_stream_is_reproducible(self):
        first = ProblemFactory().build(
            family="CLASSICAL",
            dimension=3,
            parameters={"function_number": 7},
            random_streams=ReplicaRandomStreams(77),
        )
        second = ProblemFactory().build(
            family="CLASSICAL",
            dimension=3,
            parameters={"function_number": 7},
            random_streams=ReplicaRandomStreams(77),
        )

        self.assertEqual(
            first.evaluate((0.1, 0.2, 0.3)).objective,
            second.evaluate((0.1, 0.2, 0.3)).objective,
        )

    def test_custom_family_requires_no_optimizer_change(self):
        def build_fixture(dimension, parameters, random_streams):
            del parameters, random_streams
            return CallableProblem(
                ProblemMetadata(
                    problem_id="ENGINEERING_FIXTURE",
                    family="ENGINEERING_CONTINUOUS",
                    search_space=SearchSpace((-1.0,) * dimension, (1.0,) * dimension),
                    direction=OptimizationDirection.MINIMIZE,
                ),
                lambda candidate: Evaluation(sum(value * value for value in candidate)),
            )

        problem = ProblemFactory(
            {"ENGINEERING_CONTINUOUS": build_fixture}
        ).build(
            family="ENGINEERING_CONTINUOUS",
            dimension=2,
            parameters={},
            random_streams=self.streams,
        )

        self.assertEqual(problem.evaluate((0.5, -0.5)).objective, 0.5)

    def test_builder_cannot_return_mismatched_identity(self):
        def wrong_family(dimension, parameters, random_streams):
            del parameters, random_streams
            return CallableProblem(
                ProblemMetadata(
                    problem_id="wrong",
                    family="OTHER",
                    search_space=SearchSpace((0.0,) * dimension, (1.0,) * dimension),
                ),
                lambda candidate: 0.0,
            )

        with self.assertRaisesRegex(ValueError, "different family"):
            ProblemFactory({"EXPECTED": wrong_family}).build(
                family="EXPECTED",
                dimension=2,
                parameters={},
                random_streams=self.streams,
            )


if __name__ == "__main__":
    unittest.main()
