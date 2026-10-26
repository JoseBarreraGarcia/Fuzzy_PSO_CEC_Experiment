"""Resumable sequential or process-parallel experiment orchestration."""

from __future__ import annotations

from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path

from afcs.metrics import load_metric_registry
from afcs.persistence import (
    ExperimentRepository,
    RepositoryError,
    connect_v2_database,
)

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


class CampaignOrchestrator:
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
        self._parallel_safe_defaults = (
            optimizer_factory is None and run_executor is None
        )

    def plan(self, loaded: LoadedCampaignConfig) -> PersistedCampaignPlan:
        if not isinstance(loaded, LoadedCampaignConfig):
            raise TypeError("loaded must be LoadedCampaignConfig")
        return CampaignPlanner(self._repository).persist(
            loaded.campaign, loaded.treatments
        )

    def plan_and_execute(
        self, loaded: LoadedCampaignConfig
    ) -> CampaignExecutionSummary:
        plan = self.plan(loaded)
        return self.execute_pending(
            plan.campaign_id, parallel_workers=loaded.execution.parallel_workers
        )

    def execute_pending(
        self, campaign_id: str, parallel_workers: int | None = None
    ) -> CampaignExecutionSummary:
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

        workers = (
            self._configured_workers(campaign_id)
            if parallel_workers is None
            else parallel_workers
        )
        if isinstance(workers, bool) or not isinstance(workers, int) or workers < 1:
            raise ValueError("parallel_workers must be a positive integer")
        pending = self._repository.run_ids_by_status(campaign_id, "planned")
        if workers == 1:
            executed = self._execute_sequential(campaign_id, pending)
        else:
            executed = self._execute_parallel(campaign_id, pending, workers)

        if not self._repository.run_ids_by_status(campaign_id, "planned"):
            self._repository.finish_campaign(campaign_id)
        return self._summary(campaign_id, executed_now=executed)

    def _execute_sequential(self, campaign_id: str, run_ids: tuple[int, ...]) -> int:
        executed = 0
        selected_metrics = self._repository.selected_metric_ids(campaign_id)
        for run_id in run_ids:
            plan = self._repository.get_planned_run(run_id)
            optimizer = self._factory.build(plan, selected_metrics=selected_metrics)
            self._executor.execute(run_id, optimizer)
            executed += 1
        return executed

    def _execute_parallel(
        self, campaign_id: str, run_ids: tuple[int, ...], workers: int
    ) -> int:
        if not run_ids:
            return 0
        if not self._parallel_safe_defaults:
            raise ValueError(
                "Parallel execution does not accept process-local factory/executor overrides"
            )
        database_path = self._repository.database_path
        errors: list[Exception] = []
        completed = 0
        effective_workers = min(workers, len(run_ids))
        with ProcessPoolExecutor(max_workers=effective_workers) as pool:
            futures = {
                pool.submit(
                    _execute_persisted_run, database_path, campaign_id, run_id
                ): run_id
                for run_id in run_ids
            }
            for future in as_completed(futures):
                try:
                    future.result()
                    completed += 1
                except Exception as error:
                    errors.append(error)
        if errors:
            raise RuntimeError(
                f"{len(errors)} parallel run(s) failed; inspect persisted run errors"
            ) from errors[0]
        return completed

    def _configured_workers(self, campaign_id: str) -> int:
        config = self._repository.campaign_config(campaign_id)
        execution = config.get("execution", {})
        return int(execution.get("parallel_workers", 1))

    def recover_interrupted(
        self, campaign_id: str, run_ids: tuple[int, ...], reason: str
    ) -> CampaignExecutionSummary:
        """Explicitly abandon active attempts and requeue their logical runs."""

        if not run_ids:
            raise ValueError("At least one run_id is required for recovery")
        if len(run_ids) != len(set(run_ids)):
            raise ValueError("Recovery run_ids must be unique")
        with self._repository.transaction():
            for run_id in run_ids:
                self._repository.recover_interrupted_run(
                    campaign_id=campaign_id,
                    run_id=run_id,
                    reason=reason,
                )
        return self._summary(campaign_id, executed_now=0)

    def cancel_runs(
        self, campaign_id: str, run_ids: tuple[int, ...], reason: str
    ) -> CampaignExecutionSummary:
        """Cancel selected logical replicas atomically without automatic retry."""

        if not run_ids:
            raise ValueError("At least one run_id is required for cancellation")
        if len(run_ids) != len(set(run_ids)):
            raise ValueError("Cancellation run_ids must be unique")
        if not isinstance(reason, str) or not reason.strip():
            raise ValueError("Cancellation reason must be a non-empty string")
        with self._repository.transaction():
            for run_id in run_ids:
                self._repository.cancel_run(campaign_id, run_id, reason)
        return self._summary(campaign_id, executed_now=0)

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


def _execute_persisted_run(
    database_path: Path, campaign_id: str, run_id: int
) -> None:
    """Process-safe worker entry point; all mutable state is worker-local."""

    connection = connect_v2_database(database_path)
    try:
        repository = ExperimentRepository(connection, load_metric_registry())
        plan = repository.get_planned_run(run_id)
        optimizer = OptimizerFactory().build(
            plan,
            selected_metrics=repository.selected_metric_ids(campaign_id),
        )
        ExperimentRunExecutor(repository).execute(run_id, optimizer)
    finally:
        connection.close()


# Compatibility name retained while callers migrate to the general API.
SequentialCampaignOrchestrator = CampaignOrchestrator
