"""In-memory, legacy-compatible Particle Swarm Optimization cycle."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import math
from time import perf_counter
from collections.abc import Callable

import numpy as np

from afcs.controllers import ParameterPolicy
from afcs.core import EvaluationBudget, OptimizationDirection, ReplicaRandomStreams
from afcs.optimizers import OptimizerMetadata, OptimizerRunMetadata, SearchState
from afcs.metrics import OptimizationTracePoint, PSOTraceCollector
from afcs.problems import OptimizationProblem

from .core import PSOConfig, advance_swarm


@dataclass(frozen=True, slots=True)
class LegacyPSORunConfig:
    """Execution settings that preserve the approved historical PSO rules."""

    population_size: int
    max_iterations: int
    cognitive: float = 2.0
    social: float = 2.0
    velocity_factor: float = 0.1

    def __post_init__(self) -> None:
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


class LegacyCompatiblePSO:
    """Run PSO without persistence, controllers, or seed derivation.

    The caller owns and injects the NumPy generator. This is dependency
    injection only: it intentionally does not define the campaign seed
    protocol or derive per-replica random streams.
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
        self._problem = problem
        self._config = config
        self._inertia_policy = inertia_policy
        self._trace_collector = trace_collector
        self._clock = clock
        if random_streams is None:
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
                version="2.0.0a0-legacy-compatible",
                configurable_parameters=(
                    "w",
                    "cognitive",
                    "social",
                    "velocity_factor",
                ),
                adaptable_parameters=("w",),
            ),
            problem=self._problem.metadata,
            parameters={
                "cognitive": self._config.cognitive,
                "social": self._config.social,
                "velocity_factor": self._config.velocity_factor,
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
        initialization_started = self._clock()
        space = self._problem.metadata.search_space
        lower = np.asarray(space.lower_bounds, dtype=float)
        upper = np.asarray(space.upper_bounds, dtype=float)
        maximum_velocity = self._config.velocity_factor * upper[0]
        if maximum_velocity < 0:
            raise ValueError(
                "legacy Vmax requires the first upper bound to be non-negative"
            )

        budget = EvaluationBudget(self._config.evaluation_budget)
        shape = (self._config.population_size, space.dimension)
        positions = self._initialization_rng.uniform(lower, upper, size=shape)
        velocities = np.zeros(shape, dtype=float)
        initial_population_sha256 = _array_sha256(positions)
        initial_velocity_sha256 = _array_sha256(velocities)
        objective_values = self._evaluate_population(positions, budget)
        personal_best = positions.copy()
        personal_best_values = objective_values.copy()
        best_index = self._best_index(personal_best_values)
        global_best = personal_best[best_index].copy()
        global_best_value = float(personal_best_values[best_index])
        self._observe(
            iteration=0,
            evaluations=budget.consumed,
            positions=positions,
            objective_values=objective_values,
            best_objective=global_best_value,
            elapsed_seconds=self._clock() - initialization_started,
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

            improved = self._improvement_mask(
                objective_values, personal_best_values
            )
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
                iteration=iteration,
                evaluations=budget.consumed,
                positions=positions,
                objective_values=objective_values,
                best_objective=global_best_value,
                elapsed_seconds=self._clock() - iteration_started,
                inertia_weight=inertia,
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
            trace_points=(
                self._trace_collector.points
                if self._trace_collector is not None
                else ()
            ),
        )

    def _observe(self, **observation) -> None:
        if self._trace_collector is not None:
            self._trace_collector.observe(**observation)

    def _evaluate_population(
        self, positions: np.ndarray, budget: EvaluationBudget
    ) -> np.ndarray:
        values = np.empty(positions.shape[0], dtype=float)
        for index, position in enumerate(positions):
            budget.consume()
            values[index] = self._problem.evaluate(position).objective
        return values

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


def _array_sha256(values: np.ndarray) -> str:
    canonical = np.ascontiguousarray(values, dtype="<f8")
    payload = (
        str(canonical.shape).encode("ascii")
        + canonical.dtype.str.encode("ascii")
        + canonical.tobytes()
    )
    return hashlib.sha256(payload).hexdigest()
