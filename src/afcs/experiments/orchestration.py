"""Sequential, resumable orchestration of persisted experiment campaigns."""

from __future__ import annotations

from dataclasses import dataclass

from afcs.persistence import ExperimentRepository, RepositoryError

from .configuration import LoadedCampaignConfig
from .factory import OptimizerFactory
from .planning import CampaignPlanner, PersistedCampaignPlan
from .runner import ExperimentRunExecutor


class CampaignRecoveryRequired(RuntimeError):
    """Raised when a previous process left a run in the running state."""


@dataclass(frozen=True, slots=True)
class CampaignExecutionSummary:
    campaign_id: str
    executed_now: int
    planned: int
    running: int
    completed: int
    failed: int
    cancelled: int
    campaign_status: str


class SequentialCampaignOrchestrator:
    """Plan and execute campaigns using SQLite as the canonical work queue.

    Re-entry executes only rows still marked ``planned``. Failed rows remain
    immutable evidence and are not retried automatically. A stale ``running``
    row requires an explicit recovery policy and is therefore never reset
    silently.
    """

    def __init__(
        self,
        repository: ExperimentRepository,
        optimizer_factory: OptimizerFactory | None = None,
        run_executor: ExperimentRunExecutor | None = None,
    ) -> None:
        if not isinstance(repository, ExperimentRepository):
            raise TypeError("repository must be ExperimentRepository")
        self._repository = repository
        self._factory = optimizer_factory or OptimizerFactory()
        self._executor = run_executor or ExperimentRunExecutor(repository)

    def plan(self, loaded: LoadedCampaignConfig) -> PersistedCampaignPlan:
        if not isinstance(loaded, LoadedCampaignConfig):
            raise TypeError("loaded must be LoadedCampaignConfig")
        if loaded.execution.parallel_workers != 1:
            raise ValueError("Sequential orchestrator requires parallel_workers=1")
        return CampaignPlanner(self._repository).persist(
            loaded.campaign, loaded.treatments
        )

    def plan_and_execute(
        self, loaded: LoadedCampaignConfig
    ) -> CampaignExecutionSummary:
        plan = self.plan(loaded)
        return self.execute_pending(plan.campaign_id)

    def execute_pending(self, campaign_id: str) -> CampaignExecutionSummary:
        status = self._repository.campaign_status(campaign_id)
        if status == "draft":
            self._repository.start_campaign(campaign_id)
        elif status in {"completed", "sealed"}:
            return self._summary(campaign_id, executed_now=0)
        elif status != "running":
            raise RepositoryError(
                f"Campaign {campaign_id!r} cannot execute from status {status!r}"
            )

        stale = self._repository.run_ids_by_status(campaign_id, "running")
        if stale:
            raise CampaignRecoveryRequired(
                "Campaign contains runs left in 'running' state; an explicit "
                f"recovery decision is required for run_ids={list(stale)}"
            )

        executed = 0
        for run_id in self._repository.run_ids_by_status(campaign_id, "planned"):
            plan = self._repository.get_planned_run(run_id)
            optimizer = self._factory.build(plan)
            self._executor.execute(run_id, optimizer)
            executed += 1

        if not self._repository.run_ids_by_status(campaign_id, "planned"):
            self._repository.finish_campaign(campaign_id)
        return self._summary(campaign_id, executed_now=executed)

    def _summary(
        self, campaign_id: str, *, executed_now: int
    ) -> CampaignExecutionSummary:
        counts = {
            status: len(self._repository.run_ids_by_status(campaign_id, status))
            for status in (
                "planned",
                "running",
                "completed",
                "failed",
                "cancelled",
            )
        }
        return CampaignExecutionSummary(
            campaign_id=campaign_id,
            executed_now=executed_now,
            campaign_status=self._repository.campaign_status(campaign_id),
            **counts,
        )
