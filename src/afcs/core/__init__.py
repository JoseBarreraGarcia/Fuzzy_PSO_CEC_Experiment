"""Shared domain contracts for AFCS experiments."""

from .domain import (
    BudgetExceededError,
    Evaluation,
    EvaluationBudget,
    OptimizationDirection,
    SearchSpace,
)

__all__ = [
    "BudgetExceededError",
    "Evaluation",
    "EvaluationBudget",
    "OptimizationDirection",
    "SearchSpace",
]

