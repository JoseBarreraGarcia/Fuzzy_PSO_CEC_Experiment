"""Failure-safe execution of one planned experiment replica."""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
import math
from time import perf_counter

from afcs.experiments.contracts import RunnableOptimizer
from afcs.persistence import ExperimentRepository, PlannedRun, canonical_json


class RunBindingError(ValueError):
    """Raised when an executable object differs from its persisted plan."""


class ExperimentRunExecutor:
    """Bridge a configured optimizer to the repository run lifecycle.

    Seed assignment and optimizer construction deliberately remain outside this
    class. The executor starts one already-planned run, persists its final
    result, and records a structured failure before re-raising an exception.
    """

    def __init__(
        self,
        repository: ExperimentRepository,
        clock: Callable[[], float] = perf_counter,
    ) -> None:
        if not isinstance(repository, ExperimentRepository):
            raise TypeError("repository must be ExperimentRepository")
        if not callable(clock):
            raise TypeError("clock must be callable")
        self._repository = repository
        self._clock = clock

    def execute(self, run_id: int, optimizer: RunnableOptimizer):
        """Execute and persist one replica, returning its optimizer result."""

        if isinstance(run_id, bool) or not isinstance(run_id, int):
            raise TypeError("run_id must be an integer")
        if not isinstance(optimizer, RunnableOptimizer):
            raise TypeError("optimizer must implement RunnableOptimizer")

        plan = self._repository.get_planned_run(run_id)
        self._validate_binding(plan, optimizer)
        self._repository.start_run(run_id)
        try:
            started = self._read_clock()
            result = optimizer.run()
            objective = _finite_float(result.best_objective, "best_objective")
            evaluations = _non_negative_integer(result.evaluations, "evaluations")
            solution = _finite_solution(result.best_position)
            finished = self._read_clock()
            runtime = finished - started
            if runtime < 0:
                raise ValueError("clock must be monotonic")
            selected_metric_ids = self._repository.selected_metric_ids_for_run(run_id)
            selected_run_metrics = {
                metric_id: value
                for metric_id, value in getattr(result, "run_metrics", {}).items()
                if metric_id in selected_metric_ids
            }
            with self._repository.transaction():
                for point in getattr(result, "trace_points", ()):
                    self._repository.record_trace(
                        run_id=run_id,
                        checkpoint_index=point.checkpoint_index,
                        iteration_index=point.iteration_index,
                        evaluations=point.evaluations,
                        elapsed_seconds=point.elapsed_seconds,
                        metrics=point.metrics,
                    )
                self._repository.complete_run(
                    run_id=run_id,
                    objective_best=objective,
                    solution=solution,
                    evaluations=evaluations,
                    runtime_total_seconds=runtime,
                    metrics=selected_run_metrics,
                    initial_population_sha256=getattr(
                        result, "initial_population_sha256", None
                    ),
                    initial_velocity_sha256=getattr(
                        result, "initial_velocity_sha256", None
                    ),
                )
            return result
        except Exception as error:
            self._repository.fail_run(
                run_id,
                error_type=type(error).__name__,
                error_message=str(error),
            )
            raise

    def _read_clock(self) -> float:
        return _finite_float(self._clock(), "clock value")

    @staticmethod
    def _validate_binding(plan: PlannedRun, optimizer: RunnableOptimizer) -> None:
        actual = optimizer.run_metadata
        problem = actual.problem
        actual_problem_parameters = dict(problem.parameters)
        actual_data_sha256 = actual_problem_parameters.pop("data_sha256", None)
        mismatches: list[str] = []

        exact_checks = (
            ("algorithm", plan.algorithm, actual.optimizer.optimizer_id),
            ("optimizer version", plan.optimizer_version, actual.optimizer.version),
            ("problem family", plan.problem_family, problem.family),
            ("problem name", plan.problem_name, problem.problem_id),
            ("dimension", plan.dimension, problem.dimension),
            ("direction", plan.direction, problem.direction.value),
            ("known optimum", plan.optimum, problem.known_optimum),
            (
                "algorithm parameters",
                canonical_json(dict(plan.algorithm_parameters)),
                canonical_json(dict(actual.parameters)),
            ),
            (
                "problem parameters",
                canonical_json(dict(plan.problem_parameters)),
                canonical_json(actual_problem_parameters),
            ),
            ("problem data hash", plan.data_sha256, actual_data_sha256),
            ("population size", plan.population_size, actual.population_size),
            ("replica seed", plan.random_seed, actual.replica_seed),
            ("RNG engine", plan.rng_engine, actual.rng_engine),
        )
        budget_checks = (
            (
                "evaluation budget",
                plan.budget_evaluations,
                actual.evaluation_budget,
            ),
            ("iteration budget", plan.budget_iterations, actual.iteration_budget),
        )
        for label, planned, observed in exact_checks:
            if planned != observed:
                mismatches.append(
                    f"{label}: planned={planned!r}, executable={observed!r}"
                )
        for label, planned, observed in budget_checks:
            if planned is not None and planned != observed:
                mismatches.append(
                    f"{label}: planned={planned!r}, executable={observed!r}"
                )
        if mismatches:
            raise RunBindingError(
                "Run does not match its persisted plan: " + "; ".join(mismatches)
            )


def _finite_float(value: float, label: str) -> float:
    if isinstance(value, bool):
        raise TypeError(f"{label} must be numeric")
    try:
        normalized = float(value)
    except (TypeError, ValueError) as error:
        raise TypeError(f"{label} must be numeric") from error
    if not math.isfinite(normalized):
        raise ValueError(f"{label} must be finite")
    return normalized


def _non_negative_integer(value: int, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{label} must be an integer")
    if value < 0:
        raise ValueError(f"{label} cannot be negative")
    return value


def _finite_solution(values: Iterable[float]) -> list[float]:
    if isinstance(values, (str, bytes, Mapping)) or not isinstance(values, Iterable):
        raise TypeError("best_position must be a numeric sequence")
    normalized = [
        _finite_float(value, "solution coordinate") for value in values
    ]
    if not normalized:
        raise ValueError("best_position cannot be empty")
    return normalized
