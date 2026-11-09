"""Contracts for optional, observable-state parameter adaptation."""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Protocol, runtime_checkable

from afcs.optimizers import SearchState


@dataclass(frozen=True, slots=True)
class ParameterUpdate:
    """One explicit proposal to change optimizer parameters."""

    policy_id: str
    policy_version: str
    values: Mapping[str, float] = field(default_factory=dict)
    reason: str | None = None

    def __post_init__(self) -> None:
        if not self.policy_id.strip() or not self.policy_version.strip():
            raise ValueError("Policy identity and version must be non-empty")
        if not isinstance(self.values, Mapping):
            raise TypeError("values must be a mapping")
        normalized: dict[str, float] = {}
        for name, value in self.values.items():
            if not isinstance(name, str) or not name:
                raise ValueError("Parameter names must be non-empty strings")
            if isinstance(value, bool):
                raise TypeError(f"Parameter {name!r} must be numeric")
            try:
                numeric = float(value)
            except (TypeError, ValueError) as error:
                raise TypeError(f"Parameter {name!r} must be numeric") from error
            if not math.isfinite(numeric):
                raise ValueError(f"Parameter {name!r} must be finite")
            normalized[name] = numeric
        object.__setattr__(self, "values", MappingProxyType(normalized))


@runtime_checkable
class ParameterPolicy(Protocol):
    """A policy that may propose parameter changes from current observations."""

    policy_id: str
    policy_version: str

    @property
    def compatible_parameters(self) -> tuple[str, ...]: ...

    @property
    def configuration(self) -> Mapping[str, Any]: ...

    def propose(
        self,
        state: SearchState,
        current_parameters: Mapping[str, float],
    ) -> ParameterUpdate: ...


class NoAdaptation:
    """Explicit policy for an optimizer executed without external adaptation."""

    policy_id = "no_adaptation"
    policy_version = "1"
    compatible_parameters: tuple[str, ...] = ()

    @property
    def configuration(self) -> Mapping[str, Any]:
        return MappingProxyType({})

    def propose(
        self,
        state: SearchState,
        current_parameters: Mapping[str, float],
    ) -> ParameterUpdate:
        if not isinstance(state, SearchState):
            raise TypeError("state must be SearchState")
        if not isinstance(current_parameters, Mapping):
            raise TypeError("current_parameters must be a mapping")
        return ParameterUpdate(self.policy_id, self.policy_version)
