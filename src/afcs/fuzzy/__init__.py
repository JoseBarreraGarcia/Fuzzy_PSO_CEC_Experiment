"""Versioned fuzzy-logic primitives independent from optimizers."""

from .mamdani import FuzzyInferenceResult, MamdaniController, RULE_PATTERNS, rule_matrix
from .membership import (
    MembershipFunction,
    SUPPORTED_MEMBERSHIP_FAMILIES,
    SUPPORTED_OVERLAP_DEFINITIONS,
    fuzzify,
    uniform_partition,
)

__all__ = [
    "FuzzyInferenceResult",
    "MamdaniController",
    "MembershipFunction",
    "RULE_PATTERNS",
    "SUPPORTED_MEMBERSHIP_FAMILIES",
    "SUPPORTED_OVERLAP_DEFINITIONS",
    "fuzzify",
    "rule_matrix",
    "uniform_partition",
]
