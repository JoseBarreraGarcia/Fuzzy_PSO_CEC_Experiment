"""Validated AFCS adapter for the CEC 2017 benchmark suite."""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np

from afcs.core import Evaluation, OptimizationDirection, SearchSpace
from afcs.problems.base import ProblemMetadata

from .functions import all_functions
from .transforms import CEC2017_DATA_SHA256

CEC2017_SUPPORTED_DIMENSIONS = frozenset((10, 30, 50, 100))
CEC2017_DEPRECATED_FUNCTIONS = frozenset((2,))
CEC2017_FUNCTION_NUMBERS = tuple(
    number for number in range(1, 31) if number not in CEC2017_DEPRECATED_FUNCTIONS
)


def get_function(function_number: int):
    """Return one supported raw vectorized function by official number."""

    if isinstance(function_number, bool) or not isinstance(function_number, int):
        raise TypeError("function_number must be an integer")
    if function_number in CEC2017_DEPRECATED_FUNCTIONS:
        raise ValueError("CEC2017 F2 was removed from the official suite")
    if function_number < 1 or function_number > len(all_functions):
        raise ValueError("function_number must be between 1 and 30")
    return all_functions[function_number - 1]


class CEC2017Problem:
    """One CEC 2017 function at one supported experimental dimension."""

    def __init__(self, function_number: int, dimension: int) -> None:
        function = get_function(function_number)
        if isinstance(dimension, bool) or not isinstance(dimension, int):
            raise TypeError("dimension must be an integer")
        if dimension not in CEC2017_SUPPORTED_DIMENSIONS:
            supported = sorted(CEC2017_SUPPORTED_DIMENSIONS)
            raise ValueError(
                f"Unsupported CEC2017 dimension {dimension}; expected one of {supported}"
            )
        self._function_number = function_number
        self._function = function
        self._metadata = ProblemMetadata(
            problem_id=f"F{function_number}CEC2017",
            family="CEC2017",
            search_space=SearchSpace.uniform(dimension, -100.0, 100.0),
            direction=OptimizationDirection.MINIMIZE,
            known_optimum=float(function_number * 100),
            parameters={
                "function_number": function_number,
                "suite": "CEC2017",
                "data_sha256": CEC2017_DATA_SHA256,
            },
        )

    @property
    def metadata(self) -> ProblemMetadata:
        return self._metadata

    @property
    def function_number(self) -> int:
        return self._function_number

    def evaluate(self, candidate: Sequence[float]) -> Evaluation:
        values = self.metadata.search_space.normalize_candidate(candidate)
        result = self._function(np.asarray(values, dtype=float).reshape(1, -1))
        objective = float(np.asarray(result).reshape(-1)[0])
        if not np.isfinite(objective):
            raise FloatingPointError(
                f"{self.metadata.problem_id} returned a non-finite objective"
            )
        return Evaluation(
            objective=objective,
            details={
                "suite": "CEC2017",
                "function_number": self.function_number,
                "dimension": self.metadata.dimension,
            },
        )
