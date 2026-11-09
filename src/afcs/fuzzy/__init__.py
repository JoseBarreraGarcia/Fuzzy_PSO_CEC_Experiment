"""Versioned fuzzy-logic primitives independent from optimizers."""

from .mamdani import RULE_PATTERNS, FuzzyInferenceResult, MamdaniController, rule_matrix
from .membership import (
    SUPPORTED_MEMBERSHIP_FAMILIES,
    SUPPORTED_OVERLAP_DEFINITIONS,
    MembershipFunction,
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
