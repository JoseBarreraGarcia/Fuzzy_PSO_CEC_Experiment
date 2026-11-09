"""Bounded real-coded genetic algorithm with explicit evaluation accounting."""

from __future__ import annotations

import math
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from time import perf_counter
from types import MappingProxyType
from typing import SupportsFloat, SupportsIndex

import numpy as np

from afcs.controllers import NoAdaptation, ParameterPolicy
from afcs.core import (
    EvaluationBudget,
    OptimizationDirection,
    ReplicaRandomStreams,
)
from afcs.core.hashing import INITIAL_STATE_HASH_VERSION, array_sha256
from afcs.metrics import (
    GA_TRACE_METRICS,
    OptimizationObservation,
    OptimizationTraceCollector,
    OptimizationTracePoint,
    PopulationObservation,
    TraceSampling,
)
from afcs.optimizers import OptimizerMetadata, OptimizerRunMetadata, SearchState
from afcs.optimizers.contracts import unconstrained_objective
from afcs.problems import OptimizationProblem

GA_IMPLEMENTATION_VERSION = "2.0.0a0-real-coded"
_ADAPTABLE_PARAMETERS = frozenset({"crossover_probability", "mutation_probability"})


@dataclass(frozen=True, slots=True)
class RealCodedGARunConfig:
    """Fixed generation and operator settings for bounded continuous search."""

    population_size: int
    max_iterations: int
    crossover_probability: float = 0.9
    crossover_distribution_index: float = 20.0
    mutation_probability: float | None = None
    mutation_distribution_index: float = 20.0
    tournament_size: int = 2

    def __post_init__(self) -> None:
        for name, value, minimum in (
            ("population_size", self.population_size, 2),
            ("max_iterations", self.max_iterations, 1),
            ("tournament_size", self.tournament_size, 2),
        ):
            if isinstance(value, bool) or not isinstance(value, int):
                raise TypeError(f"{name} must be an integer")
            if value < minimum:
                raise ValueError(f"{name} must be at least {minimum}")
        for name in ("crossover_probability", "mutation_probability"):
            value = getattr(self, name)
            if value is None and name == "mutation_probability":
                continue
            normalized = _probability(value, name)
            object.__setattr__(self, name, normalized)
        for name in (
            "crossover_distribution_index",
            "mutation_distribution_index",
        ):
            normalized = _finite_positive(getattr(self, name), name)
            object.__setattr__(self, name, normalized)

    @property
    def evaluation_budget(self) -> int:
        """Initial population plus one complete evaluated generation per step."""

        return self.population_size * (self.max_iterations + 1)

    def effective_mutation_probability(self, dimension: int) -> float:
        if self.mutation_probability is not None:
            return self.mutation_probability
        if (
            isinstance(dimension, bool)
            or not isinstance(dimension, int)
            or dimension <= 0
        ):
            raise ValueError("dimension must be a positive integer")
        return 1.0 / dimension


@dataclass(frozen=True, slots=True)
class GARunResult:
    """Immutable final snapshot from one real-coded GA execution."""

    best_position: np.ndarray
    best_objective: float
    positions: np.ndarray
    objective_values: np.ndarray
    iterations: int
    evaluations: int
    initial_population_sha256: str
    trace_points: tuple[OptimizationTracePoint, ...] = ()
    run_metrics: Mapping[str, object] = field(default_factory=dict)
    initial_state_hash_version: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "run_metrics", MappingProxyType(dict(self.run_metrics))
        )


class RealCodedGA:
    """Run a bounded real-coded GA using SBX, polynomial mutation and elitism.

    The default ``NoAdaptation`` policy keeps parameters fixed. The policy
    boundary supports future adaptation of crossover and mutation probabilities
    without making those controls part of the algorithm's current default.
    """

    def __init__(
        self,
        *,
        problem: OptimizationProblem,
        config: RealCodedGARunConfig,
        parameter_policy: ParameterPolicy | None = None,
        rng: np.random.Generator | None = None,
        random_streams: ReplicaRandomStreams | None = None,
        trace_collector: "GATraceCollector | None" = None,
        clock: Callable[[], float] = perf_counter,
        component_clock: Callable[[], float] = perf_counter,
    ) -> None:
        if not isinstance(problem, OptimizationProblem):
            raise TypeError("problem must implement OptimizationProblem")
        if not isinstance(config, RealCodedGARunConfig):
            raise TypeError("config must be RealCodedGARunConfig")
        if (rng is None) == (random_streams is None):
            raise ValueError("provide exactly one of rng or random_streams")
        if rng is not None and not isinstance(rng, np.random.Generator):
            raise TypeError("rng must be numpy.random.Generator")
        if random_streams is not None and not isinstance(
            random_streams, ReplicaRandomStreams
        ):
            raise TypeError("random_streams must be ReplicaRandomStreams")
        if parameter_policy is None:
            parameter_policy = NoAdaptation()
        if not isinstance(parameter_policy, ParameterPolicy):
            raise TypeError("parameter_policy must implement ParameterPolicy")
        incompatible = (
            set(parameter_policy.compatible_parameters) - _ADAPTABLE_PARAMETERS
        )
        if incompatible:
            raise ValueError(
                "parameter_policy declares parameters unsupported by GA: "
                f"{sorted(incompatible)}"
            )
        if trace_collector is not None and not isinstance(
            trace_collector, GATraceCollector
        ):
            raise TypeError("trace_collector must be GATraceCollector")
        if not callable(clock) or not callable(component_clock):
            raise TypeError("clocks must be callable")

        self._problem = problem
        self._config = config
        self._parameter_policy = parameter_policy
        self._trace_collector = trace_collector
        self._clock = clock
        self._component_clock = component_clock
        self._problem_time_seconds = 0.0
        self._metric_time_seconds = 0.0
        self._run_started = False
        if random_streams is None:
            if rng is None:
                raise ValueError("rng is required without random_streams")
            self._initialization_rng = rng
            self._dynamics_rng = rng
            self._replica_seed = None
            self._rng_engine = None
        else:
            self._initialization_rng = random_streams.generator("initialization")
            self._dynamics_rng = random_streams.generator("dynamics")
            self._replica_seed = random_streams.replica_seed
            self._rng_engine = random_streams.engine

    @property
    def run_metadata(self) -> OptimizerRunMetadata:
        mutation_probability: float | str = (
            self._config.mutation_probability
            if self._config.mutation_probability is not None
            else "1/d"
        )
        return OptimizerRunMetadata(
            optimizer=OptimizerMetadata(
                optimizer_id="GA",
                version=GA_IMPLEMENTATION_VERSION,
                configurable_parameters=(
                    "crossover_probability",
                    "crossover_distribution_index",
                    "mutation_probability",
                    "mutation_distribution_index",
                    "tournament_size",
                ),
                adaptable_parameters=tuple(sorted(_ADAPTABLE_PARAMETERS)),
            ),
            problem=self._problem.metadata,
            parameters={
                "crossover": "simulated_binary_bounded_v1",
                "crossover_probability": self._config.crossover_probability,
                "crossover_distribution_index": self._config.crossover_distribution_index,
                "elitism_count": 1,
                "mutation": "polynomial_bounded_v1",
                "mutation_probability": mutation_probability,
                "mutation_distribution_index": self._config.mutation_distribution_index,
                "parameter_policy": {
                    "policy_id": self._parameter_policy.policy_id,
                    "policy_version": self._parameter_policy.policy_version,
                    "configuration": dict(self._parameter_policy.configuration),
                },
                "selection": "tournament",
                "tournament_size": self._config.tournament_size,
            },
            evaluation_budget=self._config.evaluation_budget,
            iteration_budget=self._config.max_iterations,
            population_size=self._config.population_size,
            replica_seed=self._replica_seed,
            rng_engine=self._rng_engine,
        )

    def run(self) -> GARunResult:
        """Execute one attempt; this instance cannot be run again, even on failure."""

        if self._run_started:
            raise RuntimeError(
                "Optimizer instances are single-use; create a new instance"
            )
        self._run_started = True
        self._problem_time_seconds = 0.0
        self._metric_time_seconds = 0.0
        started = self._clock()
        space = self._problem.metadata.search_space
        lower = np.asarray(space.lower_bounds, dtype=float)
        upper = np.asarray(space.upper_bounds, dtype=float)
        shape = (self._config.population_size, space.dimension)
        budget = EvaluationBudget(self._config.evaluation_budget)

        population = self._initialization_rng.uniform(lower, upper, size=shape)
        initial_population_sha256 = array_sha256(population)
        objective_values = self._evaluate_population(population, budget)
        best_index = self._best_index(objective_values)
        best_position = population[best_index].copy()
        best_objective = float(objective_values[best_index])
        self._observe(
            iteration=0,
            evaluations=budget.consumed,
            population=population,
            objective_values=objective_values,
            best_objective=best_objective,
            elapsed_seconds=self._clock() - started,
            parameters=None,
        )

        current_parameters = {
            "crossover_probability": self._config.crossover_probability,
            "mutation_probability": self._config.effective_mutation_probability(
                space.dimension
            ),
        }
        for iteration in range(1, self._config.max_iterations + 1):
            iteration_started = self._clock()
            state = SearchState(
                iteration=iteration,
                evaluations=budget.consumed,
                evaluation_budget=budget.maximum,
                best_objective=best_objective,
                elapsed_seconds=max(0.0, iteration_started - started),
                observations={"positions": _readonly_copy(population)},
            )
            update = self._parameter_policy.propose(state, current_parameters)
            if update.policy_id != self._parameter_policy.policy_id:
                raise ValueError("parameter update policy_id does not match its policy")
            if update.policy_version != self._parameter_policy.policy_version:
                raise ValueError(
                    "parameter update policy_version does not match its policy"
                )
            unknown = set(update.values) - _ADAPTABLE_PARAMETERS
            if unknown:
                raise ValueError(
                    f"parameter policy proposed unsupported GA parameters: {sorted(unknown)}"
                )
            undeclared = set(update.values) - set(
                self._parameter_policy.compatible_parameters
            )
            if undeclared:
                raise ValueError(
                    "parameter policy proposed undeclared GA parameters: "
                    f"{sorted(undeclared)}"
                )
            current_parameters.update(
                {
                    name: _probability(value, name)
                    for name, value in update.values.items()
                }
            )
            offspring = self._make_offspring(
                population=population,
                objective_values=objective_values,
                lower=lower,
                upper=upper,
                crossover_probability=current_parameters["crossover_probability"],
                mutation_probability=current_parameters["mutation_probability"],
            )
            offspring_values = self._evaluate_population(offspring, budget)

            offspring_best = self._best_index(offspring_values)
            candidate_objective = float(offspring_values[offspring_best])
            if self._problem.metadata.direction.is_better(
                candidate_objective, best_objective
            ):
                best_position = offspring[offspring_best].copy()
                best_objective = candidate_objective

            worst_index = self._worst_index(offspring_values)
            offspring[worst_index] = best_position
            offspring_values[worst_index] = best_objective
            population, objective_values = offspring, offspring_values
            self._observe(
                iteration=iteration,
                evaluations=budget.consumed,
                population=population,
                objective_values=objective_values,
                best_objective=best_objective,
                elapsed_seconds=self._clock() - iteration_started,
                parameters=current_parameters,
            )

        if not budget.exhausted:
            raise RuntimeError("GA terminated before consuming its declared budget")
        summary_metrics = {
            "objective_best": best_objective,
            "problem_evaluation_total_seconds": self._problem_time_seconds,
            "metric_collection_total_seconds": self._metric_time_seconds,
        }
        summary_metrics.update(getattr(self._parameter_policy, "summary_metrics", {}))
        return GARunResult(
            best_position=_readonly_copy(best_position),
            best_objective=best_objective,
            positions=_readonly_copy(population),
            objective_values=_readonly_copy(objective_values),
            iterations=self._config.max_iterations,
            evaluations=budget.consumed,
            initial_population_sha256=initial_population_sha256,
            initial_state_hash_version=INITIAL_STATE_HASH_VERSION,
            trace_points=(
                self._trace_collector.points
                if self._trace_collector is not None
                else ()
            ),
            run_metrics=summary_metrics,
        )

    def _make_offspring(
        self,
        *,
        population: np.ndarray,
        objective_values: np.ndarray,
        lower: np.ndarray,
        upper: np.ndarray,
        crossover_probability: float,
        mutation_probability: float,
    ) -> np.ndarray:
        offspring = np.empty_like(population)
        index = 0
        while index < len(population):
            parent_a = self._select_parent(population, objective_values)
            parent_b = self._select_parent(population, objective_values)
            child_a, child_b = parent_a.copy(), parent_b.copy()
            if self._dynamics_rng.random() < crossover_probability:
                child_a, child_b = _simulated_binary_crossover(
                    parent_a,
                    parent_b,
                    lower,
                    upper,
                    self._config.crossover_distribution_index,
                    self._dynamics_rng,
                )
            child_a = _polynomial_mutation(
                child_a,
                lower,
                upper,
                mutation_probability,
                self._config.mutation_distribution_index,
                self._dynamics_rng,
            )
            child_b = _polynomial_mutation(
                child_b,
                lower,
                upper,
                mutation_probability,
                self._config.mutation_distribution_index,
                self._dynamics_rng,
            )
            offspring[index] = child_a
            if index + 1 < len(population):
                offspring[index + 1] = child_b
            index += 2
        return offspring

    def _select_parent(
        self, population: np.ndarray, objective_values: np.ndarray
    ) -> np.ndarray:
        candidates = self._dynamics_rng.integers(
            0, len(population), size=self._config.tournament_size
        )
        best = int(candidates[0])
        for raw_index in candidates[1:]:
            candidate = int(raw_index)
            candidate_value = float(objective_values[candidate])
            best_value = float(objective_values[best])
            if self._problem.metadata.direction.is_better(
                candidate_value, best_value
            ) or (
                candidate_value == best_value and self._dynamics_rng.integers(0, 2) == 1
            ):
                best = candidate
        return population[best]

    def _best_index(self, values: np.ndarray) -> int:
        if self._problem.metadata.direction is OptimizationDirection.MINIMIZE:
            return int(np.argmin(values))
        return int(np.argmax(values))

    def _worst_index(self, values: np.ndarray) -> int:
        if self._problem.metadata.direction is OptimizationDirection.MINIMIZE:
            return int(np.argmax(values))
        return int(np.argmin(values))

    def _evaluate_population(
        self, population: np.ndarray, budget: EvaluationBudget
    ) -> np.ndarray:
        values = np.empty(len(population), dtype=float)
        for index, candidate in enumerate(population):
            budget.consume()
            started = self._read_component_clock()
            values[index] = unconstrained_objective(self._problem.evaluate(candidate))
            self._problem_time_seconds += self._component_elapsed(started)
        return values

    def _observe(
        self,
        *,
        iteration: int,
        evaluations: int,
        population: np.ndarray,
        objective_values: np.ndarray,
        best_objective: float,
        elapsed_seconds: float,
        parameters: Mapping[str, float] | None,
    ) -> None:
        if self._trace_collector is None:
            return
        started = self._read_component_clock()
        self._trace_collector.observe(
            observation=OptimizationObservation(
                iteration=iteration,
                evaluations=evaluations,
                best_objective=best_objective,
                elapsed_seconds=elapsed_seconds,
            ),
            population=PopulationObservation(population, objective_values),
            parameters=parameters,
        )
        self._metric_time_seconds += self._component_elapsed(started)

    def _read_component_clock(self) -> float:
        value = float(self._component_clock())
        if not math.isfinite(value):
            raise ValueError("component_clock must produce finite values")
        return value

    def _component_elapsed(self, started: float) -> float:
        elapsed = self._read_component_clock() - started
        if elapsed < 0:
            raise ValueError("component_clock must be monotonic")
        return elapsed


class GATraceCollector(OptimizationTraceCollector):
    """Add the real-coded GA's effective operator probabilities to common traces."""

    def __init__(
        self,
        *,
        selected_metrics: tuple[str, ...],
        sampling: TraceSampling,
        maximum_iteration: int,
        lower_bounds: tuple[float, ...],
        upper_bounds: tuple[float, ...],
    ) -> None:
        selected = tuple(selected_metrics)
        super().__init__(
            selected_metrics=selected,
            sampling=sampling,
            maximum_iteration=maximum_iteration,
            lower_bounds=lower_bounds,
            upper_bounds=upper_bounds,
        )
        self._selected = frozenset(selected).intersection(
            self._selected | GA_TRACE_METRICS
        )

    def observe(
        self,
        *,
        observation: OptimizationObservation,
        population: PopulationObservation | None = None,
        parameters: Mapping[str, float] | None = None,
    ) -> None:
        metrics = {
            "iteration_index": observation.iteration,
            "iteration_time_seconds": observation.elapsed_seconds,
            "objective_best": observation.best_objective,
            "evaluations": observation.evaluations,
        }
        if population is not None:
            metrics.update(self._population_metrics(population))
        if parameters is not None:
            metrics.update(
                {
                    "crossover_probability": parameters["crossover_probability"],
                    "mutation_probability": parameters["mutation_probability"],
                }
            )
        self._record(observation, metrics)


def _simulated_binary_crossover(
    parent_a: np.ndarray,
    parent_b: np.ndarray,
    lower: np.ndarray,
    upper: np.ndarray,
    distribution_index: float,
    rng: np.random.Generator,
) -> tuple[np.ndarray, np.ndarray]:
    child_a = parent_a.copy()
    child_b = parent_b.copy()
    for index in range(parent_a.size):
        if rng.random() > 0.5 or math.isclose(
            float(parent_a[index]), float(parent_b[index]), rel_tol=0.0, abs_tol=1e-14
        ):
            continue
        y1 = min(float(parent_a[index]), float(parent_b[index]))
        y2 = max(float(parent_a[index]), float(parent_b[index]))
        low, high = float(lower[index]), float(upper[index])
        random_value = float(rng.random())
        beta = 1.0 + 2.0 * (y1 - low) / (y2 - y1)
        alpha = 2.0 - beta ** (-(distribution_index + 1.0))
        if random_value <= 1.0 / alpha:
            beta_q = (random_value * alpha) ** (1.0 / (distribution_index + 1.0))
        else:
            beta_q = (1.0 / (2.0 - random_value * alpha)) ** (
                1.0 / (distribution_index + 1.0)
            )
        c1 = 0.5 * ((y1 + y2) - beta_q * (y2 - y1))

        beta = 1.0 + 2.0 * (high - y2) / (y2 - y1)
        alpha = 2.0 - beta ** (-(distribution_index + 1.0))
        if random_value <= 1.0 / alpha:
            beta_q = (random_value * alpha) ** (1.0 / (distribution_index + 1.0))
        else:
            beta_q = (1.0 / (2.0 - random_value * alpha)) ** (
                1.0 / (distribution_index + 1.0)
            )
        c2 = 0.5 * ((y1 + y2) + beta_q * (y2 - y1))
        c1 = min(max(c1, low), high)
        c2 = min(max(c2, low), high)
        if rng.integers(0, 2):
            c1, c2 = c2, c1
        child_a[index], child_b[index] = c1, c2
    return child_a, child_b


def _polynomial_mutation(
    individual: np.ndarray,
    lower: np.ndarray,
    upper: np.ndarray,
    probability: float,
    distribution_index: float,
    rng: np.random.Generator,
) -> np.ndarray:
    mutated = individual.copy()
    power = 1.0 / (distribution_index + 1.0)
    for index in range(mutated.size):
        if rng.random() >= probability:
            continue
        low, high = float(lower[index]), float(upper[index])
        span = high - low
        delta1 = (float(mutated[index]) - low) / span
        delta2 = (high - float(mutated[index])) / span
        random_value = float(rng.random())
        if random_value <= 0.5:
            value = 1.0 - delta1
            delta_q = (
                2.0 * random_value
                + (1.0 - 2.0 * random_value) * value ** (distribution_index + 1.0)
            ) ** power - 1.0
        else:
            value = 1.0 - delta2
            delta_q = (
                1.0
                - (
                    2.0 * (1.0 - random_value)
                    + 2.0 * (random_value - 0.5) * value ** (distribution_index + 1.0)
                )
                ** power
            )
        mutated[index] = min(max(float(mutated[index]) + delta_q * span, low), high)
    return mutated


def _readonly_copy(values: np.ndarray) -> np.ndarray:
    copied = np.array(values, copy=True)
    copied.setflags(write=False)
    return copied


def _probability(
    value: SupportsFloat | SupportsIndex | str | bytes | bytearray | memoryview | None,
    name: str,
) -> float:
    if value is None or isinstance(value, bool):
        raise TypeError(f"{name} must be numeric")
    try:
        normalized = float(value)
    except (TypeError, ValueError) as error:
        raise TypeError(f"{name} must be numeric") from error
    if not math.isfinite(normalized) or not 0.0 <= normalized <= 1.0:
        raise ValueError(f"{name} must be finite and between 0 and 1")
    return normalized


def _finite_positive(
    value: SupportsFloat | SupportsIndex | str | bytes | bytearray | memoryview,
    name: str,
) -> float:
    if isinstance(value, bool):
        raise TypeError(f"{name} must be numeric")
    try:
        normalized = float(value)
    except (TypeError, ValueError) as error:
        raise TypeError(f"{name} must be numeric") from error
    if not math.isfinite(normalized) or normalized <= 0.0:
        raise ValueError(f"{name} must be finite and positive")
    return normalized
