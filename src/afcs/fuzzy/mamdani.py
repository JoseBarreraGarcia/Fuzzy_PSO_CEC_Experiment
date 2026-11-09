"""Pure Mamdani inference used by versioned parameter-control policies."""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from .membership import fuzzify, uniform_partition

RULE_PATTERNS = {
    "R1": ("decreasing", "agnostic"),
    "R2": ("increasing", "agnostic"),
    "R3": ("agnostic", "following"),
    "R4": ("agnostic", "compensating"),
    "R5": ("decreasing", "following"),
    "R6": ("decreasing", "compensating"),
    "R7": ("increasing", "following"),
    "R8": ("increasing", "compensating"),
}


@dataclass(frozen=True, slots=True)
class FuzzyInferenceResult:
    normalized_output: float
    diversity_degrees: tuple[float, ...]
    progress_degrees: tuple[float, ...]
    active_rules: tuple[tuple[int, int, int, float], ...]
    boundary_events: int
    evaluated_rule_count: int
    skipped_rule_count: int


def rule_matrix(rule_base: str, granularity: int) -> tuple[tuple[int, ...], ...]:
    try:
        progress_pattern, diversity_pattern = RULE_PATTERNS[rule_base]
    except KeyError as error:
        raise ValueError(f"rule_base must be one of {list(RULE_PATTERNS)}") from error
    if granularity < 3 or granularity % 2 == 0:
        raise ValueError("granularity must be an odd integer >= 3")
    center = (granularity - 1) // 2

    def progress_effect(index: int) -> int:
        if progress_pattern == "decreasing":
            return center - index
        if progress_pattern == "increasing":
            return index - center
        return 0

    def diversity_effect(index: int) -> int:
        if diversity_pattern == "following":
            return index - center
        if diversity_pattern == "compensating":
            return center - index
        return 0

    matrix: list[tuple[int, ...]] = []
    for diversity_index in range(granularity):
        row = []
        for progress_index in range(granularity):
            p_effect = progress_effect(progress_index)
            d_effect = diversity_effect(diversity_index)
            if progress_pattern == "agnostic":
                output = center + d_effect
            elif diversity_pattern == "agnostic":
                output = center + p_effect
            else:
                total = p_effect + d_effect
                if total > 0:
                    output = center + math.ceil(total / 2.0)
                elif total < 0:
                    output = center - math.ceil(-total / 2.0)
                else:
                    output = center
            row.append(max(0, min(granularity - 1, int(output))))
        matrix.append(tuple(row))
    return tuple(matrix)


class MamdaniController:
    """Two-input min-max Mamdani controller with centroid defuzzification."""

    controller_id = "mamdani_min_max_centroid"
    version = "1"

    def __init__(
        self,
        *,
        granularity: int,
        rule_base: str,
        membership_family: str,
        diversity_overlap: float,
        progress_overlap: float,
        output_overlap: float,
        zero_overlap_boundary_policy: str = "nearest_center_tie_upper",
        centroid_grid_points: int = 501,
        evaluation_mode: str = "dense_v1",
    ) -> None:
        if centroid_grid_points < 101 or centroid_grid_points % 2 == 0:
            raise ValueError("centroid_grid_points must be an odd integer >= 101")
        self.granularity = granularity
        self.rule_base = rule_base
        self.membership_family = membership_family
        self.zero_overlap_boundary_policy = zero_overlap_boundary_policy
        if evaluation_mode not in {"dense_v1", "sparse_v1"}:
            raise ValueError("evaluation_mode must be 'dense_v1' or 'sparse_v1'")
        self.evaluation_mode = evaluation_mode
        self.diversity_partition = uniform_partition(
            granularity=granularity,
            family=membership_family,
            overlap=diversity_overlap,
        )
        self.progress_partition = uniform_partition(
            granularity=granularity,
            family=membership_family,
            overlap=progress_overlap,
        )
        self.output_partition = uniform_partition(
            granularity=granularity,
            family=membership_family,
            overlap=output_overlap,
        )
        self.rules = rule_matrix(rule_base, granularity)
        self.grid = np.linspace(0.0, 1.0, centroid_grid_points)
        self._output_values = tuple(
            np.fromiter(
                (membership.degree(value) for value in self.grid),
                dtype=float,
                count=centroid_grid_points,
            )
            for membership in self.output_partition
        )
        centroids = tuple(self._centroid(values) for values in self._output_values)
        self._centroid_min = min(centroids)
        self._centroid_max = max(centroids)

    def infer(self, diversity: float, progress: float) -> FuzzyInferenceResult:
        diversity_degrees, diversity_boundary = fuzzify(
            diversity,
            self.diversity_partition,
            zero_overlap_boundary_policy=self.zero_overlap_boundary_policy,
        )
        progress_degrees, progress_boundary = fuzzify(
            progress,
            self.progress_partition,
            zero_overlap_boundary_policy=self.zero_overlap_boundary_policy,
        )
        aggregate = np.zeros_like(self.grid)
        active_rules: list[tuple[int, int, int, float]] = []
        if self.evaluation_mode == "dense_v1":
            diversity_indices = range(self.granularity)
            progress_indices = range(self.granularity)
        else:
            diversity_indices = tuple(
                index for index, degree in enumerate(diversity_degrees) if degree > 0.0
            )
            progress_indices = tuple(
                index for index, degree in enumerate(progress_degrees) if degree > 0.0
            )
        evaluated_rule_count = len(diversity_indices) * len(progress_indices)
        total_rule_count = self.granularity * self.granularity
        for diversity_index in diversity_indices:
            diversity_degree = diversity_degrees[diversity_index]
            for progress_index in progress_indices:
                progress_degree = progress_degrees[progress_index]
                firing = min(diversity_degree, progress_degree)
                if firing <= 0.0:
                    continue
                output_index = self.rules[diversity_index][progress_index]
                aggregate = np.maximum(
                    aggregate,
                    np.minimum(firing, self._output_values[output_index]),
                )
                active_rules.append(
                    (diversity_index, progress_index, output_index, float(firing))
                )
        denominator = float(np.trapezoid(aggregate, self.grid))
        if denominator <= 1e-12:
            raise RuntimeError("Mamdani inference produced an empty output set")
        centroid = float(np.trapezoid(self.grid * aggregate, self.grid) / denominator)
        span = self._centroid_max - self._centroid_min
        if span <= 1e-12:
            raise RuntimeError("output partition has a degenerate centroid range")
        normalized = min(1.0, max(0.0, (centroid - self._centroid_min) / span))
        return FuzzyInferenceResult(
            normalized_output=normalized,
            diversity_degrees=diversity_degrees,
            progress_degrees=progress_degrees,
            active_rules=tuple(active_rules),
            boundary_events=int(diversity_boundary) + int(progress_boundary),
            evaluated_rule_count=evaluated_rule_count,
            skipped_rule_count=total_rule_count - evaluated_rule_count,
        )

    def _centroid(self, values: np.ndarray) -> float:
        denominator = float(np.trapezoid(values, self.grid))
        if denominator <= 1e-12:
            raise ValueError("output membership function has zero area")
        return float(np.trapezoid(self.grid * values, self.grid) / denominator)
