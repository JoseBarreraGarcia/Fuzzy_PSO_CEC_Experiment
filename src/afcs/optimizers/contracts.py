"""Method-neutral contracts shared by optimizers and parameter policies."""

from __future__ import annotations

from dataclasses import dataclass, field
import math
from types import MappingProxyType
from typing import Any, Mapping


@dataclass(frozen=True, slots=True)
class OptimizerMetadata:
    """Stable identity and declared parameter capabilities of an optimizer."""

    optimizer_id: str
    version: str
    configurable_parameters: tuple[str, ...]
    adaptable_parameters: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.optimizer_id, str) or not self.optimizer_id.strip():
            raise ValueError("optimizer_id must be a non-empty string")
        if not isinstance(self.version, str) or not self.version.strip():
            raise ValueError("version must be a non-empty string")
        configurable = tuple(self.configurable_parameters)
        adaptable = tuple(self.adaptable_parameters)
        if len(configurable) != len(set(configurable)):
            raise ValueError("configurable_parameters contains duplicates")
        if len(adaptable) != len(set(adaptable)):
            raise ValueError("adaptable_parameters contains duplicates")
        unknown = set(adaptable) - set(configurable)
        if unknown:
            raise ValueError(
                f"Adaptable parameters must be configurable: {sorted(unknown)}"
            )
        object.__setattr__(self, "configurable_parameters", configurable)
        object.__setattr__(self, "adaptable_parameters", adaptable)


@dataclass(frozen=True, slots=True)
class SearchState:
    """Read-only information observable before one optimizer transition."""

    iteration: int
    evaluations: int
    evaluation_budget: int
    best_objective: float
    elapsed_seconds: float = 0.0
    observations: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for name, value in (
            ("iteration", self.iteration),
            ("evaluations", self.evaluations),
            ("evaluation_budget", self.evaluation_budget),
        ):
            if isinstance(value, bool) or not isinstance(value, int):
                raise TypeError(f"{name} must be an integer")
        if self.iteration < 0 or self.evaluations < 0:
            raise ValueError("iteration and evaluations cannot be negative")
        if self.evaluation_budget <= 0:
            raise ValueError("evaluation_budget must be positive")
        if self.evaluations > self.evaluation_budget:
            raise ValueError("evaluations cannot exceed evaluation_budget")
        if not math.isfinite(float(self.best_objective)):
            raise ValueError("best_objective must be finite")
        if not math.isfinite(float(self.elapsed_seconds)) or self.elapsed_seconds < 0:
            raise ValueError("elapsed_seconds must be finite and non-negative")
        if not isinstance(self.observations, Mapping):
            raise TypeError("observations must be a mapping")
        object.__setattr__(
            self, "observations", MappingProxyType(dict(self.observations))
        )

    @property
    def progress(self) -> float:
        return self.evaluations / self.evaluation_budget

