"""Method-neutral value objects shared by the v2 architecture."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping, Sequence


class OptimizationDirection(str, Enum):
    """Direction in which objective values improve."""

    MINIMIZE = "minimize"
    MAXIMIZE = "maximize"

    def is_better(self, candidate: float, incumbent: float) -> bool:
        candidate = _finite_float(candidate, "candidate")
        incumbent = _finite_float(incumbent, "incumbent")
        if self is OptimizationDirection.MINIMIZE:
            return candidate < incumbent
        return candidate > incumbent


@dataclass(frozen=True, slots=True)
class SearchSpace:
    """Finite box domain for a fixed-dimensional real-valued problem."""

    lower_bounds: tuple[float, ...]
    upper_bounds: tuple[float, ...]

    def __post_init__(self) -> None:
        lower = tuple(
            _finite_float(value, "lower bound") for value in self.lower_bounds
        )
        upper = tuple(
            _finite_float(value, "upper bound") for value in self.upper_bounds
        )
        if not lower:
            raise ValueError("A search space must have at least one dimension")
        if len(lower) != len(upper):
            raise ValueError("Lower and upper bounds must have the same dimension")
        if any(low >= high for low, high in zip(lower, upper, strict=True)):
            raise ValueError("Every lower bound must be smaller than its upper bound")
        object.__setattr__(self, "lower_bounds", lower)
        object.__setattr__(self, "upper_bounds", upper)

    @classmethod
    def uniform(cls, dimension: int, lower: float, upper: float) -> "SearchSpace":
        if (
            isinstance(dimension, bool)
            or not isinstance(dimension, int)
            or dimension <= 0
        ):
            raise ValueError("dimension must be a positive integer")
        return cls((lower,) * dimension, (upper,) * dimension)

    @property
    def dimension(self) -> int:
        return len(self.lower_bounds)

    def normalize_candidate(self, candidate: Sequence[float]) -> tuple[float, ...]:
        if len(candidate) != self.dimension:
            raise ValueError(
                f"Expected candidate dimension {self.dimension}, got {len(candidate)}"
            )
        return tuple(
            _finite_float(value, "candidate coordinate") for value in candidate
        )

    def contains(self, candidate: Sequence[float]) -> bool:
        values = self.normalize_candidate(candidate)
        return all(
            low <= value <= high
            for value, low, high in zip(
                values, self.lower_bounds, self.upper_bounds, strict=True
            )
        )


@dataclass(frozen=True, slots=True)
class Evaluation:
    """Result of one objective-function evaluation."""

    objective: float
    feasible: bool = True
    constraint_violation: float = 0.0
    details: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        objective = _finite_float(self.objective, "objective")
        violation = _finite_float(self.constraint_violation, "constraint violation")
        if violation < 0.0:
            raise ValueError("constraint_violation cannot be negative")
        if not isinstance(self.feasible, bool):
            raise TypeError("feasible must be a boolean")
        if not isinstance(self.details, Mapping):
            raise TypeError("details must be a mapping")
        object.__setattr__(self, "objective", objective)
        object.__setattr__(self, "constraint_violation", violation)
        object.__setattr__(self, "details", MappingProxyType(dict(self.details)))


class BudgetExceededError(RuntimeError):
    """Raised when an operation would exceed its evaluation budget."""


@dataclass(slots=True)
class EvaluationBudget:
    """Explicit counter for objective-function evaluations (NFE)."""

    maximum: int
    consumed: int = 0

    def __post_init__(self) -> None:
        _positive_integer(self.maximum, "maximum")
        if isinstance(self.consumed, bool) or not isinstance(self.consumed, int):
            raise TypeError("consumed must be an integer")
        if self.consumed < 0 or self.consumed > self.maximum:
            raise ValueError("consumed must be between zero and maximum")

    @property
    def remaining(self) -> int:
        return self.maximum - self.consumed

    @property
    def exhausted(self) -> bool:
        return self.consumed == self.maximum

    def consume(self, amount: int = 1) -> int:
        _positive_integer(amount, "amount")
        if amount > self.remaining:
            raise BudgetExceededError(
                f"Cannot consume {amount} evaluations; only {self.remaining} remain"
            )
        self.consumed += amount
        return self.consumed


def _finite_float(value: float, label: str) -> float:
    if isinstance(value, bool):
        raise TypeError(f"{label} must be numeric")
    try:
        normalized = float(value)
    except (TypeError, ValueError) as exc:
        raise TypeError(f"{label} must be numeric") from exc
    if not math.isfinite(normalized):
        raise ValueError(f"{label} must be finite")
    return normalized


def _positive_integer(value: int, label: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{label} must be an integer")
    if value <= 0:
        raise ValueError(f"{label} must be positive")
