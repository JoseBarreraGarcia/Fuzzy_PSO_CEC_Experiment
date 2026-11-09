"""Particle Swarm Optimization core and parameter policies."""

from .core import PSOConfig, PSOStepResult, advance_swarm
from .optimizer import (
    PSO_DOMAIN_WIDTH_VERSION,
    PSO_IMPLEMENTATION_VERSION,
    LegacyCompatiblePSO,
    LegacyPSORunConfig,
    PSORunResult,
)
from .policies import (
    EndpointLinearInertia,
    FixedInertia,
    FuzzyInertiaPolicy,
    LegacyLinearInertia,
)

__all__ = [
    "FixedInertia",
    "EndpointLinearInertia",
    "FuzzyInertiaPolicy",
    "LegacyCompatiblePSO",
    "LegacyLinearInertia",
    "LegacyPSORunConfig",
    "PSOConfig",
    "PSO_IMPLEMENTATION_VERSION",
    "PSO_DOMAIN_WIDTH_VERSION",
    "PSORunResult",
    "PSOStepResult",
    "advance_swarm",
]
