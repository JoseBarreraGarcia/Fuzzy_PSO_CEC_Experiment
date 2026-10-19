import sys
from pathlib import Path
import unittest


SRC = Path(__file__).resolve().parents[1] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from afcs.core import (  # noqa: E402
    BudgetExceededError,
    Evaluation,
    EvaluationBudget,
    OptimizationDirection,
    SearchSpace,
)
from afcs.problems import CallableProblem, OptimizationProblem, ProblemMetadata  # noqa: E402


class TestCoreContracts(unittest.TestCase):
    def test_direction_compares_without_hidden_tolerance(self):
        self.assertTrue(OptimizationDirection.MINIMIZE.is_better(1.0, 2.0))
        self.assertTrue(OptimizationDirection.MAXIMIZE.is_better(2.0, 1.0))
        self.assertFalse(OptimizationDirection.MINIMIZE.is_better(1.0, 1.0))

    def test_uniform_search_space_validates_candidates(self):
        space = SearchSpace.uniform(dimension=3, lower=-5.0, upper=5.0)
        self.assertEqual(space.dimension, 3)
        self.assertTrue(space.contains((-5.0, 0.0, 5.0)))
        self.assertFalse(space.contains((0.0, 0.0, 6.0)))
        with self.assertRaisesRegex(ValueError, "dimension"):
            space.normalize_candidate((1.0, 2.0))
        with self.assertRaisesRegex(ValueError, "finite"):
            space.normalize_candidate((1.0, float("nan"), 2.0))

    def test_evaluation_is_finite_and_details_are_immutable(self):
        details = {"source": "observed"}
        result = Evaluation(1.5, details=details)
        details["source"] = "changed"
        self.assertEqual(result.details["source"], "observed")
        with self.assertRaises(TypeError):
            result.details["new"] = "value"
        with self.assertRaisesRegex(ValueError, "finite"):
            Evaluation(float("inf"))
        with self.assertRaisesRegex(ValueError, "negative"):
            Evaluation(1.0, constraint_violation=-1.0)

    def test_budget_never_overruns(self):
        budget = EvaluationBudget(maximum=3)
        self.assertEqual(budget.consume(2), 2)
        self.assertEqual(budget.remaining, 1)
        with self.assertRaises(BudgetExceededError):
            budget.consume(2)
        self.assertEqual(budget.consumed, 2)
        budget.consume()
        self.assertTrue(budget.exhausted)

    def test_callable_problem_implements_structural_contract(self):
        metadata = ProblemMetadata(
            problem_id="sphere-2d",
            family="synthetic",
            search_space=SearchSpace.uniform(2, -5.0, 5.0),
            known_optimum=0.0,
            parameters={"formula": "sum(x_i^2)"},
        )
        problem = CallableProblem(metadata, lambda x: sum(value**2 for value in x))
        self.assertIsInstance(problem, OptimizationProblem)
        self.assertEqual(problem.evaluate((3.0, 4.0)).objective, 25.0)
        self.assertEqual(problem.metadata.dimension, 2)
        with self.assertRaisesRegex(ValueError, "dimension"):
            problem.evaluate((1.0,))

    def test_problem_can_return_constraint_information(self):
        metadata = ProblemMetadata(
            problem_id="constrained",
            family="synthetic",
            search_space=SearchSpace.uniform(1, 0.0, 10.0),
        )
        problem = CallableProblem(
            metadata,
            lambda x: Evaluation(
                objective=x[0],
                feasible=False,
                constraint_violation=2.0,
                details={"repair_applied": False},
            ),
        )
        result = problem.evaluate((4.0,))
        self.assertFalse(result.feasible)
        self.assertEqual(result.constraint_violation, 2.0)


if __name__ == "__main__":
    unittest.main()

