"""PSO-specific parameter policies."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
import math

from afcs.controllers import ParameterUpdate
from afcs.optimizers import SearchState


@dataclass(frozen=True, slots=True)
class LegacyLinearInertia:
    """Historical 0.9→0.1 schedule retained only for compatibility."""

    max_iterations: int
    maximum: float = 0.9
    minimum: float = 0.1

    policy_id = "legacy_ldiw"
    policy_version = "1"
    compatible_parameters = ("w",)

    def __post_init__(self) -> None:
        if (
            isinstance(self.max_iterations, bool)
            or not isinstance(self.max_iterations, int)
            or self.max_iterations <= 0
        ):
            raise ValueError("max_iterations must be a positive integer")
        if not math.isfinite(self.maximum) or not math.isfinite(self.minimum):
            raise ValueError("Inertia bounds must be finite")
        if self.minimum > self.maximum:
            raise ValueError("minimum inertia cannot exceed maximum inertia")

    def value_at(self, iteration: int) -> float:
        if isinstance(iteration, bool) or not isinstance(iteration, int):
            raise TypeError("iteration must be an integer")
        if iteration < 0 or iteration > self.max_iterations:
            raise ValueError("iteration must be between zero and max_iterations")
        return self.maximum - iteration * (
            (self.maximum - self.minimum) / self.max_iterations
        )

    def propose(
        self,
        state: SearchState,
        current_parameters: Mapping[str, float],
    ) -> ParameterUpdate:
        if not isinstance(state, SearchState):
            raise TypeError("state must be SearchState")
        return ParameterUpdate(
            policy_id=self.policy_id,
            policy_version=self.policy_version,
            values={"w": self.value_at(state.iteration)},
            reason="historical linear inertia schedule",
        )

