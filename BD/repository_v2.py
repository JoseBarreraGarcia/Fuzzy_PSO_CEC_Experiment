"""Transactional repository for the prepared v2 experiment schema."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import math
import sqlite3
from typing import Any

from BD.persistence_v2 import configure_campaign_metrics, sync_metric_definitions
from Util.metrics_registry import MetricRegistry


class RepositoryError(RuntimeError):
    """Raised when an operation violates the v2 experiment lifecycle."""


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


@dataclass(frozen=True)
class StoredValue:
    value_real: float | None = None
    value_integer: int | None = None
    value_text: str | None = None
    value_json: str | None = None


def encode_metric_value(value: Any, dtype: str | None = None) -> StoredValue:
    """Encode one Python value into exactly one SQLite value column."""

    if dtype == "float":
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise RepositoryError("Expected a numeric metric value")
        numeric_value = float(value)
        if not math.isfinite(numeric_value):
            raise RepositoryError("Metric values must be finite")
        return StoredValue(value_real=numeric_value)
    if dtype == "integer":
        if isinstance(value, bool) or not isinstance(value, int):
            raise RepositoryError("Expected an integer metric value")
        return StoredValue(value_integer=value)
    if dtype == "boolean":
        if not isinstance(value, bool):
            raise RepositoryError("Expected a boolean metric value")
        return StoredValue(value_integer=int(value))
    if dtype == "string":
        if not isinstance(value, str):
            raise RepositoryError("Expected a string metric value")
        return StoredValue(value_text=value)
    if dtype == "json":
        if not isinstance(value, (dict, list, tuple)):
            raise RepositoryError("Expected an object or list metric value")
        return StoredValue(value_json=canonical_json(value))
    if dtype is not None:
        raise RepositoryError(f"Unsupported registered metric dtype: {dtype}")

    if isinstance(value, bool):
        return StoredValue(value_integer=int(value))
    if isinstance(value, int):
        return StoredValue(value_integer=value)
    if isinstance(value, float):
        if not math.isfinite(value):
            raise RepositoryError("Metric values must be finite")
        return StoredValue(value_real=value)
    if isinstance(value, str):
        return StoredValue(value_text=value)
    if isinstance(value, (dict, list, tuple)):
        return StoredValue(value_json=canonical_json(value))
    raise RepositoryError(f"Unsupported metric value type: {type(value).__name__}")


class ExperimentRepository:
    def __init__(self, connection: sqlite3.Connection, registry: MetricRegistry):
        self.connection = connection
        self.registry = registry

    def create_campaign(
        self,
        campaign_id: str,
        name: str,
        config: Mapping[str, Any],
        code_commit: str,
        metric_selection: object = "minimal",
        created_at: str | None = None,
        notes: str | None = None,
    ) -> tuple[str, ...]:
        config_payload = canonical_json(config)
        timestamp = created_at or utc_now()
        with self.connection:
            self.connection.execute(
                """
                INSERT INTO campaigns (
                    campaign_id, name, config_json, config_sha256, code_commit,
                    metric_registry_version, schema_version, created_at, notes
                ) VALUES (?, ?, ?, ?, ?, ?, 1, ?, ?)
                """,
                (
                    campaign_id,
                    name,
                    config_payload,
                    sha256_text(config_payload),
                    code_commit,
                    self.registry.schema_version,
                    timestamp,
                    notes,
                ),
            )
            sync_metric_definitions(self.connection, self.registry)
            return configure_campaign_metrics(
                self.connection, campaign_id, self.registry, metric_selection
            )

    def add_problem_instance(
        self,
        problem_family: str,
        name: str,
        dimension: int | None,
        optimum: float | None = None,
        direction: str = "minimize",
        parameters: Mapping[str, Any] | None = None,
        data_sha256: str | None = None,
    ) -> int:
        parameters_json = canonical_json(parameters or {})
        with self.connection:
            existing = self.connection.execute(
                """
                SELECT instance_id FROM problem_instances
                WHERE problem_family = ? AND name = ? AND dimension IS ?
                  AND parameters_json = ?
                """,
                (problem_family, name, dimension, parameters_json),
            ).fetchone()
            if existing is not None:
                return int(existing["instance_id"])
            cursor = self.connection.execute(
                """
                INSERT INTO problem_instances (
                    problem_family, name, dimension, optimum, direction,
                    parameters_json, data_sha256
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    problem_family,
                    name,
                    dimension,
                    optimum,
                    direction,
                    parameters_json,
                    data_sha256,
                ),
            )
            return int(cursor.lastrowid)

    def add_algorithm_configuration(
        self,
        configuration_id: str,
        campaign_id: str,
        algorithm: str,
        parameters: Mapping[str, Any],
        budget_type: str,
        budget_evaluations: int | None = None,
        budget_iterations: int | None = None,
        population_size: int | None = None,
        created_at: str | None = None,
    ) -> None:
        self._require_campaign_status(campaign_id, "draft")
        parameters_json = canonical_json(parameters)
        with self.connection:
            self.connection.execute(
                """
                INSERT INTO algorithm_configurations (
                    configuration_id, campaign_id, algorithm, parameters_json,
                    parameters_sha256, budget_type, budget_evaluations,
                    budget_iterations, population_size, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    configuration_id,
                    campaign_id,
                    algorithm,
                    parameters_json,
                    sha256_text(parameters_json),
                    budget_type,
                    budget_evaluations,
                    budget_iterations,
                    population_size,
                    created_at or utc_now(),
                ),
            )

    def plan_run(
        self,
        campaign_id: str,
        configuration_id: str,
        instance_id: int,
        replica_index: int,
        random_seed: int | None = None,
    ) -> int:
        self._require_campaign_status(campaign_id, "draft")
        with self.connection:
            cursor = self.connection.execute(
                """
                INSERT INTO runs (
                    campaign_id, configuration_id, instance_id,
                    replica_index, random_seed, status
                ) VALUES (?, ?, ?, ?, ?, 'planned')
                """,
                (
                    campaign_id,
                    configuration_id,
                    instance_id,
                    replica_index,
                    random_seed,
                ),
            )
            return int(cursor.lastrowid)

    def start_campaign(self, campaign_id: str, started_at: str | None = None) -> None:
        self._require_campaign_status(campaign_id, "draft")
        run_count = self.connection.execute(
            "SELECT COUNT(*) FROM runs WHERE campaign_id = ?", (campaign_id,)
        ).fetchone()[0]
        if run_count == 0:
            raise RepositoryError("A campaign cannot start without planned runs")
        with self.connection:
            self.connection.execute(
                "UPDATE campaigns SET status = 'running', started_at = ? WHERE campaign_id = ?",
                (started_at or utc_now(), campaign_id),
            )

    def start_run(self, run_id: int, started_at: str | None = None) -> None:
        row = self._get_run(run_id)
        self._require_campaign_status(row["campaign_id"], "running")
        if row["status"] != "planned":
            raise RepositoryError(f"Run {run_id} is not planned")
        with self.connection:
            self.connection.execute(
                "UPDATE runs SET status = 'running', started_at = ? WHERE run_id = ?",
                (started_at or utc_now(), run_id),
            )

    def record_trace(
        self,
        run_id: int,
        checkpoint_index: int,
        iteration_index: int | None,
        evaluations: int,
        metrics: Mapping[str, Any],
        elapsed_seconds: float | None = None,
        provenance: str = "observed",
    ) -> None:
        row = self._get_run(run_id)
        if row["status"] != "running":
            raise RepositoryError("Trace metrics can only be recorded for a running run")
        self._validate_selected_metrics(row["campaign_id"], metrics, "iteration")

        previous = self.connection.execute(
            """
            SELECT checkpoint_index, evaluations
            FROM trace_points WHERE run_id = ?
            ORDER BY checkpoint_index DESC LIMIT 1
            """,
            (run_id,),
        ).fetchone()
        if previous is not None and (
            checkpoint_index <= previous["checkpoint_index"]
            or evaluations < previous["evaluations"]
        ):
            raise RepositoryError("Trace checkpoints and evaluations must be monotonic")

        with self.connection:
            self.connection.execute(
                """
                INSERT INTO trace_points (
                    run_id, checkpoint_index, iteration_index,
                    evaluations, elapsed_seconds
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (run_id, checkpoint_index, iteration_index, evaluations, elapsed_seconds),
            )
            for metric_id, value in metrics.items():
                self._insert_trace_metric(
                    run_id, checkpoint_index, metric_id, value, provenance
                )

    def complete_run(
        self,
        run_id: int,
        objective_best: float,
        solution: Any,
        evaluations: int,
        runtime_total_seconds: float,
        feasible: bool | None = None,
        constraint_violation: float | None = None,
        metrics: Mapping[str, Any] | None = None,
        finished_at: str | None = None,
    ) -> None:
        row = self._get_run(run_id)
        if row["status"] != "running":
            raise RepositoryError(f"Run {run_id} is not running")
        if not math.isfinite(objective_best):
            raise RepositoryError("Completed objective_best must be finite")
        selected_metrics = metrics or {}
        self._validate_selected_metrics(row["campaign_id"], selected_metrics, "replica")

        with self.connection:
            self.connection.execute(
                """
                UPDATE runs
                SET status = 'completed', finished_at = ?, objective_best = ?,
                    solution_json = ?, evaluations = ?, runtime_total_seconds = ?,
                    feasible = ?, constraint_violation = ?
                WHERE run_id = ?
                """,
                (
                    finished_at or utc_now(),
                    objective_best,
                    canonical_json(solution),
                    evaluations,
                    runtime_total_seconds,
                    None if feasible is None else int(feasible),
                    constraint_violation,
                    run_id,
                ),
            )
            for metric_id, value in selected_metrics.items():
                self._insert_run_metric(run_id, metric_id, value, "observed")

    def fail_run(
        self,
        run_id: int,
        error_type: str,
        error_message: str,
        finished_at: str | None = None,
    ) -> None:
        row = self._get_run(run_id)
        if row["status"] not in {"planned", "running"}:
            raise RepositoryError(f"Run {run_id} cannot transition to failed")
        with self.connection:
            self.connection.execute(
                """
                UPDATE runs
                SET status = 'failed', finished_at = ?, error_type = ?, error_message = ?
                WHERE run_id = ?
                """,
                (finished_at or utc_now(), error_type, error_message, run_id),
            )

    def finish_campaign(self, campaign_id: str, finished_at: str | None = None) -> None:
        self._require_campaign_status(campaign_id, "running")
        pending = self.connection.execute(
            """
            SELECT COUNT(*) FROM runs
            WHERE campaign_id = ? AND status NOT IN ('completed', 'failed', 'cancelled')
            """,
            (campaign_id,),
        ).fetchone()[0]
        if pending:
            raise RepositoryError("Campaign still has non-terminal runs")
        with self.connection:
            self.connection.execute(
                "UPDATE campaigns SET status = 'completed', finished_at = ? WHERE campaign_id = ?",
                (finished_at or utc_now(), campaign_id),
            )

    def seal_campaign(self, campaign_id: str, sealed_at: str | None = None) -> None:
        self._require_campaign_status(campaign_id, "completed")
        with self.connection:
            self.connection.execute(
                "UPDATE campaigns SET status = 'sealed', sealed_at = ? WHERE campaign_id = ?",
                (sealed_at or utc_now(), campaign_id),
            )

    def _get_run(self, run_id: int) -> sqlite3.Row:
        row = self.connection.execute(
            "SELECT * FROM runs WHERE run_id = ?", (run_id,)
        ).fetchone()
        if row is None:
            raise RepositoryError(f"Unknown run: {run_id}")
        return row

    def _require_campaign_status(self, campaign_id: str, expected: str) -> None:
        row = self.connection.execute(
            "SELECT status FROM campaigns WHERE campaign_id = ?", (campaign_id,)
        ).fetchone()
        if row is None:
            raise RepositoryError(f"Unknown campaign: {campaign_id!r}")
        if row["status"] != expected:
            raise RepositoryError(
                f"Campaign {campaign_id!r} must be {expected!r}, got {row['status']!r}"
            )

    def _validate_selected_metrics(
        self, campaign_id: str, metrics: Mapping[str, Any], scope: str
    ) -> None:
        if not metrics:
            return
        selected = {
            row["metric_id"]
            for row in self.connection.execute(
                "SELECT metric_id FROM campaign_metrics WHERE campaign_id = ?",
                (campaign_id,),
            )
        }
        unknown = set(metrics) - selected
        if unknown:
            raise RepositoryError(
                "Metrics were not selected for this campaign: "
                + ", ".join(sorted(unknown))
            )
        invalid_scope = {
            metric_id
            for metric_id in metrics
            if scope not in self.registry.metrics[metric_id].scope
        }
        if invalid_scope:
            raise RepositoryError(
                f"Metrics do not support {scope!r} scope: "
                + ", ".join(sorted(invalid_scope))
            )

    def _metric_version(self, metric_id: str) -> int:
        try:
            return self.registry.metrics[metric_id].version
        except KeyError as error:
            raise RepositoryError(f"Unknown metric: {metric_id}") from error

    def _insert_run_metric(
        self, run_id: int, metric_id: str, value: Any, provenance: str
    ) -> None:
        definition = self.registry.metrics[metric_id]
        encoded = encode_metric_value(value, definition.dtype)
        self.connection.execute(
            """
            INSERT INTO run_metric_values (
                run_id, metric_id, metric_version, provenance,
                value_real, value_integer, value_text, value_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                metric_id,
                self._metric_version(metric_id),
                provenance,
                encoded.value_real,
                encoded.value_integer,
                encoded.value_text,
                encoded.value_json,
            ),
        )

    def _insert_trace_metric(
        self,
        run_id: int,
        checkpoint_index: int,
        metric_id: str,
        value: Any,
        provenance: str,
    ) -> None:
        definition = self.registry.metrics[metric_id]
        encoded = encode_metric_value(value, definition.dtype)
        self.connection.execute(
            """
            INSERT INTO trace_metric_values (
                run_id, checkpoint_index, metric_id, metric_version,
                provenance, value_real, value_integer, value_text, value_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                checkpoint_index,
                metric_id,
                self._metric_version(metric_id),
                provenance,
                encoded.value_real,
                encoded.value_integer,
                encoded.value_text,
                encoded.value_json,
            ),
        )
