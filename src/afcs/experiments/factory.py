"""Build executable optimizers from the canonical persisted run plan."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from types import MappingProxyType

from afcs.core import ReplicaRandomStreams
from afcs.metrics import PSOTraceCollector, TraceSampling
from afcs.optimizers.pso import (
    FixedInertia,
    FuzzyInertiaPolicy,
    LegacyCompatiblePSO,
    LegacyLinearInertia,
    LegacyPSORunConfig,
)
from afcs.persistence import PlannedRun
from afcs.problems.benchmarks.cec2017 import CEC2017Problem

from .contracts import RunnableOptimizer


OptimizerBuilder = Callable[[PlannedRun, tuple[str, ...]], RunnableOptimizer]
PSO_VERSION = "2.0.0a0-legacy-compatible"


class OptimizerFactory:
    """Extensible catalog that turns one database plan into an optimizer."""

    def __init__(
        self, builders: Mapping[str, OptimizerBuilder] | None = None
    ) -> None:
        configured = dict({"PSO": _build_pso} if builders is None else builders)
        if not configured or any(
            not isinstance(name, str) or not name or not callable(builder)
            for name, builder in configured.items()
        ):
            raise ValueError("builders must map optimizer IDs to callables")
        self._builders = MappingProxyType(configured)

    @property
    def supported_optimizers(self) -> tuple[str, ...]:
        return tuple(self._builders)

    def build(
        self,
        plan: PlannedRun,
        *,
        selected_metrics: tuple[str, ...] = (),
    ) -> RunnableOptimizer:
        if not isinstance(plan, PlannedRun):
            raise TypeError("plan must be PlannedRun")
        try:
            builder = self._builders[plan.algorithm]
        except KeyError as error:
            raise ValueError(
                f"Unsupported persisted optimizer {plan.algorithm!r}; "
                f"available={list(self._builders)}"
            ) from error
        optimizer = builder(plan, selected_metrics)
        if not isinstance(optimizer, RunnableOptimizer):
            raise TypeError("optimizer builder must return RunnableOptimizer")
        return optimizer


def _build_pso(
    plan: PlannedRun, selected_metrics: tuple[str, ...]
) -> LegacyCompatiblePSO:
    if plan.optimizer_version != PSO_VERSION:
        raise ValueError(
            f"Unsupported PSO version {plan.optimizer_version!r}; expected {PSO_VERSION!r}"
        )
    if plan.problem_family != "CEC2017":
        raise ValueError("The v1 PSO builder currently supports only CEC2017")
    if plan.dimension is None:
        raise ValueError("CEC2017 plan requires a dimension")
    if plan.population_size is None or plan.budget_iterations is None:
        raise ValueError("PSO plan requires population and iteration budgets")
    if plan.random_seed is None or plan.rng_engine is None:
        raise ValueError("PSO plan requires persisted replica randomness")

    function_number = plan.problem_parameters.get("function_number")
    if isinstance(function_number, bool) or not isinstance(function_number, int):
        raise ValueError("CEC2017 plan requires an integer function_number")
    problem = CEC2017Problem(function_number, plan.dimension)
    trace = plan.campaign_config.get("trace")
    if not isinstance(trace, Mapping):
        raise ValueError("Persisted campaign requires trace configuration")
    sampling = TraceSampling(
        enabled=trace.get("enabled"),
        every_iterations=trace.get("every_iterations"),
        include_initial=trace.get("include_initial"),
        include_final=trace.get("include_final"),
    )

    parameters = plan.algorithm_parameters
    policy_data = parameters.get("inertia_policy")
    if not isinstance(policy_data, Mapping):
        raise ValueError("PSO plan requires inertia_policy metadata")
    policy = _build_inertia_policy(policy_data, plan.budget_iterations)
    config = LegacyPSORunConfig(
        population_size=plan.population_size,
        max_iterations=plan.budget_iterations,
        cognitive=parameters.get("cognitive", 2.0),
        social=parameters.get("social", 2.0),
        velocity_factor=parameters.get("velocity_factor", 0.1),
    )
    streams = ReplicaRandomStreams(plan.random_seed, engine=plan.rng_engine)
    collector = PSOTraceCollector(
        selected_metrics=selected_metrics,
        sampling=sampling,
        maximum_iteration=plan.budget_iterations,
        lower_bounds=problem.metadata.search_space.lower_bounds,
        upper_bounds=problem.metadata.search_space.upper_bounds,
    )
    return LegacyCompatiblePSO(
        problem=problem,
        config=config,
        inertia_policy=policy,
        random_streams=streams,
        trace_collector=collector,
    )


def _build_inertia_policy(raw: Mapping, max_iterations: int):
    policy_id = raw.get("policy_id")
    version = raw.get("policy_version")
    configuration = raw.get("configuration")
    if version != "1" or not isinstance(configuration, Mapping):
        raise ValueError("Unsupported or malformed inertia policy metadata")
    if policy_id == "fixed_inertia":
        return FixedInertia(configuration.get("value"))
    if policy_id == "legacy_ldiw":
        persisted_iterations = configuration.get("max_iterations")
        if persisted_iterations != max_iterations:
            raise ValueError("legacy_ldiw iteration budget does not match the plan")
        return LegacyLinearInertia(
            max_iterations=max_iterations,
            maximum=configuration.get("maximum", 0.9),
            minimum=configuration.get("minimum", 0.1),
        )
    if policy_id == "fuzzy_inertia_mamdani":
        persisted_iterations = configuration.get("max_iterations")
        if persisted_iterations != max_iterations:
            raise ValueError("fuzzy policy iteration budget does not match the plan")
        overlap = configuration.get("overlap")
        if not isinstance(overlap, Mapping):
            raise ValueError("fuzzy policy requires persisted overlap configuration")
        overlap_arguments = {"overlap_mode": overlap.get("mode")}
        if overlap.get("mode") == "shared":
            overlap_arguments["overlap"] = overlap.get("value")
        else:
            overlap_arguments.update(
                diversity_overlap=overlap.get("diversity"),
                progress_overlap=overlap.get("progress"),
                output_overlap=overlap.get("output"),
            )
        return FuzzyInertiaPolicy(
            max_iterations=max_iterations,
            minimum=configuration.get("minimum"),
            maximum=configuration.get("maximum"),
            granularity=configuration.get("granularity"),
            rule_base=configuration.get("rule_base"),
            membership_family=configuration.get("membership_family"),
            zero_overlap_boundary_policy=configuration.get(
                "zero_overlap_boundary_policy"
            ),
            centroid_grid_points=configuration.get("centroid_grid_points", 501),
            inference_evaluation_mode=configuration.get(
                "inference_evaluation_mode", "dense_v1"
            ),
            **overlap_arguments,
        )
    raise ValueError(f"Unsupported inertia policy: {policy_id!r}")
