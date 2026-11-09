"""Versioned in-memory PSO cycle with explicit historical or domain-width limits."""

from __future__ import annotations

import math
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from time import perf_counter
from types import MappingProxyType

import numpy as np

from afcs.controllers import ParameterPolicy
from afcs.core import EvaluationBudget, OptimizationDirection, ReplicaRandomStreams
from afcs.core.hashing import INITIAL_STATE_HASH_VERSION, array_sha256
from afcs.metrics import (
    OptimizationObservation,
    OptimizationTracePoint,
    PopulationObservation,
    PSOTraceCollector,
)
from afcs.optimizers import OptimizerMetadata, OptimizerRunMetadata, SearchState
from afcs.optimizers.contracts import unconstrained_objective
from afcs.problems import OptimizationProblem

from .core import PSOConfig, advance_swarm

PSO_IMPLEMENTATION_VERSION = "2.0.0a0-legacy-compatible"
PSO_DOMAIN_WIDTH_VERSION = "2.0.0a1-domain-width"


@dataclass(frozen=True, slots=True)
class LegacyPSORunConfig:
    """Execution settings that preserve the approved historical PSO rules."""

    population_size: int
    max_iterations: int
    cognitive: float = 2.0
    social: float = 2.0
    velocity_factor: float = 0.1
    velocity_rule: str = "legacy_upper0_v1"

    def __post_init__(self) -> None:
        if self.velocity_rule not in {"legacy_upper0_v1", "domain_width_v1"}:
            raise ValueError("Unsupported PSO velocity_rule")
        for name, value in (
            ("population_size", self.population_size),
            ("max_iterations", self.max_iterations),
        ):
            if isinstance(value, bool) or not isinstance(value, int):
                raise TypeError(f"{name} must be an integer")
            if value <= 0:
                raise ValueError(f"{name} must be positive")
        coefficients = PSOConfig(cognitive=self.cognitive, social=self.social)
        object.__setattr__(self, "cognitive", coefficients.cognitive)
        object.__setattr__(self, "social", coefficients.social)
        if isinstance(self.velocity_factor, bool):
            raise TypeError("velocity_factor must be numeric")
        try:
            velocity_factor = float(self.velocity_factor)
        except (TypeError, ValueError) as error:
            raise TypeError("velocity_factor must be numeric") from error
        if not math.isfinite(velocity_factor) or velocity_factor < 0:
            raise ValueError("velocity_factor must be finite and non-negative")
        object.__setattr__(self, "velocity_factor", velocity_factor)

    @property
    def evaluation_budget(self) -> int:
        """Initial population plus one population per PSO iteration."""

        return self.population_size * (self.max_iterations + 1)


@dataclass(frozen=True, slots=True)
class PSORunResult:
    """Final immutable snapshot returned by an in-memory PSO execution."""

    best_position: np.ndarray
    best_objective: float
    positions: np.ndarray
    objective_values: np.ndarray
    iterations: int
    evaluations: int
    inertia_history: tuple[float, ...]
    initial_population_sha256: str
    initial_velocity_sha256: str
    trace_points: tuple[OptimizationTracePoint, ...] = ()
    run_metrics: Mapping[str, object] = field(default_factory=dict)
    initial_state_hash_version: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "run_metrics", MappingProxyType(dict(self.run_metrics))
        )


class LegacyCompatiblePSO:
    """Run single-use PSO with an injected inertia policy and explicit RNG.

    ``rng`` is a shared in-memory stream without replica provenance;
    ``random_streams`` is the auditable campaign protocol. Velocity semantics
    are explicit and determine the implementation version.
    """

    def __init__(
        self,
        *,
        problem: OptimizationProblem,
        config: LegacyPSORunConfig,
        inertia_policy: ParameterPolicy,
        rng: np.random.Generator | None = None,
        random_streams: ReplicaRandomStreams | None = None,
        trace_collector: PSOTraceCollector | None = None,
        clock: Callable[[], float] = perf_counter,
        component_clock: Callable[[], float] = perf_counter,
    ) -> None:
        if not isinstance(problem, OptimizationProblem):
            raise TypeError("problem must implement OptimizationProblem")
        if not isinstance(config, LegacyPSORunConfig):
            raise TypeError("config must be LegacyPSORunConfig")
        if not isinstance(inertia_policy, ParameterPolicy):
            raise TypeError("inertia_policy must implement ParameterPolicy")
        if "w" not in inertia_policy.compatible_parameters:
            raise ValueError("inertia_policy must declare compatibility with 'w'")
        if (rng is None) == (random_streams is None):
            raise ValueError("provide exactly one of rng or random_streams")
        if rng is not None and not isinstance(rng, np.random.Generator):
            raise TypeError("rng must be numpy.random.Generator")
        if random_streams is not None and not isinstance(
            random_streams, ReplicaRandomStreams
        ):
            raise TypeError("random_streams must be ReplicaRandomStreams")
        if trace_collector is not None and not isinstance(
            trace_collector, PSOTraceCollector
        ):
            raise TypeError("trace_collector must be PSOTraceCollector")
        if not callable(clock):
            raise TypeError("clock must be callable")
        if not callable(component_clock):
            raise TypeError("component_clock must be callable")
        self._problem = problem
        self._config = config
        self._inertia_policy = inertia_policy
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
        return OptimizerRunMetadata(
            optimizer=OptimizerMetadata(
                optimizer_id="PSO",
                version=(
                    PSO_IMPLEMENTATION_VERSION
                    if self._config.velocity_rule == "legacy_upper0_v1"
                    else PSO_DOMAIN_WIDTH_VERSION
                ),
                configurable_parameters=(
                    "w",
                    "cognitive",
                    "social",
                    "velocity_factor",
                    *(
                        ("velocity_rule",)
                        if self._config.velocity_rule != "legacy_upper0_v1"
                        else ()
                    ),
                ),
                adaptable_parameters=("w",),
            ),
            problem=self._problem.metadata,
            parameters={
                "cognitive": self._config.cognitive,
                "social": self._config.social,
                "velocity_factor": self._config.velocity_factor,
                **(
                    {"velocity_rule": self._config.velocity_rule}
                    if self._config.velocity_rule != "legacy_upper0_v1"
                    else {}
                ),
                "inertia_policy": {
                    "policy_id": self._inertia_policy.policy_id,
                    "policy_version": self._inertia_policy.policy_version,
                    "configuration": dict(self._inertia_policy.configuration),
                },
            },
            evaluation_budget=self._config.evaluation_budget,
            iteration_budget=self._config.max_iterations,
            population_size=self._config.population_size,
            replica_seed=self._replica_seed,
            rng_engine=self._rng_engine,
        )

    def run(self) -> PSORunResult:
        """Execute one attempt; this instance cannot be run again, even on failure."""

        if self._run_started:
            raise RuntimeError(
                "Optimizer instances are single-use; create a new instance"
            )
        self._run_started = True
        self._problem_time_seconds = 0.0
        self._metric_time_seconds = 0.0
        initialization_started = self._clock()
        space = self._problem.metadata.search_space
        lower = np.asarray(space.lower_bounds, dtype=float)
        upper = np.asarray(space.upper_bounds, dtype=float)
        maximum_velocity = self._config.velocity_factor * (
            upper - lower
            if self._config.velocity_rule == "domain_width_v1"
            else upper[0]
        )
        if not np.all(np.isfinite(maximum_velocity)) or np.any(maximum_velocity < 0):
            label = (
                "legacy Vmax"
                if self._config.velocity_rule == "legacy_upper0_v1"
                else "domain-width Vmax"
            )
            raise ValueError(f"{label} must produce finite non-negative limits")

        budget = EvaluationBudget(self._config.evaluation_budget)
        shape = (self._config.population_size, space.dimension)
        positions = self._initialization_rng.uniform(lower, upper, size=shape)
        velocities = np.zeros(shape, dtype=float)
        initial_population_sha256 = array_sha256(positions)
        initial_velocity_sha256 = array_sha256(velocities)
        objective_values = self._evaluate_population(positions, budget)
        personal_best = positions.copy()
        personal_best_values = objective_values.copy()
        best_index = self._best_index(personal_best_values)
        global_best = personal_best[best_index].copy()
        global_best_value = float(personal_best_values[best_index])
        self._observe(
            observation=OptimizationObservation(
                iteration=0,
                evaluations=budget.consumed,
                best_objective=global_best_value,
                elapsed_seconds=self._clock() - initialization_started,
            ),
            population=PopulationObservation(positions, objective_values),
            inertia_weight=None,
        )

        inertia_history: list[float] = []
        current_parameters: dict[str, float] = {}
        movement_config = PSOConfig(
            cognitive=self._config.cognitive,
            social=self._config.social,
        )

        for iteration in range(1, self._config.max_iterations + 1):
            iteration_started = self._clock()
            state = SearchState(
                iteration=iteration,
                evaluations=budget.consumed,
                evaluation_budget=budget.maximum,
                best_objective=global_best_value,
                observations={"positions": _readonly_copy(positions)},
            )
            update = self._inertia_policy.propose(state, current_parameters)
            if update.policy_id != self._inertia_policy.policy_id:
                raise ValueError("parameter update policy_id does not match its policy")
            if update.policy_version != self._inertia_policy.policy_version:
                raise ValueError(
                    "parameter update policy_version does not match its policy"
                )
            if "w" not in update.values:
                raise ValueError("inertia_policy must propose parameter 'w'")
            inertia = float(update.values["w"])
            current_parameters["w"] = inertia
            inertia_history.append(inertia)

            step = advance_swarm(
                positions=positions,
                velocities=velocities,
                personal_best=personal_best,
                global_best=global_best,
                inertia=inertia,
                cognitive_random=self._dynamics_rng.random(shape),
                social_random=self._dynamics_rng.random(shape),
                maximum_velocity=maximum_velocity,
                config=movement_config,
            )
            positions = np.clip(step.positions, lower, upper)
            velocities = step.velocities
            objective_values = self._evaluate_population(positions, budget)

            improved = self._improvement_mask(objective_values, personal_best_values)
            personal_best[improved] = positions[improved]
            personal_best_values[improved] = objective_values[improved]
            candidate_index = self._best_index(personal_best_values)
            candidate_value = float(personal_best_values[candidate_index])
            if self._problem.metadata.direction.is_better(
                candidate_value, global_best_value
            ):
                global_best = personal_best[candidate_index].copy()
                global_best_value = candidate_value
            self._observe(
                observation=OptimizationObservation(
                    iteration=iteration,
                    evaluations=budget.consumed,
                    best_objective=global_best_value,
                    elapsed_seconds=self._clock() - iteration_started,
                ),
                population=PopulationObservation(positions, objective_values),
                inertia_weight=inertia,
                policy_diagnostics=getattr(
                    self._inertia_policy, "last_diagnostics", None
                ),
            )

        if not budget.exhausted:
            raise RuntimeError("PSO terminated before consuming its declared budget")
        return PSORunResult(
            best_position=_readonly_copy(global_best),
            best_objective=global_best_value,
            positions=_readonly_copy(positions),
            objective_values=_readonly_copy(objective_values),
            iterations=self._config.max_iterations,
            evaluations=budget.consumed,
            inertia_history=tuple(inertia_history),
            initial_population_sha256=initial_population_sha256,
            initial_velocity_sha256=initial_velocity_sha256,
            initial_state_hash_version=INITIAL_STATE_HASH_VERSION,
            trace_points=(
                self._trace_collector.points
                if self._trace_collector is not None
                else ()
            ),
            run_metrics={
                **getattr(self._inertia_policy, "summary_metrics", {}),
                "objective_best": global_best_value,
                "problem_evaluation_total_seconds": self._problem_time_seconds,
                "metric_collection_total_seconds": self._metric_time_seconds,
            },
        )

    def _observe(
        self,
        *,
        observation: OptimizationObservation,
        population: PopulationObservation,
        inertia_weight: float | None,
        policy_diagnostics: Mapping[str, object] | None = None,
    ) -> None:
        if self._trace_collector is not None:
            started = self._read_component_clock()
            self._trace_collector.observe(
                observation=observation,
                population=population,
                inertia_weight=inertia_weight,
                policy_diagnostics=policy_diagnostics,
            )
            self._metric_time_seconds += self._component_elapsed(started)

    def _evaluate_population(
        self, positions: np.ndarray, budget: EvaluationBudget
    ) -> np.ndarray:
        values = np.empty(positions.shape[0], dtype=float)
        for index, position in enumerate(positions):
            budget.consume()
            started = self._read_component_clock()
            values[index] = unconstrained_objective(self._problem.evaluate(position))
            self._problem_time_seconds += self._component_elapsed(started)
        return values

    def _read_component_clock(self) -> float:
        value = float(self._component_clock())
        if not math.isfinite(value):
            raise ValueError("component_clock must produce finite values")
        return value

    def _component_elapsed(self, started: float) -> float:
        elapsed = self._read_component_clock() - started
        if elapsed < 0.0:
            raise ValueError("component_clock must be monotonic")
        return elapsed

    def _best_index(self, values: np.ndarray) -> int:
        if self._problem.metadata.direction is OptimizationDirection.MINIMIZE:
            return int(np.argmin(values))
        return int(np.argmax(values))

    def _improvement_mask(
        self, candidates: np.ndarray, incumbents: np.ndarray
    ) -> np.ndarray:
        if self._problem.metadata.direction is OptimizationDirection.MINIMIZE:
            return candidates < incumbents
        return candidates > incumbents


def _readonly_copy(values: np.ndarray) -> np.ndarray:
    snapshot = np.array(values, dtype=float, copy=True)
    snapshot.setflags(write=False)
    return snapshot
