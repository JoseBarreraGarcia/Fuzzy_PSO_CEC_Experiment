"""Method-neutral contracts shared by optimizers and parameter policies."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Mapping

from afcs.core import Evaluation
from afcs.core.randomness import MAX_SEED
from afcs.core.serialization import freeze_json_mapping
from afcs.problems import ProblemMetadata


def unconstrained_objective(evaluation: Evaluation) -> float:
    """Reject constraint evidence rather than silently selecting by objective alone."""

    if not evaluation.feasible or evaluation.constraint_violation != 0:
        raise ValueError(
            "This optimizer does not support constraints; use an explicit constrained optimizer"
        )
    return evaluation.objective


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


@dataclass(frozen=True, slots=True)
class OptimizerRunMetadata:
    """Canonical description of one configured optimizer execution."""

    optimizer: OptimizerMetadata
    problem: ProblemMetadata
    parameters: Mapping[str, Any]
    evaluation_budget: int
    iteration_budget: int | None
    population_size: int | None
    replica_seed: int | None = None
    rng_engine: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.optimizer, OptimizerMetadata):
            raise TypeError("optimizer must be OptimizerMetadata")
        if not isinstance(self.problem, ProblemMetadata):
            raise TypeError("problem must be ProblemMetadata")
        if not isinstance(self.parameters, Mapping):
            raise TypeError("parameters must be a mapping")
        for name, value, optional in (
            ("evaluation_budget", self.evaluation_budget, False),
            ("iteration_budget", self.iteration_budget, True),
            ("population_size", self.population_size, True),
        ):
            if value is None and optional:
                continue
            if isinstance(value, bool) or not isinstance(value, int):
                raise TypeError(f"{name} must be an integer")
            if value <= 0:
                raise ValueError(f"{name} must be positive")
        if self.replica_seed is not None:
            if isinstance(self.replica_seed, bool) or not isinstance(
                self.replica_seed, int
            ):
                raise TypeError("replica_seed must be an integer or None")
            if not 0 <= self.replica_seed <= MAX_SEED:
                raise ValueError(f"replica_seed must be between 0 and {MAX_SEED}")
            if not isinstance(self.rng_engine, str) or not self.rng_engine:
                raise ValueError("rng_engine is required with replica_seed")
        elif self.rng_engine is not None:
            raise ValueError("rng_engine requires replica_seed")
        object.__setattr__(self, "parameters", freeze_json_mapping(self.parameters))
