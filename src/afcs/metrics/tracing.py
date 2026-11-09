"""Versioned population metrics and immutable optimization trace points."""

from __future__ import annotations

import math
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from types import MappingProxyType

import numpy as np

OPTIMIZATION_TRACE_METRICS = frozenset(
    {
        "iteration_index",
        "iteration_time_seconds",
        "objective_best",
        "evaluations",
    }
)

POPULATION_TRACE_METRICS = frozenset(
    {
        "objective_mean",
        "objective_std",
        "diversity_hussain",
        "exploration_percent",
        "exploitation_percent",
        "population_entropy",
        "diversity_dimension_mean",
        "diversity_dimension_min",
        "diversity_dimension_max",
    }
)

PSO_TRACE_METRICS = frozenset(
    {
        "inertia_weight",
    }
)

GA_TRACE_METRICS = frozenset(
    {
        "crossover_probability",
        "mutation_probability",
    }
)

CONTROLLER_TRACE_METRICS = frozenset(
    {
        "progress_ratio",
        "fuzzy_input_diversity",
        "fuzzy_membership_degrees",
        "fuzzy_active_rules",
        "fuzzy_rule_firing_strengths",
        "fuzzy_output_normalized",
        "fuzzy_inference_time_seconds",
        "fuzzy_evaluated_rule_count",
        "fuzzy_skipped_rule_count",
        "fuzzy_boundary_event_count",
        "fuzzy_no_activation_count",
        "fuzzy_fallback_count",
    }
)
ALL_TRACE_METRICS = (
    OPTIMIZATION_TRACE_METRICS
    | POPULATION_TRACE_METRICS
    | PSO_TRACE_METRICS
    | GA_TRACE_METRICS
    | CONTROLLER_TRACE_METRICS
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
        return iteration % self.every_iterations == 0 or iteration == maximum_iteration


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


@dataclass(frozen=True, slots=True)
class OptimizationObservation:
    """Method-neutral state recorded at one completed optimization checkpoint."""

    iteration: int
    evaluations: int
    best_objective: float
    elapsed_seconds: float

    def __post_init__(self) -> None:
        for name, value in (
            ("iteration", self.iteration),
            ("evaluations", self.evaluations),
        ):
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ValueError(f"{name} must be a non-negative integer")
        if not math.isfinite(float(self.best_objective)):
            raise ValueError("best_objective must be finite")
        if not math.isfinite(float(self.elapsed_seconds)) or self.elapsed_seconds < 0:
            raise ValueError("elapsed_seconds must be finite and non-negative")


@dataclass(frozen=True, slots=True)
class PopulationObservation:
    """Population state shared by population-based optimizer metric providers."""

    positions: np.ndarray
    objective_values: np.ndarray


class OptimizationTraceCollector:
    """Collect method-neutral and optional population metrics."""

    def __init__(
        self,
        *,
        selected_metrics: Iterable[str],
        sampling: TraceSampling,
        maximum_iteration: int,
        lower_bounds: Iterable[float] | None = None,
        upper_bounds: Iterable[float] | None = None,
    ) -> None:
        if (lower_bounds is None) != (upper_bounds is None):
            raise ValueError("lower_bounds and upper_bounds must be provided together")
        self._selected = frozenset(selected_metrics).intersection(
            OPTIMIZATION_TRACE_METRICS | POPULATION_TRACE_METRICS
        )
        self._sampling = sampling
        self._maximum_iteration = maximum_iteration
        self._lower = (
            np.asarray(tuple(lower_bounds), dtype=float)
            if lower_bounds is not None
            else None
        )
        self._upper = (
            np.asarray(tuple(upper_bounds), dtype=float)
            if upper_bounds is not None
            else None
        )
        self._maximum_diversity = 0.0
        self._points: list[OptimizationTracePoint] = []

    @property
    def points(self) -> tuple[OptimizationTracePoint, ...]:
        return tuple(self._points)

    def observe(
        self,
        *,
        observation: OptimizationObservation,
        population: PopulationObservation | None = None,
    ) -> None:
        if not isinstance(observation, OptimizationObservation):
            raise TypeError("observation must be OptimizationObservation")
        metrics = {
            "iteration_index": observation.iteration,
            "iteration_time_seconds": observation.elapsed_seconds,
            "objective_best": observation.best_objective,
            "evaluations": observation.evaluations,
        }
        if population is not None:
            metrics.update(self._population_metrics(population))
        self._record(observation, metrics)

    def _population_metrics(
        self, population: PopulationObservation
    ) -> dict[str, object]:
        if not isinstance(population, PopulationObservation):
            raise TypeError("population must be PopulationObservation")
        positions = _population(population.positions)
        objective_values = np.asarray(population.objective_values, dtype=float)
        if (
            objective_values.ndim != 1
            or not objective_values.size
            or objective_values.size != positions.shape[0]
            or not np.all(np.isfinite(objective_values))
        ):
            raise ValueError(
                "objective_values must be a finite vector matching the population"
            )
        metrics: dict[str, object] = {}
        if self._selected.intersection({"objective_mean", "objective_std"}):
            metrics["objective_mean"] = float(np.mean(objective_values))
            metrics["objective_std"] = float(np.std(objective_values))

        diversity_metrics = {
            "diversity_hussain",
            "exploration_percent",
            "exploitation_percent",
        }
        diversity = None
        if self._selected.intersection(diversity_metrics):
            diversity = hussain_diversity_v1(positions)
            self._maximum_diversity = max(self._maximum_diversity, diversity)
        if diversity is not None:
            metrics["diversity_hussain"] = diversity
            exploration, exploitation = exploration_exploitation_v1(
                diversity, self._maximum_diversity
            )
            metrics["exploration_percent"] = exploration
            metrics["exploitation_percent"] = exploitation
        if "population_entropy" in self._selected:
            entropy, _ = population_entropy_v1(
                positions, lower_bounds=self._lower, upper_bounds=self._upper
            )
            metrics["population_entropy"] = entropy
        dimension_metrics = {
            "diversity_dimension_mean",
            "diversity_dimension_min",
            "diversity_dimension_max",
        }
        if self._selected.intersection(dimension_metrics):
            _, div_mean, div_minimum, div_maximum = diversity_per_dimension_v1(
                positions
            )
            metrics.update(
                {
                    "diversity_dimension_mean": div_mean,
                    "diversity_dimension_min": div_minimum,
                    "diversity_dimension_max": div_maximum,
                }
            )
        return metrics

    def _record(
        self,
        observation: OptimizationObservation,
        metrics: Mapping[str, object],
    ) -> None:
        if not self._sampling.includes(observation.iteration, self._maximum_iteration):
            return
        selected = {
            metric_id: value
            for metric_id, value in metrics.items()
            if metric_id in self._selected
        }
        self._points.append(
            OptimizationTracePoint(
                checkpoint_index=len(self._points),
                iteration_index=observation.iteration,
                evaluations=observation.evaluations,
                elapsed_seconds=observation.elapsed_seconds,
                metrics=selected,
            )
        )


class PSOTraceCollector(OptimizationTraceCollector):
    """Add PSO parameter and controller telemetry to general trace metrics."""

    def __init__(
        self,
        *,
        selected_metrics: Iterable[str],
        sampling: TraceSampling,
        maximum_iteration: int,
        lower_bounds: Iterable[float],
        upper_bounds: Iterable[float],
    ) -> None:
        selected = tuple(selected_metrics)
        super().__init__(
            selected_metrics=selected,
            sampling=sampling,
            maximum_iteration=maximum_iteration,
            lower_bounds=lower_bounds,
            upper_bounds=upper_bounds,
        )
        self._selected = frozenset(selected).intersection(ALL_TRACE_METRICS)

    def observe(
        self,
        *,
        observation: OptimizationObservation,
        population: PopulationObservation | None = None,
        inertia_weight: float | None = None,
        policy_diagnostics: Mapping[str, object] | None = None,
    ) -> None:
        if not isinstance(observation, OptimizationObservation):
            raise TypeError("observation must be OptimizationObservation")
        metrics = {
            "iteration_index": observation.iteration,
            "iteration_time_seconds": observation.elapsed_seconds,
            "objective_best": observation.best_objective,
            "evaluations": observation.evaluations,
        }
        if population is not None:
            metrics.update(self._population_metrics(population))
        if inertia_weight is not None:
            metrics.update(self._pso_metrics(inertia_weight))
        metrics.update(self._controller_metrics(policy_diagnostics))
        self._record(observation, metrics)

    @staticmethod
    def _pso_metrics(inertia_weight: float) -> dict[str, object]:
        return {"inertia_weight": inertia_weight}

    @staticmethod
    def _controller_metrics(
        diagnostics: Mapping[str, object] | None,
    ) -> dict[str, object]:
        if not diagnostics:
            return {}
        values = {
            "progress_ratio": diagnostics.get("progress_ratio"),
            "fuzzy_input_diversity": diagnostics.get("diversity_ratio"),
            "fuzzy_membership_degrees": diagnostics.get("membership_degrees"),
            "fuzzy_active_rules": diagnostics.get("active_rules"),
            "fuzzy_rule_firing_strengths": diagnostics.get("rule_firing_strengths"),
            "fuzzy_output_normalized": diagnostics.get("normalized_output"),
            "fuzzy_inference_time_seconds": diagnostics.get("inference_time_seconds"),
            "fuzzy_evaluated_rule_count": diagnostics.get("evaluated_rule_count"),
            "fuzzy_skipped_rule_count": diagnostics.get("skipped_rule_count"),
            "fuzzy_boundary_event_count": diagnostics.get("boundary_event_count"),
            "fuzzy_no_activation_count": diagnostics.get("no_activation_count"),
            "fuzzy_fallback_count": diagnostics.get("fallback_count"),
        }
        return {key: value for key, value in values.items() if value is not None}


def hussain_diversity_v1(population: np.ndarray) -> float:
    """Exact vectorized equivalent of legacy ``diversidadHussain``."""

    return round(hussain_diversity_v2(population), 3)


def hussain_diversity_v2(population: np.ndarray) -> float:
    """Mean absolute distance from the centroid, without internal quantization."""

    values = _population(population)
    centre = np.mean(values, axis=0)
    return float(np.mean(np.abs(values - centre)))


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
            entropy_by_dimension[index] = float(entropy / np.log(effective_bins))
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
