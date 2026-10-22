"""Validated expansion and atomic persistence of experiment campaigns."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any

from afcs.optimizers import OptimizerRunMetadata
from afcs.persistence import ExperimentRepository, canonical_json
from afcs.core import RandomnessConfig


@dataclass(frozen=True, slots=True)
class CampaignDefinition:
    """Human-level campaign attributes that are not optimizer-specific."""

    campaign_id: str
    name: str
    source_config: Mapping[str, Any]
    code_commit: str
    replicas: int
    randomness: RandomnessConfig = RandomnessConfig()
    metric_selection: object = "minimal"
    notes: str | None = None

    def __post_init__(self) -> None:
        for name, value in (
            ("campaign_id", self.campaign_id),
            ("name", self.name),
            ("code_commit", self.code_commit),
        ):
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string")
        if not isinstance(self.source_config, Mapping):
            raise TypeError("source_config must be a mapping")
        if isinstance(self.replicas, bool) or not isinstance(self.replicas, int):
            raise TypeError("replicas must be an integer")
        if self.replicas <= 0:
            raise ValueError("replicas must be positive")
        if not isinstance(self.randomness, RandomnessConfig):
            raise TypeError("randomness must be RandomnessConfig")
        object.__setattr__(
            self, "source_config", MappingProxyType(dict(self.source_config))
        )


@dataclass(frozen=True, slots=True)
class TreatmentDefinition:
    """One algorithm configuration applied to one problem instance."""

    configuration_id: str
    run_metadata: OptimizerRunMetadata

    def __post_init__(self) -> None:
        if not isinstance(self.configuration_id, str) or not self.configuration_id.strip():
            raise ValueError("configuration_id must be a non-empty string")
        if not isinstance(self.run_metadata, OptimizerRunMetadata):
            raise TypeError("run_metadata must be OptimizerRunMetadata")


@dataclass(frozen=True, slots=True)
class PersistedCampaignPlan:
    campaign_id: str
    configuration_ids: tuple[str, ...]
    instance_ids: tuple[int, ...]
    run_ids: tuple[int, ...]


class CampaignPlanner:
    """Validate a compact campaign and persist its expanded run matrix."""

    def __init__(self, repository: ExperimentRepository) -> None:
        if not isinstance(repository, ExperimentRepository):
            raise TypeError("repository must be ExperimentRepository")
        self._repository = repository

    def persist(
        self,
        campaign: CampaignDefinition,
        treatments: Sequence[TreatmentDefinition],
    ) -> PersistedCampaignPlan:
        if not isinstance(campaign, CampaignDefinition):
            raise TypeError("campaign must be CampaignDefinition")
        normalized = tuple(treatments)
        self._validate_treatments(normalized)

        configuration_metadata: dict[str, OptimizerRunMetadata] = {}
        problem_ids: dict[str, int] = {}
        run_ids: list[int] = []

        with self._repository.transaction():
            self._repository.create_campaign(
                campaign_id=campaign.campaign_id,
                name=campaign.name,
                config=dict(campaign.source_config),
                code_commit=campaign.code_commit,
                metric_selection=campaign.metric_selection,
                notes=campaign.notes,
                base_seed=campaign.randomness.base_seed,
                seed_protocol=campaign.randomness.protocol,
                rng_engine=campaign.randomness.engine,
            )
            for treatment in normalized:
                metadata = treatment.run_metadata
                problem_key = _problem_key(metadata)
                if problem_key not in problem_ids:
                    parameters = dict(metadata.problem.parameters)
                    data_sha256 = parameters.pop("data_sha256", None)
                    problem_ids[problem_key] = self._repository.add_problem_instance(
                        problem_family=metadata.problem.family,
                        name=metadata.problem.problem_id,
                        dimension=metadata.problem.dimension,
                        optimum=metadata.problem.known_optimum,
                        direction=metadata.problem.direction.value,
                        parameters=parameters,
                        data_sha256=data_sha256,
                    )
                if treatment.configuration_id not in configuration_metadata:
                    configuration_metadata[treatment.configuration_id] = metadata
                    self._repository.add_algorithm_configuration(
                        configuration_id=treatment.configuration_id,
                        campaign_id=campaign.campaign_id,
                        algorithm=metadata.optimizer.optimizer_id,
                        parameters=dict(metadata.parameters),
                        budget_type=(
                            "hybrid"
                            if metadata.iteration_budget is not None
                            else "evaluations"
                        ),
                        budget_evaluations=metadata.evaluation_budget,
                        budget_iterations=metadata.iteration_budget,
                        population_size=metadata.population_size,
                    )
                for replica_index in range(campaign.replicas):
                    run_ids.append(
                        self._repository.plan_run(
                            campaign_id=campaign.campaign_id,
                            configuration_id=treatment.configuration_id,
                            instance_id=problem_ids[problem_key],
                            replica_index=replica_index,
                            random_seed=campaign.randomness.seed_for_replica(
                                replica_index
                            ),
                        )
                    )

        return PersistedCampaignPlan(
            campaign_id=campaign.campaign_id,
            configuration_ids=tuple(configuration_metadata),
            instance_ids=tuple(problem_ids.values()),
            run_ids=tuple(run_ids),
        )

    @staticmethod
    def _validate_treatments(
        treatments: tuple[TreatmentDefinition, ...],
    ) -> None:
        if not treatments:
            raise ValueError("A campaign must contain at least one treatment")
        configurations: dict[str, str] = {}
        combinations: set[tuple[str, str]] = set()
        for treatment in treatments:
            if not isinstance(treatment, TreatmentDefinition):
                raise TypeError("treatments must contain TreatmentDefinition values")
            metadata = treatment.run_metadata
            signature = _configuration_signature(metadata)
            previous = configurations.setdefault(treatment.configuration_id, signature)
            if previous != signature:
                raise ValueError(
                    f"Configuration {treatment.configuration_id!r} has conflicting definitions"
                )
            combination = (treatment.configuration_id, _problem_key(metadata))
            if combination in combinations:
                raise ValueError(
                    "Duplicate treatment for configuration and problem instance"
                )
            combinations.add(combination)


def _configuration_signature(metadata: OptimizerRunMetadata) -> str:
    return canonical_json(
        {
            "optimizer_id": metadata.optimizer.optimizer_id,
            "optimizer_version": metadata.optimizer.version,
            "parameters": dict(metadata.parameters),
            "evaluation_budget": metadata.evaluation_budget,
            "iteration_budget": metadata.iteration_budget,
            "population_size": metadata.population_size,
        }
    )


def _problem_key(metadata: OptimizerRunMetadata) -> str:
    problem = metadata.problem
    return canonical_json(
        {
            "family": problem.family,
            "problem_id": problem.problem_id,
            "dimension": problem.dimension,
            "direction": problem.direction.value,
            "known_optimum": problem.known_optimum,
            "parameters": dict(problem.parameters),
        }
    )
