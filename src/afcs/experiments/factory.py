"""Build executable optimizers from the canonical persisted run plan."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from types import MappingProxyType

from afcs.core import ReplicaRandomStreams
from afcs.optimizers.pso import (
    FixedInertia,
    LegacyCompatiblePSO,
    LegacyLinearInertia,
    LegacyPSORunConfig,
)
from afcs.persistence import PlannedRun
from afcs.problems.benchmarks.cec2017 import CEC2017Problem

from .contracts import RunnableOptimizer


OptimizerBuilder = Callable[[PlannedRun], RunnableOptimizer]
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

    def build(self, plan: PlannedRun) -> RunnableOptimizer:
        if not isinstance(plan, PlannedRun):
            raise TypeError("plan must be PlannedRun")
        try:
            builder = self._builders[plan.algorithm]
        except KeyError as error:
            raise ValueError(
                f"Unsupported persisted optimizer {plan.algorithm!r}; "
                f"available={list(self._builders)}"
            ) from error
        optimizer = builder(plan)
        if not isinstance(optimizer, RunnableOptimizer):
            raise TypeError("optimizer builder must return RunnableOptimizer")
        return optimizer


def _build_pso(plan: PlannedRun) -> LegacyCompatiblePSO:
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
    return LegacyCompatiblePSO(
        problem=problem,
        config=config,
        inertia_policy=policy,
        random_streams=streams,
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
    raise ValueError(f"Unsupported inertia policy: {policy_id!r}")
