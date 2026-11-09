"""PSO-specific parameter policies."""

from __future__ import annotations

import math
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from time import perf_counter
from types import MappingProxyType

import numpy as np

from afcs.controllers import ParameterUpdate
from afcs.fuzzy import SUPPORTED_OVERLAP_DEFINITIONS, MamdaniController
from afcs.metrics import hussain_diversity_v1, hussain_diversity_v2
from afcs.optimizers import SearchState


@dataclass(frozen=True, slots=True)
class FixedInertia:
    """Return the same inertia value at every PSO transition."""

    value: float

    policy_id = "fixed_inertia"
    policy_version = "1"
    compatible_parameters = ("w",)

    def __post_init__(self) -> None:
        if isinstance(self.value, bool):
            raise TypeError("inertia value must be numeric")
        try:
            value = float(self.value)
        except (TypeError, ValueError) as error:
            raise TypeError("inertia value must be numeric") from error
        if not math.isfinite(value):
            raise ValueError("inertia value must be finite")
        object.__setattr__(self, "value", value)

    @property
    def configuration(self) -> Mapping[str, float]:
        return MappingProxyType({"value": self.value})

    def propose(
        self,
        state: SearchState,
        current_parameters: Mapping[str, float],
    ) -> ParameterUpdate:
        if not isinstance(state, SearchState):
            raise TypeError("state must be SearchState")
        if not isinstance(current_parameters, Mapping):
            raise TypeError("current_parameters must be a mapping")
        return ParameterUpdate(
            policy_id=self.policy_id,
            policy_version=self.policy_version,
            values={"w": self.value},
            reason="configured fixed inertia",
        )


@dataclass(frozen=True, slots=True)
class LegacyLinearInertia:
    """Historical 0.9→0.1 schedule retained only for compatibility."""

    max_iterations: int
    maximum: float = 0.9
    minimum: float = 0.1

    policy_id = "legacy_ldiw"
    policy_version = "1"
    compatible_parameters = ("w",)

    def __post_init__(self) -> None:
        if (
            isinstance(self.max_iterations, bool)
            or not isinstance(self.max_iterations, int)
            or self.max_iterations <= 0
        ):
            raise ValueError("max_iterations must be a positive integer")
        if not math.isfinite(self.maximum) or not math.isfinite(self.minimum):
            raise ValueError("Inertia bounds must be finite")
        if self.minimum > self.maximum:
            raise ValueError("minimum inertia cannot exceed maximum inertia")

    def value_at(self, iteration: int) -> float:
        if isinstance(iteration, bool) or not isinstance(iteration, int):
            raise TypeError("iteration must be an integer")
        if iteration < 0 or iteration > self.max_iterations:
            raise ValueError("iteration must be between zero and max_iterations")
        return self.maximum - iteration * (
            (self.maximum - self.minimum) / self.max_iterations
        )

    @property
    def configuration(self) -> Mapping[str, float | int]:
        return MappingProxyType(
            {
                "max_iterations": self.max_iterations,
                "maximum": self.maximum,
                "minimum": self.minimum,
            }
        )

    def propose(
        self,
        state: SearchState,
        current_parameters: Mapping[str, float],
    ) -> ParameterUpdate:
        if not isinstance(state, SearchState):
            raise TypeError("state must be SearchState")
        return ParameterUpdate(
            policy_id=self.policy_id,
            policy_version=self.policy_version,
            values={"w": self.value_at(state.iteration)},
            reason=f"{self.policy_id} inertia schedule",
        )


class EndpointLinearInertia(LegacyLinearInertia):
    """Linear movement weights including both endpoints; one movement uses maximum."""

    policy_id = "linear_endpoints_v1"

    def value_at(self, iteration: int) -> float:
        super().value_at(iteration)
        if iteration <= 1 or self.max_iterations == 1:
            return self.maximum
        if iteration == self.max_iterations:
            return self.minimum
        return self.maximum - (self.maximum - self.minimum) * (
            (iteration - 1) / (self.max_iterations - 1)
        )


class FuzzyInertiaPolicy:
    """Mamdani control of PSO inertia from Hussain diversity and t/T progress."""

    policy_id = "fuzzy_inertia_mamdani"
    policy_version = "1"
    compatible_parameters: tuple[str, ...] = ("w",)

    def __init__(
        self,
        *,
        max_iterations: int,
        minimum: float = 0.1,
        maximum: float = 0.9,
        granularity: int,
        rule_base: str,
        membership_family: str = "triangular_v1",
        overlap_mode: str = "shared",
        overlap: float | None = None,
        diversity_overlap: float | None = None,
        progress_overlap: float | None = None,
        output_overlap: float | None = None,
        zero_overlap_boundary_policy: str = "nearest_center_tie_upper",
        centroid_grid_points: int = 501,
        inference_evaluation_mode: str = "dense_v1",
        diversity_metric: str = "hussain_diversity_v1",
        clock: Callable[[], float] = perf_counter,
    ) -> None:
        if diversity_metric not in {"hussain_diversity_v1", "hussain_diversity_v2"}:
            raise ValueError("Unsupported fuzzy diversity_metric")
        self.diversity_metric = diversity_metric
        self.policy_version = "1" if diversity_metric == "hussain_diversity_v1" else "2"
        if (
            isinstance(max_iterations, bool)
            or not isinstance(max_iterations, int)
            or max_iterations <= 0
        ):
            raise ValueError("max_iterations must be a positive integer")
        minimum = float(minimum)
        maximum = float(maximum)
        if (
            not math.isfinite(minimum)
            or not math.isfinite(maximum)
            or minimum >= maximum
        ):
            raise ValueError(
                "minimum and maximum must be finite with minimum < maximum"
            )
        if overlap_mode == "shared":
            if overlap is None:
                raise ValueError("shared overlap mode requires overlap")
            if any(
                value is not None
                for value in (diversity_overlap, progress_overlap, output_overlap)
            ):
                raise ValueError(
                    "shared overlap mode cannot declare independent overlaps"
                )
            diversity_overlap = progress_overlap = output_overlap = overlap
        elif overlap_mode == "independent":
            if overlap is not None:
                raise ValueError(
                    "independent overlap mode cannot declare shared overlap"
                )
            if (
                diversity_overlap is None
                or progress_overlap is None
                or output_overlap is None
            ):
                raise ValueError("independent overlap mode requires all three overlaps")
        else:
            raise ValueError("overlap_mode must be 'shared' or 'independent'")
        if zero_overlap_boundary_policy != "nearest_center_tie_upper":
            raise ValueError(
                "zero_overlap_boundary_policy must be 'nearest_center_tie_upper'"
            )
        if not callable(clock):
            raise TypeError("clock must be callable")

        self.max_iterations = max_iterations
        self.minimum = minimum
        self.maximum = maximum
        self.granularity = granularity
        self.rule_base = rule_base
        self.membership_family = membership_family
        self.overlap_mode = overlap_mode
        self.diversity_overlap = float(diversity_overlap)
        self.progress_overlap = float(progress_overlap)
        self.output_overlap = float(output_overlap)
        self.zero_overlap_boundary_policy = zero_overlap_boundary_policy
        self.centroid_grid_points = centroid_grid_points
        self.inference_evaluation_mode = inference_evaluation_mode
        self._clock = clock
        self._controller = MamdaniController(
            granularity=granularity,
            rule_base=rule_base,
            membership_family=membership_family,
            diversity_overlap=self.diversity_overlap,
            progress_overlap=self.progress_overlap,
            output_overlap=self.output_overlap,
            zero_overlap_boundary_policy=zero_overlap_boundary_policy,
            centroid_grid_points=centroid_grid_points,
            evaluation_mode=inference_evaluation_mode,
        )
        self._maximum_diversity = 0.0
        self._inference_calls = 0
        self._inference_time_seconds = 0.0
        self._boundary_event_count = 0
        self._evaluated_rule_count = 0
        self._skipped_rule_count = 0
        self._no_activation_count = 0
        self._fallback_count = 0
        self._last_diagnostics: Mapping[str, object] = MappingProxyType({})

    @property
    def configuration(self) -> Mapping[str, object]:
        overlap_config: dict[str, object] = {"mode": self.overlap_mode}
        if self.overlap_mode == "shared":
            overlap_config["value"] = self.diversity_overlap
        else:
            overlap_config.update(
                diversity=self.diversity_overlap,
                progress=self.progress_overlap,
                output=self.output_overlap,
            )
        return MappingProxyType(
            {
                "max_iterations": self.max_iterations,
                "minimum": self.minimum,
                "maximum": self.maximum,
                "granularity": self.granularity,
                "rule_base": self.rule_base,
                "membership_family": self.membership_family,
                "overlap_definition": SUPPORTED_OVERLAP_DEFINITIONS[
                    self.membership_family
                ],
                "overlap": overlap_config,
                "diversity_metric": self.diversity_metric,
                "diversity_normalization": "running_max_ratio_v1",
                "progress": "iteration_over_max_iterations_v1",
                "zero_overlap_boundary_policy": self.zero_overlap_boundary_policy,
                "inference": "mamdani_min_max_centroid_v1",
                "centroid_grid_points": self.centroid_grid_points,
                "inference_evaluation_mode": self.inference_evaluation_mode,
            }
        )

    @property
    def last_diagnostics(self) -> Mapping[str, object]:
        return self._last_diagnostics

    @property
    def summary_metrics(self) -> Mapping[str, object]:
        return MappingProxyType(
            {
                "fuzzy_runtime_total_seconds": self._inference_time_seconds,
                "fuzzy_inference_call_count": self._inference_calls,
                "fuzzy_boundary_event_count": self._boundary_event_count,
                "fuzzy_evaluated_rule_count": self._evaluated_rule_count,
                "fuzzy_skipped_rule_count": self._skipped_rule_count,
                "fuzzy_no_activation_count": self._no_activation_count,
                "fuzzy_fallback_count": self._fallback_count,
            }
        )

    def propose(
        self,
        state: SearchState,
        current_parameters: Mapping[str, float],
    ) -> ParameterUpdate:
        if not isinstance(state, SearchState):
            raise TypeError("state must be SearchState")
        if state.iteration < 1 or state.iteration > self.max_iterations:
            raise ValueError("fuzzy policy is called only for iterations 1..T")
        positions = state.observations.get("positions")
        if positions is None:
            raise ValueError("fuzzy policy requires the current swarm positions")
        diversity_function = (
            hussain_diversity_v1
            if self.diversity_metric == "hussain_diversity_v1"
            else hussain_diversity_v2
        )
        diversity = diversity_function(np.asarray(positions, dtype=float))
        self._maximum_diversity = max(self._maximum_diversity, diversity)
        diversity_ratio = (
            0.0
            if self._maximum_diversity == 0.0
            else diversity / self._maximum_diversity
        )
        progress = state.iteration / self.max_iterations
        inference_started = float(self._clock())
        inference = self._controller.infer(diversity_ratio, progress)
        inference_finished = float(self._clock())
        inference_time = inference_finished - inference_started
        if not math.isfinite(inference_time) or inference_time < 0.0:
            raise ValueError("clock must produce finite monotonic inference timing")
        self._inference_calls += 1
        self._inference_time_seconds += inference_time
        self._boundary_event_count += inference.boundary_events
        self._evaluated_rule_count += inference.evaluated_rule_count
        self._skipped_rule_count += inference.skipped_rule_count
        inertia = self.minimum + inference.normalized_output * (
            self.maximum - self.minimum
        )
        self._last_diagnostics = MappingProxyType(
            {
                "diversity_hussain": diversity,
                "diversity_maximum": self._maximum_diversity,
                "diversity_ratio": diversity_ratio,
                "progress_ratio": progress,
                "normalized_output": inference.normalized_output,
                "active_rule_count": len(inference.active_rules),
                "evaluated_rule_count": inference.evaluated_rule_count,
                "skipped_rule_count": inference.skipped_rule_count,
                "boundary_event_count": inference.boundary_events,
                "no_activation_count": 0,
                "fallback_count": 0,
                "inference_time_seconds": inference_time,
                "membership_degrees": {
                    "diversity": {
                        f"L{index}": degree
                        for index, degree in enumerate(inference.diversity_degrees)
                    },
                    "progress": {
                        f"L{index}": degree
                        for index, degree in enumerate(inference.progress_degrees)
                    },
                },
                "active_rules": [
                    f"D{d}:P{p}->W{w}" for d, p, w, _firing in inference.active_rules
                ],
                "rule_firing_strengths": {
                    f"D{d}:P{p}->W{w}": firing
                    for d, p, w, firing in inference.active_rules
                },
            }
        )
        return ParameterUpdate(
            policy_id=self.policy_id,
            policy_version=self.policy_version,
            values={"w": inertia},
            reason="Mamdani control from Hussain diversity and iteration progress",
        )
