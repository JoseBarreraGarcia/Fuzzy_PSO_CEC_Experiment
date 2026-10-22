"""Particle Swarm Optimization core and parameter policies."""

from .core import PSOConfig, PSOStepResult, advance_swarm
from .policies import LegacyLinearInertia

__all__ = [
    "LegacyLinearInertia",
    "PSOConfig",
    "PSOStepResult",
    "advance_swarm",
]

