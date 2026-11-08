"""Extensible construction of optimization problems from persisted identity."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from types import MappingProxyType
from typing import Any

from afcs.core import ReplicaRandomStreams

from .base import OptimizationProblem
from .benchmarks import (
    CLASSICAL_FUNCTIONS,
    ClassicalBenchmarkProblem,
    OpfunuCECProblem,
)
from .benchmarks.cec2017 import CEC2017Problem


ProblemBuilder = Callable[
    [int, Mapping[str, Any], ReplicaRandomStreams], OptimizationProblem
]


class ProblemFactory:
    """Build one problem without coupling its family to an optimizer."""

    def __init__(self, builders: Mapping[str, ProblemBuilder] | None = None) -> None:
        configured = dict(
            {
                "CEC2017": _build_cec2017,
                "CLASSICAL": _build_classical,
                "OPFUNU_CEC": _build_opfunu_cec,
            }
            if builders is None
            else builders
        )
        if not configured or any(
            not isinstance(family, str)
            or not family.strip()
            or not callable(builder)
            for family, builder in configured.items()
        ):
            raise ValueError("builders must map problem family IDs to callables")
        self._builders = MappingProxyType(configured)

    @property
    def supported_families(self) -> tuple[str, ...]:
        return tuple(self._builders)

    def build(
        self,
        *,
        family: str,
        dimension: int,
        parameters: Mapping[str, Any],
        random_streams: ReplicaRandomStreams,
    ) -> OptimizationProblem:
        if not isinstance(family, str) or not family.strip():
            raise ValueError("family must be a non-empty string")
        if isinstance(dimension, bool) or not isinstance(dimension, int):
            raise TypeError("dimension must be an integer")
        if dimension < 1:
            raise ValueError("dimension must be positive")
        if not isinstance(parameters, Mapping):
            raise TypeError("parameters must be a mapping")
        if not isinstance(random_streams, ReplicaRandomStreams):
            raise TypeError("random_streams must be ReplicaRandomStreams")
        try:
            builder = self._builders[family]
        except KeyError as error:
            raise ValueError(
                f"Unsupported problem family {family!r}; "
                f"available={list(self._builders)}"
            ) from error
        problem = builder(dimension, parameters, random_streams)
        if not isinstance(problem, OptimizationProblem):
            raise TypeError("problem builder must return OptimizationProblem")
        if problem.metadata.family != family:
            raise ValueError("problem builder returned a different family")
        if problem.metadata.dimension != dimension:
            raise ValueError("problem builder returned a different dimension")
        return problem


def _function_number(parameters: Mapping[str, Any]) -> int:
    value = parameters.get("function_number")
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError("Benchmark problem requires an integer function_number")
    return value


def _build_cec2017(
    dimension: int,
    parameters: Mapping[str, Any],
    random_streams: ReplicaRandomStreams,
) -> OptimizationProblem:
    del random_streams
    return CEC2017Problem(_function_number(parameters), dimension)


def _build_classical(
    dimension: int,
    parameters: Mapping[str, Any],
    random_streams: ReplicaRandomStreams,
) -> OptimizationProblem:
    function_number = _function_number(parameters)
    try:
        definition = CLASSICAL_FUNCTIONS[function_number]
    except KeyError as error:
        raise ValueError("Unsupported classical function number") from error
    return ClassicalBenchmarkProblem(
        function_number,
        dimension,
        noise_rng=(
            random_streams.generator("problem") if definition.stochastic else None
        ),
    )


def _build_opfunu_cec(
    dimension: int,
    parameters: Mapping[str, Any],
    random_streams: ReplicaRandomStreams,
) -> OptimizationProblem:
    del random_streams
    suite_year = parameters.get("suite_year")
    if isinstance(suite_year, bool) or not isinstance(suite_year, int):
        raise ValueError("OPFUNU_CEC problem requires an integer suite_year")
    return OpfunuCECProblem(suite_year, _function_number(parameters), dimension)


DEFAULT_PROBLEM_FACTORY = ProblemFactory()
