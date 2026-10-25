"""Versioned membership functions and uniform partition construction."""

from __future__ import annotations

from dataclasses import dataclass
import math


SUPPORTED_MEMBERSHIP_FAMILIES = ("triangular_v1", "gaussian_v1")
SUPPORTED_OVERLAP_DEFINITIONS = {
    "triangular_v1": "geometric_support_v1",
    "gaussian_v1": "two_sigma_geometric_v1",
}


@dataclass(frozen=True, slots=True)
class MembershipFunction:
    family: str
    center: float
    width: float
    left_shoulder: bool = False
    right_shoulder: bool = False

    def degree(self, value: float) -> float:
        x = float(value)
        if not math.isfinite(x):
            raise ValueError("membership input must be finite")
        if self.family == "triangular_v1":
            if self.left_shoulder and x <= self.center:
                return 1.0
            if self.right_shoulder and x >= self.center:
                return 1.0
            distance = abs(x - self.center)
            return max(0.0, 1.0 - distance / self.width)
        if self.family == "gaussian_v1":
            exponent = -0.5 * ((x - self.center) / self.width) ** 2
            return math.exp(exponent)
        raise ValueError(f"unsupported membership family: {self.family!r}")


def uniform_partition(
    *,
    granularity: int,
    family: str,
    overlap: float,
) -> tuple[MembershipFunction, ...]:
    """Create a uniform partition on [0, 1] using the approved overlap index.

    Triangular half-support is ``delta * (1 + overlap) / 2``. Gaussian spread
    follows the approved effective-support convention ``2 sigma = h(overlap)``.
    """

    if isinstance(granularity, bool) or not isinstance(granularity, int):
        raise TypeError("granularity must be an integer")
    if granularity < 3 or granularity % 2 == 0:
        raise ValueError("granularity must be an odd integer >= 3")
    if family not in SUPPORTED_MEMBERSHIP_FAMILIES:
        raise ValueError(
            f"membership family must be one of {list(SUPPORTED_MEMBERSHIP_FAMILIES)}"
        )
    if isinstance(overlap, bool):
        raise TypeError("overlap must be numeric")
    overlap = float(overlap)
    if not math.isfinite(overlap) or not 0.0 <= overlap <= 1.0:
        raise ValueError("overlap must be finite and between 0 and 1")

    delta = 1.0 / (granularity - 1)
    width = delta * (1.0 + overlap) / 2.0
    if family == "gaussian_v1":
        width /= 2.0  # width stores sigma; effective radius is 2 sigma.
    return tuple(
        MembershipFunction(
            family=family,
            center=index * delta,
            width=width,
            left_shoulder=family == "triangular_v1" and index == 0,
            right_shoulder=(
                family == "triangular_v1" and index == granularity - 1
            ),
        )
        for index in range(granularity)
    )


def fuzzify(
    value: float,
    partition: tuple[MembershipFunction, ...],
    *,
    zero_overlap_boundary_policy: str,
    tolerance: float = 1e-12,
) -> tuple[tuple[float, ...], bool]:
    """Return degrees and whether the zero-overlap boundary policy was used."""

    x = min(1.0, max(0.0, float(value)))
    degrees = tuple(membership.degree(x) for membership in partition)
    if any(degree > tolerance for degree in degrees):
        return degrees, False
    if zero_overlap_boundary_policy != "nearest_center_tie_upper":
        raise ValueError("fuzzy input has no active membership function")
    distances = tuple(abs(x - membership.center) for membership in partition)
    nearest_distance = min(distances)
    nearest = [
        index
        for index, distance in enumerate(distances)
        if math.isclose(distance, nearest_distance, abs_tol=tolerance, rel_tol=0.0)
    ]
    selected = max(nearest)
    categorical = tuple(1.0 if index == selected else 0.0 for index in range(len(partition)))
    return categorical, True
