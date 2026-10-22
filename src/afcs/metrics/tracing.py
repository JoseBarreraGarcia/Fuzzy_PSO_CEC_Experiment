"""Versioned population metrics and immutable optimization trace points."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
import math
from types import MappingProxyType

import numpy as np


PSO_TRACE_METRICS = frozenset(
    {
        "iteration_index",
        "iteration_time_seconds",
        "objective_best",
        "evaluations",
        "objective_mean",
        "objective_std",
        "diversity_hussain",
        "exploration_percent",
        "exploitation_percent",
        "population_entropy",
        "diversity_dimension_mean",
        "diversity_dimension_min",
        "diversity_dimension_max",
        "inertia_weight",
    }
)


@dataclass(frozen=True, slots=True)
class TraceSampling:
    enabled: bool = True
    every_iterations: int = 1
    include_initial: bool = True
    include_final: bool = True

    def __post_init__(self) -> None:
        if not isinstance(self.enabled, bool):
            raise TypeError("enabled must be boolean")
        if isinstance(self.every_iterations, bool) or not isinstance(
            self.every_iterations, int
        ):
            raise TypeError("every_iterations must be an integer")
        if self.every_iterations <= 0:
            raise ValueError("every_iterations must be positive")
        if not isinstance(self.include_initial, bool) or not isinstance(
            self.include_final, bool
        ):
            raise TypeError("trace inclusion flags must be boolean")
        if self.enabled and not self.include_final:
            raise ValueError("include_final must be true when tracing is enabled")

    def includes(self, iteration: int, maximum_iteration: int) -> bool:
        if not self.enabled:
            return False
        if iteration == 0:
            return self.include_initial
        return (
            iteration % self.every_iterations == 0
            or iteration == maximum_iteration
        )


@dataclass(frozen=True, slots=True)
class OptimizationTracePoint:
    checkpoint_index: int
    iteration_index: int
    evaluations: int
    elapsed_seconds: float
    metrics: Mapping[str, object]

    def __post_init__(self) -> None:
        for name, value in (
            ("checkpoint_index", self.checkpoint_index),
            ("iteration_index", self.iteration_index),
            ("evaluations", self.evaluations),
        ):
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ValueError(f"{name} must be a non-negative integer")
        if not math.isfinite(self.elapsed_seconds) or self.elapsed_seconds < 0:
            raise ValueError("elapsed_seconds must be finite and non-negative")
        object.__setattr__(self, "metrics", MappingProxyType(dict(self.metrics)))


class PSOTraceCollector:
    """Collect selected PSO metrics without influencing swarm dynamics."""

    def __init__(
        self,
        *,
        selected_metrics: Iterable[str],
        sampling: TraceSampling,
        maximum_iteration: int,
        lower_bounds: Iterable[float],
        upper_bounds: Iterable[float],
    ) -> None:
        self._selected = frozenset(selected_metrics).intersection(PSO_TRACE_METRICS)
        self._sampling = sampling
        self._maximum_iteration = maximum_iteration
        self._lower = np.asarray(tuple(lower_bounds), dtype=float)
        self._upper = np.asarray(tuple(upper_bounds), dtype=float)
        self._maximum_diversity = 0.0
        self._points: list[OptimizationTracePoint] = []

    @property
    def points(self) -> tuple[OptimizationTracePoint, ...]:
        return tuple(self._points)

    def observe(
        self,
        *,
        iteration: int,
        evaluations: int,
        positions: np.ndarray,
        objective_values: np.ndarray,
        best_objective: float,
        elapsed_seconds: float,
        inertia_weight: float | None,
    ) -> None:
        diversity_metrics = {
            "diversity_hussain",
            "exploration_percent",
            "exploitation_percent",
        }
        diversity = None
        if self._selected.intersection(diversity_metrics):
            diversity = hussain_diversity_v1(positions)
            self._maximum_diversity = max(self._maximum_diversity, diversity)
        if not self._sampling.includes(iteration, self._maximum_iteration):
            return

        candidates: dict[str, object] = {
            "iteration_index": iteration,
            "iteration_time_seconds": elapsed_seconds,
            "objective_best": best_objective,
            "evaluations": evaluations,
            "objective_mean": float(np.mean(objective_values)),
            "objective_std": float(np.std(objective_values)),
        }
        if diversity is not None:
            candidates["diversity_hussain"] = diversity
            exploration, exploitation = exploration_exploitation_v1(
                diversity, self._maximum_diversity
            )
            candidates["exploration_percent"] = exploration
            candidates["exploitation_percent"] = exploitation
        if "population_entropy" in self._selected:
            entropy, _ = population_entropy_v1(
                positions, lower_bounds=self._lower, upper_bounds=self._upper
            )
            candidates["population_entropy"] = entropy
        dimension_metrics = {
            "diversity_dimension_mean",
            "diversity_dimension_min",
            "diversity_dimension_max",
        }
        if self._selected.intersection(dimension_metrics):
            _, div_mean, div_minimum, div_maximum = diversity_per_dimension_v1(
                positions
            )
            candidates.update(
                {
                    "diversity_dimension_mean": div_mean,
                    "diversity_dimension_min": div_minimum,
                    "diversity_dimension_max": div_maximum,
                }
            )
        if inertia_weight is not None:
            candidates["inertia_weight"] = inertia_weight
        metrics = {
            metric_id: value
            for metric_id, value in candidates.items()
            if metric_id in self._selected
        }
        self._points.append(
            OptimizationTracePoint(
                checkpoint_index=len(self._points),
                iteration_index=iteration,
                evaluations=evaluations,
                elapsed_seconds=elapsed_seconds,
                metrics=metrics,
            )
        )


def hussain_diversity_v1(population: np.ndarray) -> float:
    """Exact vectorized equivalent of legacy ``diversidadHussain``."""

    values = _population(population)
    centre = np.mean(values, axis=0)
    return round(float(np.mean(np.abs(values - centre))), 3)


def exploration_exploitation_v1(
    diversity: float, maximum_diversity: float
) -> tuple[float, float]:
    """Legacy XPL/XPT formula with a defined zero-diversity edge case."""

    if maximum_diversity == 0.0:
        return 0.0, 0.0
    exploration = round((diversity / maximum_diversity) * 100.0, 2)
    exploitation = round(
        (abs(diversity - maximum_diversity) / maximum_diversity) * 100.0, 2
    )
    return exploration, exploitation


def population_entropy_v1(
    population: np.ndarray,
    *,
    bins: int = 20,
    lower_bounds: np.ndarray | None = None,
    upper_bounds: np.ndarray | None = None,
) -> tuple[float, np.ndarray]:
    values = _population(population)
    population_size, dimension = values.shape
    effective_bins = max(2, min(bins, int(np.sqrt(max(population_size, 2)))))
    entropy_by_dimension = np.zeros(dimension, dtype=float)
    for index in range(dimension):
        coordinate = values[:, index]
        if lower_bounds is not None and upper_bounds is not None:
            minimum, maximum = lower_bounds[index], upper_bounds[index]
        else:
            minimum, maximum = float(np.min(coordinate)), float(np.max(coordinate))
            if maximum == minimum:
                continue
            epsilon = 1e-12 * max(1.0, abs(maximum - minimum))
            minimum -= epsilon
            maximum += epsilon
        histogram, _ = np.histogram(
            coordinate, bins=effective_bins, range=(minimum, maximum)
        )
        probabilities = histogram.astype(float) / population_size
        probabilities = probabilities[probabilities > 0.0]
        if probabilities.size:
            entropy = -np.sum(probabilities * np.log(probabilities))
            entropy_by_dimension[index] = float(
                entropy / np.log(effective_bins)
            )
    return float(np.mean(entropy_by_dimension)), entropy_by_dimension


def diversity_per_dimension_v1(
    population: np.ndarray,
) -> tuple[np.ndarray, float, float, float]:
    values = _population(population)
    median = np.median(values, axis=0)
    diversity = np.mean(np.abs(values - median), axis=0)
    return (
        diversity,
        float(np.mean(diversity)),
        float(np.min(diversity)),
        float(np.max(diversity)),
    )


def _population(population: np.ndarray) -> np.ndarray:
    values = np.asarray(population, dtype=float)
    if values.ndim != 2 or not values.size:
        raise ValueError("population must be a non-empty two-dimensional array")
    if not np.all(np.isfinite(values)):
        raise ValueError("population must contain only finite values")
    return values
