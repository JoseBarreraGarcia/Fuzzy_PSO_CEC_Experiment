"""Build executable optimizers from the canonical persisted run plan."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from types import MappingProxyType

from afcs.controllers import NoAdaptation
from afcs.core import ReplicaRandomStreams
from afcs.metrics import PSOTraceCollector, TraceSampling, load_metric_registry
from afcs.optimizers.ga import (
    GA_IMPLEMENTATION_VERSION,
    GATraceCollector,
    RealCodedGA,
    RealCodedGARunConfig,
)
from afcs.optimizers.pso import (
    PSO_DOMAIN_WIDTH_VERSION,
    PSO_IMPLEMENTATION_VERSION,
    EndpointLinearInertia,
    FixedInertia,
    FuzzyInertiaPolicy,
    LegacyCompatiblePSO,
    LegacyLinearInertia,
    LegacyPSORunConfig,
)
from afcs.persistence import PlannedRun
from afcs.problems import DEFAULT_PROBLEM_FACTORY

from .contracts import RunnableOptimizer

OptimizerBuilder = Callable[[PlannedRun, tuple[str, ...]], RunnableOptimizer]


class OptimizerFactory:
    """Extensible catalog that turns one database plan into an optimizer."""

    def __init__(self, builders: Mapping[str, OptimizerBuilder] | None = None) -> None:
        configured = (
            {"PSO": _build_pso, "GA": _build_ga} if builders is None else dict(builders)
        )
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
        if not selected_metrics:
            selected_metrics = load_metric_registry().resolve("minimal")
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
    velocity_rule = plan.algorithm_parameters.get("velocity_rule", "legacy_upper0_v1")
    expected_version = (
        PSO_IMPLEMENTATION_VERSION
        if velocity_rule == "legacy_upper0_v1"
        else PSO_DOMAIN_WIDTH_VERSION
    )
    if plan.optimizer_version != expected_version:
        raise ValueError(
            f"Unsupported PSO version {plan.optimizer_version!r}; "
            f"expected {expected_version!r}"
        )
    if plan.dimension is None:
        raise ValueError("Continuous benchmark plan requires a dimension")
    if plan.population_size is None or plan.budget_iterations is None:
        raise ValueError("PSO plan requires population and iteration budgets")
    if plan.random_seed is None or plan.rng_engine is None:
        raise ValueError("PSO plan requires persisted replica randomness")

    streams = ReplicaRandomStreams(plan.random_seed, engine=plan.rng_engine)
    problem = DEFAULT_PROBLEM_FACTORY.build(
        family=plan.problem_family,
        dimension=plan.dimension,
        parameters=plan.problem_parameters,
        random_streams=streams,
    )
    trace = plan.campaign_config.get("trace")
    if not isinstance(trace, Mapping):
        raise ValueError("Persisted campaign requires trace configuration")
    sampling = TraceSampling(
        enabled=trace["enabled"],
        every_iterations=trace["every_iterations"],
        include_initial=trace["include_initial"],
        include_final=trace["include_final"],
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
        velocity_rule=velocity_rule,
    )
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


def _build_ga(plan: PlannedRun, selected_metrics: tuple[str, ...]) -> RealCodedGA:
    if plan.optimizer_version != GA_IMPLEMENTATION_VERSION:
        raise ValueError(
            f"Unsupported GA version {plan.optimizer_version!r}; "
            f"expected {GA_IMPLEMENTATION_VERSION!r}"
        )
    if plan.dimension is None:
        raise ValueError("Continuous benchmark plan requires a dimension")
    if plan.population_size is None or plan.budget_iterations is None:
        raise ValueError("GA plan requires population and iteration budgets")
    if plan.random_seed is None or plan.rng_engine is None:
        raise ValueError("GA plan requires persisted replica randomness")

    streams = ReplicaRandomStreams(plan.random_seed, engine=plan.rng_engine)
    problem = DEFAULT_PROBLEM_FACTORY.build(
        family=plan.problem_family,
        dimension=plan.dimension,
        parameters=plan.problem_parameters,
        random_streams=streams,
    )
    trace = plan.campaign_config.get("trace")
    if not isinstance(trace, Mapping):
        raise ValueError("Persisted campaign requires trace configuration")
    sampling = TraceSampling(
        enabled=trace["enabled"],
        every_iterations=trace["every_iterations"],
        include_initial=trace["include_initial"],
        include_final=trace["include_final"],
    )

    parameters = plan.algorithm_parameters
    policy_data = parameters.get("parameter_policy")
    if (
        not isinstance(policy_data, Mapping)
        or policy_data.get("policy_id") != "no_adaptation"
        or policy_data.get("policy_version") != "1"
        or policy_data.get("configuration") != {}
    ):
        raise ValueError("GA currently requires the no_adaptation parameter policy")
    mutation_probability = parameters.get("mutation_probability")
    if mutation_probability == "1/d":
        mutation_probability = None
    config = RealCodedGARunConfig(
        population_size=plan.population_size,
        max_iterations=plan.budget_iterations,
        crossover_probability=parameters["crossover_probability"],
        crossover_distribution_index=parameters["crossover_distribution_index"],
        mutation_probability=mutation_probability,
        mutation_distribution_index=parameters["mutation_distribution_index"],
        tournament_size=parameters["tournament_size"],
    )
    collector = GATraceCollector(
        selected_metrics=selected_metrics,
        sampling=sampling,
        maximum_iteration=plan.budget_iterations,
        lower_bounds=problem.metadata.search_space.lower_bounds,
        upper_bounds=problem.metadata.search_space.upper_bounds,
    )
    return RealCodedGA(
        problem=problem,
        config=config,
        parameter_policy=NoAdaptation(),
        random_streams=streams,
        trace_collector=collector,
    )


def _build_inertia_policy(raw: Mapping, max_iterations: int):
    policy_id = raw.get("policy_id")
    version = raw.get("policy_version")
    configuration = raw.get("configuration")
    if not isinstance(configuration, Mapping):
        raise ValueError("Unsupported or malformed inertia policy metadata")
    expected_version = (
        "2"
        if policy_id == "fuzzy_inertia_mamdani"
        and configuration.get("diversity_metric") == "hussain_diversity_v2"
        else "1"
    )
    if version != expected_version:
        raise ValueError(
            "Inertia policy version disagrees with its scientific definition"
        )
    if policy_id == "fixed_inertia":
        return FixedInertia(configuration["value"])
    if policy_id in {"legacy_ldiw", "linear_endpoints_v1"}:
        persisted_iterations = configuration.get("max_iterations")
        if persisted_iterations != max_iterations:
            raise ValueError("linear inertia iteration budget does not match the plan")
        policy_type = (
            LegacyLinearInertia if policy_id == "legacy_ldiw" else EndpointLinearInertia
        )
        return policy_type(
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
        shared_overlap = overlap.get("mode") == "shared"
        return FuzzyInertiaPolicy(
            diversity_metric=configuration.get(
                "diversity_metric", "hussain_diversity_v1"
            ),
            max_iterations=max_iterations,
            minimum=configuration["minimum"],
            maximum=configuration["maximum"],
            granularity=configuration["granularity"],
            rule_base=configuration["rule_base"],
            membership_family=configuration["membership_family"],
            zero_overlap_boundary_policy=configuration["zero_overlap_boundary_policy"],
            centroid_grid_points=configuration.get("centroid_grid_points", 501),
            inference_evaluation_mode=configuration.get(
                "inference_evaluation_mode", "dense_v1"
            ),
            overlap_mode=overlap["mode"],
            overlap=overlap.get("value") if shared_overlap else None,
            diversity_overlap=None if shared_overlap else overlap.get("diversity"),
            progress_overlap=None if shared_overlap else overlap.get("progress"),
            output_overlap=None if shared_overlap else overlap.get("output"),
        )
    raise ValueError(f"Unsupported inertia policy: {policy_id!r}")
