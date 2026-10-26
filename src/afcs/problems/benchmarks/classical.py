"""Versioned, self-contained adapter for the legacy F1--F23 suite."""

from __future__ import annotations

from dataclasses import dataclass
import math
from types import MappingProxyType
from typing import Callable, Sequence

import numpy as np

from afcs.core import Evaluation, OptimizationDirection, SearchSpace
from afcs.problems import ProblemMetadata


CLASSICAL_SUITE_VERSION = "legacy_classical_v1"


@dataclass(frozen=True, slots=True)
class ClassicalFunctionDefinition:
    number: int
    name: str
    lower_bound: float
    upper_bound: float
    optimum: float | Callable[[int], float]
    fixed_dimension: int | None = None
    stochastic: bool = False

    def optimum_for(self, dimension: int) -> float:
        value = self.optimum(dimension) if callable(self.optimum) else self.optimum
        return float(value)


_DEFINITIONS = {
    1: ClassicalFunctionDefinition(1, "Sphere", -100.0, 100.0, 0.0),
    2: ClassicalFunctionDefinition(2, "Schwefel 2.22", -10.0, 10.0, 0.0),
    3: ClassicalFunctionDefinition(3, "Schwefel 1.2", -100.0, 100.0, 0.0),
    4: ClassicalFunctionDefinition(4, "Schwefel 2.21", -100.0, 100.0, 0.0),
    5: ClassicalFunctionDefinition(5, "Rosenbrock", -30.0, 30.0, 0.0),
    6: ClassicalFunctionDefinition(6, "Legacy shifted quadratic", -100.0, 100.0, 0.0),
    7: ClassicalFunctionDefinition(7, "Quartic with noise", -1.28, 1.28, 0.0, stochastic=True),
    8: ClassicalFunctionDefinition(8, "Schwefel 2.26", -500.0, 500.0, lambda d: -418.9829 * d),
    9: ClassicalFunctionDefinition(9, "Rastrigin", -5.12, 5.12, 0.0),
    10: ClassicalFunctionDefinition(10, "Ackley", -32.0, 32.0, 0.0),
    11: ClassicalFunctionDefinition(11, "Griewank", -600.0, 600.0, 0.0),
    12: ClassicalFunctionDefinition(12, "Generalized Penalized 1", -50.0, 50.0, 0.0),
    13: ClassicalFunctionDefinition(13, "Generalized Penalized 2", -50.0, 50.0, 0.0),
    14: ClassicalFunctionDefinition(14, "Shekel Foxholes", -65.536, 65.536, 1.0, 2),
    15: ClassicalFunctionDefinition(15, "Kowalik", -5.0, 5.0, 0.00030, 4),
    16: ClassicalFunctionDefinition(16, "Six-Hump Camel", -5.0, 5.0, -1.0316, 2),
    17: ClassicalFunctionDefinition(17, "Branin RCOS", -5.0, 5.0, 0.398, 2),
    18: ClassicalFunctionDefinition(18, "Goldstein-Price", -2.0, 2.0, 3.0, 2),
    19: ClassicalFunctionDefinition(19, "Hartmann 3D", 0.0, 1.0, -3.86, 3),
    20: ClassicalFunctionDefinition(20, "Hartmann 6D", 0.0, 1.0, -3.32, 6),
    21: ClassicalFunctionDefinition(21, "Shekel 5", 0.0, 10.0, -10.1532, 4),
    22: ClassicalFunctionDefinition(22, "Shekel 7", 0.0, 10.0, -10.4029, 4),
    23: ClassicalFunctionDefinition(23, "Shekel 10", 0.0, 10.0, -10.5364, 4),
}
CLASSICAL_FUNCTIONS = MappingProxyType(_DEFINITIONS)


class ClassicalBenchmarkProblem:
    """Expose one F1--F23 instance through the common problem contract."""

    def __init__(
        self,
        function_number: int,
        dimension: int,
        *,
        noise_rng: np.random.Generator | None = None,
    ) -> None:
        if (
            isinstance(function_number, bool)
            or not isinstance(function_number, int)
            or function_number not in _DEFINITIONS
        ):
            raise ValueError("function_number must be an integer from 1 through 23")
        if isinstance(dimension, bool) or not isinstance(dimension, int) or dimension < 1:
            raise ValueError("dimension must be a positive integer")
        definition = _DEFINITIONS[function_number]
        if definition.fixed_dimension is not None and dimension != definition.fixed_dimension:
            raise ValueError(
                f"F{function_number} requires dimension {definition.fixed_dimension}"
            )
        if definition.stochastic and not isinstance(noise_rng, np.random.Generator):
            raise ValueError("F7 requires an explicit NumPy noise_rng")
        if not definition.stochastic and noise_rng is not None:
            raise ValueError("noise_rng is only applicable to stochastic F7")
        self.function_number = function_number
        self.definition = definition
        self._noise_rng = noise_rng
        self._metadata = ProblemMetadata(
            problem_id=f"F{function_number}",
            family="CLASSICAL",
            search_space=SearchSpace.uniform(
                dimension, definition.lower_bound, definition.upper_bound
            ),
            direction=OptimizationDirection.MINIMIZE,
            known_optimum=definition.optimum_for(dimension),
            parameters={
                "suite_version": CLASSICAL_SUITE_VERSION,
                "function_number": function_number,
                "function_name": definition.name,
                "stochastic": definition.stochastic,
            },
        )

    @property
    def metadata(self) -> ProblemMetadata:
        return self._metadata

    def evaluate(self, candidate: Sequence[float]) -> Evaluation:
        values = np.asarray(
            self.metadata.search_space.normalize_candidate(candidate), dtype=float
        )
        objective = _FUNCTIONS[self.function_number](values, self._noise_rng)
        objective = float(np.asarray(objective).item())
        if not math.isfinite(objective):
            raise FloatingPointError(f"F{self.function_number} produced a non-finite value")
        return Evaluation(objective=objective)


def create_classical_problem(
    problem_id: str, dimension: int, *, noise_rng: np.random.Generator | None = None
) -> ClassicalBenchmarkProblem:
    if not isinstance(problem_id, str) or not problem_id.upper().startswith("F"):
        raise ValueError("Classical problem_id must use the form 'F1' through 'F23'")
    try:
        number = int(problem_id[1:])
    except ValueError as error:
        raise ValueError("Classical problem_id must use the form 'F1' through 'F23'") from error
    if problem_id.upper() != f"F{number}":
        raise ValueError("Classical problem_id must use the canonical form 'F1' through 'F23'")
    return ClassicalBenchmarkProblem(number, dimension, noise_rng=noise_rng)


def _penalty(x: np.ndarray, a: float, k: float, m: int) -> np.ndarray:
    return k * (x - a) ** m * (x > a) + k * (-x - a) ** m * (x < -a)


def _f1(x, _): return np.sum(x**2)
def _f2(x, _): return np.sum(np.abs(x)) + np.prod(np.abs(x))
def _f3(x, _): return sum(np.sum(x[:i]) ** 2 for i in range(1, len(x) + 1))
def _f4(x, _): return np.max(np.abs(x))
def _f5(x, _): return np.sum(100 * (x[1:] - x[:-1] ** 2) ** 2 + (x[:-1] - 1) ** 2)
def _f6(x, _): return np.sum(np.abs(x + 0.5) ** 2)
def _f7(x, rng): return np.sum(np.arange(1, len(x) + 1) * x**4) + rng.uniform(0.0, 1.0)
def _f8(x, _): return np.sum(-x * np.sin(np.sqrt(np.abs(x))))
def _f9(x, _): return np.sum(x**2 - 10 * np.cos(2 * np.pi * x)) + 10 * len(x)
def _f10(x, _): return -20*np.exp(-0.2*np.sqrt(np.mean(x**2))) - np.exp(np.mean(np.cos(2*np.pi*x))) + 20 + np.e
def _f11(x, _): return np.sum(x**2)/4000 - np.prod(np.cos(x/np.sqrt(np.arange(1, len(x)+1)))) + 1


def _f12(x, _):
    y = 1 + (x + 1) / 4
    return (np.pi/len(x)) * (10*np.sin(np.pi*y[0])**2 + np.sum((y[:-1]-1)**2 * (1+10*np.sin(np.pi*y[1:])**2)) + (y[-1]-1)**2) + np.sum(_penalty(x, 10, 100, 4))


def _f13(x, _):
    return 0.1 * (np.sin(3*np.pi*x[0])**2 + np.sum((x[:-1]-1)**2 * (1+np.sin(3*np.pi*x[1:])**2)) + (x[-1]-1)**2 * (1+np.sin(2*np.pi*x[-1])**2)) + np.sum(_penalty(x, 5, 100, 4))


_FOXHOLES = np.asarray([
    [-32,-16,0,16,32,-32,-16,0,16,32,-32,-16,0,16,32,-32,-16,0,16,32,-32,-16,0,16,32],
    [-32,-32,-32,-32,-32,-16,-16,-16,-16,-16,0,0,0,0,0,16,16,16,16,16,32,32,32,32,32],
], dtype=float)


def _f14(x, _):
    powers = np.sum((x[:, None] - _FOXHOLES) ** 6, axis=0)
    return 1.0 / (1.0/500.0 + np.sum(1.0/(np.arange(1, 26) + powers)))


def _f15(x, _):
    a = np.asarray([.1957,.1947,.1735,.16,.0844,.0627,.0456,.0342,.0323,.0235,.0246])
    b = 1/np.asarray([.25,.5,1,2,4,6,8,10,12,14,16])
    return np.sum((a - x[0]*(b**2+x[1]*b)/(b**2+x[2]*b+x[3]))**2)


def _f16(x, _): return 4*x[0]**2 - 2.1*x[0]**4 + x[0]**6/3 + x[0]*x[1] - 4*x[1]**2 + 4*x[1]**4
def _f17(x, _): return (x[1]-5.1*x[0]**2/(4*np.pi**2)+5*x[0]/np.pi-6)**2 + 10*(1-1/(8*np.pi))*np.cos(x[0])+10


def _f18(x, _):
    a, b = x
    return (1+(a+b+1)**2*(19-14*a+3*a*a-14*b+6*a*b+3*b*b)) * (30+(2*a-3*b)**2*(18-32*a+12*a*a+48*b-36*a*b+27*b*b))


_HARTMANN_C = np.asarray([1, 1.2, 3, 3.2])


def _hartmann(x, alpha, centres):
    return -np.sum(_HARTMANN_C * np.exp(-np.sum(alpha * (x - centres) ** 2, axis=1)))


def _f19(x, _):
    a = np.asarray([[3,10,30],[.1,10,35],[3,10,30],[.1,10,35]])
    p = np.asarray([[.3689,.117,.2673],[.4699,.4387,.747],[.1091,.8732,.5547],[.03815,.5743,.8828]])
    return _hartmann(x, a, p)


def _f20(x, _):
    a = np.asarray([[10,3,17,3.5,1.7,8],[.05,10,17,.1,8,14],[3,3.5,1.7,10,17,8],[17,8,.05,10,.1,14]])
    p = np.asarray([[.1312,.1696,.5569,.0124,.8283,.5886],[.2329,.4135,.8307,.3736,.1004,.9991],[.2348,.1415,.3522,.2883,.3047,.665],[.4047,.8828,.8732,.5743,.1091,.0381]])
    return _hartmann(x, a, p)


_SHEKEL_A = np.asarray([[4,4,4,4],[1,1,1,1],[8,8,8,8],[6,6,6,6],[3,7,3,7],[2,9,2,9],[5,5,3,3],[8,1,8,1],[6,2,6,2],[7,3.6,7,3.6]], dtype=float)
_SHEKEL_C = np.asarray([.1,.2,.2,.4,.4,.6,.3,.7,.5,.5])


def _shekel(x, terms): return -np.sum(1.0/(np.sum((x-_SHEKEL_A[:terms])**2, axis=1)+_SHEKEL_C[:terms]))
def _f21(x, _): return _shekel(x, 5)
def _f22(x, _): return _shekel(x, 7)
def _f23(x, _): return _shekel(x, 10)


_FUNCTIONS = {number: globals()[f"_f{number}"] for number in range(1, 24)}

