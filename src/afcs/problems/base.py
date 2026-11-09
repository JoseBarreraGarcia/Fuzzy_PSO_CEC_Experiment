"""Common contract implemented by optimization problems."""

from __future__ import annotations

import math
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable

from afcs.core import Evaluation, OptimizationDirection, SearchSpace
from afcs.core.serialization import freeze_json_mapping


@dataclass(frozen=True, slots=True)
class ProblemMetadata:
    """Stable identity and provenance fields for one problem instance."""

    problem_id: str
    family: str
    search_space: SearchSpace
    direction: OptimizationDirection = OptimizationDirection.MINIMIZE
    known_optimum: float | None = None
    parameters: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.problem_id, str) or not self.problem_id.strip():
            raise ValueError("problem_id must be a non-empty string")
        if not isinstance(self.family, str) or not self.family.strip():
            raise ValueError("family must be a non-empty string")
        if not isinstance(self.search_space, SearchSpace):
            raise TypeError("search_space must be a SearchSpace")
        if not isinstance(self.direction, OptimizationDirection):
            raise TypeError("direction must be an OptimizationDirection")
        optimum = self.known_optimum
        if optimum is not None:
            if isinstance(optimum, bool) or not isinstance(optimum, (int, float)):
                raise TypeError("known_optimum must be numeric or None")
            optimum = float(optimum)
            if not math.isfinite(optimum):
                raise ValueError("known_optimum must be finite")
            object.__setattr__(self, "known_optimum", optimum)
        if not isinstance(self.parameters, Mapping):
            raise TypeError("parameters must be a mapping")
        object.__setattr__(self, "parameters", freeze_json_mapping(self.parameters))

    @property
    def dimension(self) -> int:
        return self.search_space.dimension


@runtime_checkable
class OptimizationProblem(Protocol):
    """Structural interface consumed by optimizers and experiment runners."""

    @property
    def metadata(self) -> ProblemMetadata: ...

    def evaluate(self, candidate: Sequence[float]) -> Evaluation: ...


class CallableProblem:
    """Adapt a scalar objective callable to the common problem contract."""

    def __init__(
        self,
        metadata: ProblemMetadata,
        objective: Callable[[tuple[float, ...]], float | Evaluation],
    ) -> None:
        if not isinstance(metadata, ProblemMetadata):
            raise TypeError("metadata must be ProblemMetadata")
        if not callable(objective):
            raise TypeError("objective must be callable")
        self._metadata = metadata
        self._objective = objective

    @property
    def metadata(self) -> ProblemMetadata:
        return self._metadata

    def evaluate(self, candidate: Sequence[float]) -> Evaluation:
        values = self.metadata.search_space.normalize_candidate(candidate)
        result = self._objective(values)
        if isinstance(result, Evaluation):
            return result
        return Evaluation(objective=result)
