"""Strict loader for the human-readable AFCS campaign configuration v1."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
import json
import math
from pathlib import Path
from types import MappingProxyType
from typing import Any

import numpy as np

from afcs.core import RandomnessConfig
from afcs.metrics import MetricRegistry, load_metric_registry
from afcs.optimizers.pso import (
    FixedInertia,
    LegacyCompatiblePSO,
    LegacyLinearInertia,
    LegacyPSORunConfig,
)
from afcs.problems.benchmarks.cec2017 import (
    CEC2017_DEPRECATED_FUNCTIONS,
    CEC2017_SUPPORTED_DIMENSIONS,
    CEC2017Problem,
)

from .planning import CampaignDefinition, TreatmentDefinition


class ConfigurationError(ValueError):
    """Raised when a campaign JSON violates the v1 configuration contract."""


@dataclass(frozen=True, slots=True)
class ExecutionConfig:
    parallel_workers: int = 1

    def __post_init__(self) -> None:
        _positive_integer(self.parallel_workers, "execution.parallel_workers")


@dataclass(frozen=True, slots=True)
class CampaignSummary:
    problem_instances: int
    algorithm_configurations: int
    replicas: int
    total_runs: int
    first_seed: int
    last_seed: int


@dataclass(frozen=True, slots=True)
class LoadedCampaignConfig:
    campaign: CampaignDefinition
    treatments: tuple[TreatmentDefinition, ...]
    execution: ExecutionConfig
    summary: CampaignSummary
    resolved_config: Mapping[str, Any]

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "resolved_config", MappingProxyType(dict(self.resolved_config))
        )


def load_campaign_config(
    path: str | Path,
    *,
    code_commit: str,
    metric_registry: MetricRegistry | None = None,
) -> LoadedCampaignConfig:
    config_path = Path(path)
    try:
        with config_path.open("r", encoding="utf-8") as config_file:
            raw = json.load(config_file)
    except json.JSONDecodeError as error:
        raise ConfigurationError(
            f"Invalid JSON in {config_path}: line {error.lineno}, column {error.colno}"
        ) from error
    return parse_campaign_config(
        raw,
        code_commit=code_commit,
        metric_registry=metric_registry,
    )


def parse_campaign_config(
    raw: Mapping[str, Any],
    *,
    code_commit: str,
    metric_registry: MetricRegistry | None = None,
) -> LoadedCampaignConfig:
    root = _object(raw, "root")
    _keys(
        root,
        required={
            "schema_version",
            "campaign",
            "randomness",
            "problems",
            "treatments",
            "execution",
        },
        optional={"$schema", "_documentation"},
        path="root",
    )
    if isinstance(root["schema_version"], bool) or root["schema_version"] != 1:
        raise ConfigurationError("schema_version must be exactly 1")

    campaign_raw = _object(root["campaign"], "campaign")
    _keys(
        campaign_raw,
        required={"id", "name", "replicas", "metrics"},
        optional={"notes"},
        path="campaign",
    )
    replicas = _positive_integer(campaign_raw["replicas"], "campaign.replicas")
    notes = campaign_raw.get("notes")
    if notes is not None and not isinstance(notes, str):
        raise ConfigurationError("campaign.notes must be a string or null")
    registry = metric_registry or load_metric_registry()
    try:
        registry.resolve(campaign_raw["metrics"])
    except ValueError as error:
        raise ConfigurationError(f"campaign.metrics: {error}") from error

    randomness_raw = _object(root["randomness"], "randomness")
    _keys(
        randomness_raw,
        required={"protocol", "base_seed", "engine"},
        optional=set(),
        path="randomness",
    )
    try:
        randomness = RandomnessConfig(
            base_seed=randomness_raw["base_seed"],
            protocol=randomness_raw["protocol"],
            engine=randomness_raw["engine"],
        )
    except (TypeError, ValueError) as error:
        raise ConfigurationError(f"randomness: {error}") from error

    problems = _parse_problems(root["problems"])
    treatment_specs = _parse_treatments(root["treatments"])
    execution = _parse_execution(root["execution"])

    treatments: list[TreatmentDefinition] = []
    for treatment_id, run_config, policy_factory in treatment_specs:
        for problem in problems:
            policy = policy_factory(run_config.max_iterations)
            optimizer = LegacyCompatiblePSO(
                problem=problem,
                config=run_config,
                inertia_policy=policy,
                rng=np.random.default_rng(0),
            )
            treatments.append(
                TreatmentDefinition(treatment_id, optimizer.run_metadata)
            )

    resolved = _resolved_config(
        campaign_raw=campaign_raw,
        randomness=randomness,
        problems=problems,
        treatment_specs=treatment_specs,
        execution=execution,
    )
    campaign = CampaignDefinition(
        campaign_id=_non_empty_string(campaign_raw["id"], "campaign.id"),
        name=_non_empty_string(campaign_raw["name"], "campaign.name"),
        source_config=resolved,
        code_commit=_non_empty_string(code_commit, "code_commit"),
        replicas=replicas,
        randomness=randomness,
        metric_selection=campaign_raw["metrics"],
        notes=notes,
    )
    summary = CampaignSummary(
        problem_instances=len(problems),
        algorithm_configurations=len(treatment_specs),
        replicas=replicas,
        total_runs=len(treatments) * replicas,
        first_seed=randomness.seed_for_replica(0),
        last_seed=randomness.seed_for_replica(replicas - 1),
    )
    return LoadedCampaignConfig(
        campaign=campaign,
        treatments=tuple(treatments),
        execution=execution,
        summary=summary,
        resolved_config=resolved,
    )


def _parse_problems(raw: Any) -> tuple[CEC2017Problem, ...]:
    entries = _non_empty_list(raw, "problems")
    problems: list[CEC2017Problem] = []
    seen: set[tuple[int, int]] = set()
    for index, value in enumerate(entries):
        path = f"problems[{index}]"
        entry = _object(value, path)
        _keys(
            entry,
            required={"family", "functions", "dimensions"},
            optional=set(),
            path=path,
        )
        if entry["family"] != "CEC2017":
            raise ConfigurationError(
                f"{path}.family: supported options are ['CEC2017']"
            )
        functions = _unique_integer_list(entry["functions"], f"{path}.functions")
        dimensions = _unique_integer_list(
            entry["dimensions"], f"{path}.dimensions"
        )
        for function_number in functions:
            if function_number in CEC2017_DEPRECATED_FUNCTIONS:
                raise ConfigurationError(f"{path}.functions: CEC2017 F2 is excluded")
            if function_number < 1 or function_number > 30:
                raise ConfigurationError(
                    f"{path}.functions: values must be between 1 and 30"
                )
        unsupported = set(dimensions) - set(CEC2017_SUPPORTED_DIMENSIONS)
        if unsupported:
            raise ConfigurationError(
                f"{path}.dimensions: unsupported values {sorted(unsupported)}; "
                f"options are {sorted(CEC2017_SUPPORTED_DIMENSIONS)}"
            )
        for function_number in functions:
            for dimension in dimensions:
                key = (function_number, dimension)
                if key in seen:
                    raise ConfigurationError(
                        f"Duplicate CEC2017 problem F{function_number} D{dimension}"
                    )
                seen.add(key)
                problems.append(CEC2017Problem(function_number, dimension))
    return tuple(problems)


def _parse_treatments(raw: Any):
    entries = _non_empty_list(raw, "treatments")
    parsed = []
    identifiers: set[str] = set()
    for index, value in enumerate(entries):
        path = f"treatments[{index}]"
        entry = _object(value, path)
        _keys(
            entry,
            required={"id", "optimizer", "parameters", "parameter_policy"},
            optional=set(),
            path=path,
        )
        treatment_id = _non_empty_string(entry["id"], f"{path}.id")
        if treatment_id in identifiers:
            raise ConfigurationError(f"Duplicate treatment id: {treatment_id!r}")
        identifiers.add(treatment_id)
        if entry["optimizer"] != "PSO":
            raise ConfigurationError(
                f"{path}.optimizer: supported options are ['PSO']"
            )
        parameters = _object(entry["parameters"], f"{path}.parameters")
        _keys(
            parameters,
            required={"population_size", "max_iterations"},
            optional={"cognitive", "social", "velocity_factor"},
            path=f"{path}.parameters",
        )
        try:
            run_config = LegacyPSORunConfig(
                population_size=parameters["population_size"],
                max_iterations=parameters["max_iterations"],
                cognitive=parameters.get("cognitive", 2.0),
                social=parameters.get("social", 2.0),
                velocity_factor=parameters.get("velocity_factor", 0.1),
            )
        except (TypeError, ValueError) as error:
            raise ConfigurationError(f"{path}.parameters: {error}") from error
        policy_factory = _parse_policy(
            entry["parameter_policy"], f"{path}.parameter_policy"
        )
        parsed.append((treatment_id, run_config, policy_factory))
    return tuple(parsed)


def _parse_policy(raw: Any, path: str):
    policy = _object(raw, path)
    _keys(policy, required={"id", "parameters"}, optional=set(), path=path)
    parameters = _object(policy["parameters"], f"{path}.parameters")
    if policy["id"] == "fixed_inertia":
        _keys(
            parameters,
            required={"value"},
            optional=set(),
            path=f"{path}.parameters",
        )
        try:
            value = FixedInertia(parameters["value"]).value
        except (TypeError, ValueError) as error:
            raise ConfigurationError(f"{path}.parameters: {error}") from error
        return lambda _max_iterations: FixedInertia(value)
    if policy["id"] == "legacy_ldiw":
        _keys(
            parameters,
            required=set(),
            optional={"maximum", "minimum"},
            path=f"{path}.parameters",
        )
        maximum = _finite_number(parameters.get("maximum", 0.9), f"{path}.maximum")
        minimum = _finite_number(parameters.get("minimum", 0.1), f"{path}.minimum")
        try:
            LegacyLinearInertia(1, maximum=maximum, minimum=minimum)
        except (TypeError, ValueError) as error:
            raise ConfigurationError(f"{path}.parameters: {error}") from error
        return lambda max_iterations: LegacyLinearInertia(
            max_iterations, maximum=maximum, minimum=minimum
        )
    raise ConfigurationError(
        f"{path}.id: supported options are ['fixed_inertia', 'legacy_ldiw']"
    )


def _parse_execution(raw: Any) -> ExecutionConfig:
    execution = _object(raw, "execution")
    _keys(
        execution,
        required=set(),
        optional={"parallel_workers"},
        path="execution",
    )
    try:
        return ExecutionConfig(execution.get("parallel_workers", 1))
    except (TypeError, ValueError) as error:
        raise ConfigurationError(str(error)) from error


def _resolved_config(**parts: Any) -> dict[str, Any]:
    campaign_raw = parts["campaign_raw"]
    randomness = parts["randomness"]
    problems = parts["problems"]
    treatment_specs = parts["treatment_specs"]
    execution = parts["execution"]
    problem_groups: dict[int, list[int]] = {}
    for problem in problems:
        problem_groups.setdefault(problem.function_number, []).append(
            problem.metadata.dimension
        )
    treatments = []
    for treatment_id, config, policy_factory in treatment_specs:
        policy = policy_factory(config.max_iterations)
        treatments.append(
            {
                "id": treatment_id,
                "optimizer": "PSO",
                "parameters": {
                    "population_size": config.population_size,
                    "max_iterations": config.max_iterations,
                    "cognitive": config.cognitive,
                    "social": config.social,
                    "velocity_factor": config.velocity_factor,
                },
                "parameter_policy": {
                    "id": policy.policy_id,
                    "parameters": dict(policy.configuration),
                },
            }
        )
    return {
        "schema_version": 1,
        "campaign": dict(campaign_raw),
        "randomness": {
            "protocol": randomness.protocol,
            "base_seed": randomness.base_seed,
            "engine": randomness.engine,
        },
        "problems": [
            {
                "family": "CEC2017",
                "functions": [function_number],
                "dimensions": sorted(dimensions),
            }
            for function_number, dimensions in sorted(problem_groups.items())
        ],
        "treatments": treatments,
        "execution": {"parallel_workers": execution.parallel_workers},
    }


def _object(value: Any, path: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ConfigurationError(f"{path} must be an object")
    return value


def _keys(
    value: Mapping[str, Any],
    *,
    required: set[str],
    optional: set[str],
    path: str,
) -> None:
    missing = required - set(value)
    unknown = set(value) - required - optional
    if missing or unknown:
        raise ConfigurationError(
            f"{path}: missing={sorted(missing)}, unknown={sorted(unknown)}"
        )


def _non_empty_list(value: Any, path: str) -> list[Any]:
    if not isinstance(value, list) or not value:
        raise ConfigurationError(f"{path} must be a non-empty list")
    return value


def _unique_integer_list(value: Any, path: str) -> tuple[int, ...]:
    values = _non_empty_list(value, path)
    if any(isinstance(item, bool) or not isinstance(item, int) for item in values):
        raise ConfigurationError(f"{path} must contain only integers")
    if len(values) != len(set(values)):
        raise ConfigurationError(f"{path} contains duplicates")
    return tuple(values)


def _positive_integer(value: Any, path: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ConfigurationError(f"{path} must be an integer")
    if value <= 0:
        raise ConfigurationError(f"{path} must be positive")
    return value


def _finite_number(value: Any, path: str) -> float:
    if isinstance(value, bool):
        raise ConfigurationError(f"{path} must be numeric")
    try:
        normalized = float(value)
    except (TypeError, ValueError) as error:
        raise ConfigurationError(f"{path} must be numeric") from error
    if not math.isfinite(normalized):
        raise ConfigurationError(f"{path} must be finite")
    return normalized


def _non_empty_string(value: Any, path: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ConfigurationError(f"{path} must be a non-empty string")
    return value
