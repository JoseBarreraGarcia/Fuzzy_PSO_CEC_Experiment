"""Controller-free numerical transition for global-best PSO."""

from __future__ import annotations

from dataclasses import dataclass
import math

import numpy as np


@dataclass(frozen=True, slots=True)
class PSOConfig:
    """Coefficients used by the common PSO velocity equation."""

    cognitive: float = 2.0
    social: float = 2.0

    def __post_init__(self) -> None:
        for name, value in (("cognitive", self.cognitive), ("social", self.social)):
            if not math.isfinite(float(value)) or value < 0:
                raise ValueError(f"{name} must be finite and non-negative")


@dataclass(frozen=True, slots=True)
class PSOStepResult:
    positions: np.ndarray
    velocities: np.ndarray


def advance_swarm(
    *,
    positions: np.ndarray,
    velocities: np.ndarray,
    personal_best: np.ndarray,
    global_best: np.ndarray,
    inertia: float,
    cognitive_random: np.ndarray,
    social_random: np.ndarray,
    maximum_velocity: float | np.ndarray,
    config: PSOConfig = PSOConfig(),
) -> PSOStepResult:
    """Apply one legacy-compatible PSO movement without evaluation or RNG."""

    positions = np.asarray(positions, dtype=float)
    velocities = np.asarray(velocities, dtype=float)
    personal_best = np.asarray(personal_best, dtype=float)
    global_best = np.asarray(global_best, dtype=float)
    cognitive_random = np.asarray(cognitive_random, dtype=float)
    social_random = np.asarray(social_random, dtype=float)

    expected_shape = positions.shape
    if positions.ndim != 2:
        raise ValueError("positions must be a two-dimensional matrix")
    for name, value in (
        ("velocities", velocities),
        ("personal_best", personal_best),
        ("cognitive_random", cognitive_random),
        ("social_random", social_random),
    ):
        if value.shape != expected_shape:
            raise ValueError(f"{name} must have shape {expected_shape}")
    if global_best.shape not in {(expected_shape[1],), (1, expected_shape[1])}:
        raise ValueError("global_best has an incompatible shape")
    for name, value in (
        ("positions", positions),
        ("velocities", velocities),
        ("personal_best", personal_best),
        ("global_best", global_best),
        ("cognitive_random", cognitive_random),
        ("social_random", social_random),
    ):
        if not np.all(np.isfinite(value)):
            raise ValueError(f"{name} must contain only finite values")
    inertia = float(inertia)
    if not math.isfinite(inertia):
        raise ValueError("inertia must be finite")
    maximum_velocity = np.asarray(maximum_velocity, dtype=float)
    if not np.all(np.isfinite(maximum_velocity)) or np.any(maximum_velocity < 0):
        raise ValueError("maximum_velocity must be finite and non-negative")

    new_velocities = (
        inertia * velocities
        + config.cognitive
        * cognitive_random
        * (personal_best - positions)
        + config.social
        * social_random
        * (global_best - positions)
    )
    new_velocities = np.clip(
        new_velocities, -maximum_velocity, maximum_velocity
    )
    return PSOStepResult(
        positions=positions + new_velocities,
        velocities=new_velocities,
    )

