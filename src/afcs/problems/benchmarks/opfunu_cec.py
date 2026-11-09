"""Auditable adapter for CEC suites distributed by the optional OPFUNU package."""

from __future__ import annotations

import math
from collections.abc import Sequence
from contextlib import redirect_stderr, redirect_stdout
from importlib.metadata import PackageNotFoundError, version
from io import StringIO

import numpy as np

from afcs.core import Evaluation, OptimizationDirection, SearchSpace
from afcs.problems import ProblemMetadata

OPFUNU_FAMILY = "OPFUNU_CEC"


def opfunu_version() -> str:
    try:
        return version("opfunu")
    except PackageNotFoundError as error:
        raise RuntimeError(
            "OPFUNU benchmarks require the optional dependency 'opfunu'"
        ) from error


class OpfunuCECProblem:
    """One explicitly identified function from an OPFUNU CEC suite."""

    def __init__(self, suite_year: int, function_number: int, dimension: int) -> None:
        for label, value in (
            ("suite_year", suite_year),
            ("function_number", function_number),
            ("dimension", dimension),
        ):
            if isinstance(value, bool) or not isinstance(value, int):
                raise TypeError(f"{label} must be an integer")
        if suite_year < 2000 or suite_year > 2099:
            raise ValueError("suite_year must be a four-digit year from 2000 to 2099")
        if function_number < 1 or dimension < 1:
            raise ValueError("function_number and dimension must be positive")

        package_version = opfunu_version()
        try:
            import opfunu.cec_based as cec_based
        except ImportError as error:
            raise RuntimeError(
                "OPFUNU benchmarks require the optional dependency 'opfunu'"
            ) from error
        class_name = f"F{function_number}{suite_year}"
        try:
            function_class = getattr(cec_based, class_name)
        except AttributeError as error:
            raise ValueError(f"OPFUNU does not expose {class_name}") from error
        dependency_output = StringIO()
        try:
            with redirect_stdout(dependency_output), redirect_stderr(dependency_output):
                function = function_class(ndim=dimension)
        except SystemExit as error:
            # Some OPFUNU releases call exit(1) when packaged data for a
            # dimension is unavailable. A library adapter must never allow an
            # invalid campaign entry to terminate the complete process.
            raise ValueError(
                f"OPFUNU {class_name} does not support dimension {dimension}"
            ) from error
        except Exception as error:
            detail = dependency_output.getvalue().strip() or str(error)
            raise ValueError(
                f"OPFUNU {class_name} does not support dimension {dimension}: {detail}"
            ) from error

        lower = tuple(float(value) for value in np.asarray(function.lb).reshape(-1))
        upper = tuple(float(value) for value in np.asarray(function.ub).reshape(-1))
        if len(lower) != dimension or len(upper) != dimension:
            raise ValueError(f"OPFUNU {class_name} returned inconsistent bounds")
        optimum = float(function.f_global)
        if not math.isfinite(optimum):
            raise ValueError(f"OPFUNU {class_name} returned a non-finite optimum")

        self._function = function
        self._metadata = ProblemMetadata(
            problem_id=f"F{function_number}CEC{suite_year}_OPFUNU",
            family=OPFUNU_FAMILY,
            search_space=SearchSpace(lower, upper),
            direction=OptimizationDirection.MINIMIZE,
            known_optimum=optimum,
            parameters={
                "suite": f"CEC{suite_year}",
                "suite_year": suite_year,
                "function_number": function_number,
                "implementation": "opfunu",
                "implementation_version": package_version,
                "implementation_class": class_name,
                "implementation_module": function_class.__module__,
            },
        )

    @property
    def metadata(self) -> ProblemMetadata:
        return self._metadata

    def evaluate(self, candidate: Sequence[float]) -> Evaluation:
        values = np.asarray(
            self.metadata.search_space.normalize_candidate(candidate), dtype=float
        )
        objective = float(self._function.evaluate(values))
        if not math.isfinite(objective):
            raise FloatingPointError(
                f"{self.metadata.problem_id} returned a non-finite objective"
            )
        return Evaluation(
            objective=objective,
            details={
                "suite": self.metadata.parameters["suite"],
                "implementation": "opfunu",
                "implementation_version": self.metadata.parameters[
                    "implementation_version"
                ],
            },
        )
