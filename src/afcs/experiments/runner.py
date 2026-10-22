"""Failure-safe execution of one planned experiment replica."""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
import math
from time import perf_counter

from afcs.experiments.contracts import RunnableOptimizer
from afcs.persistence import ExperimentRepository


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
            self._repository.complete_run(
                run_id=run_id,
                objective_best=objective,
                solution=solution,
                evaluations=evaluations,
                runtime_total_seconds=runtime,
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
