"""Small contracts used by experiment execution orchestration."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Protocol, runtime_checkable


@runtime_checkable
class OptimizationRunResult(Protocol):
    """Minimum final result required for persistent experiment execution."""

    best_position: Iterable[float]
    best_objective: float
    evaluations: int


@runtime_checkable
class RunnableOptimizer(Protocol):
    """One fully configured optimizer ready to execute exactly one replica."""

    def run(self) -> OptimizationRunResult:
        ...
