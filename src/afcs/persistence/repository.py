"""Transactional repository for the prepared v2 experiment schema."""

from __future__ import annotations

import hashlib
import json
import math
import sqlite3
from collections.abc import Mapping
from contextlib import contextmanager, nullcontext
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from afcs.core.randomness import MAX_SEED
from afcs.core.serialization import freeze_json_mapping, json_value
from afcs.metrics import MetricRegistry
from afcs.persistence.database import (
    configure_campaign_metrics,
    current_schema_version,
    sync_metric_definitions,
    validate_current_schema,
)
from afcs.persistence.metric_contracts import (
    MetricContractError,
    SelectedMetric,
    metric_evidence_issues,
    required_value_ids,
    selected_metric_contract,
)
from afcs.persistence.run_contracts import (
    POST_RUN_TIMING_METRICS,
    run_evidence_issues,
    trace_result_issues,
    valid_solution,
)


class RepositoryError(RuntimeError):
    """Raised when an operation violates the v2 experiment lifecycle."""


def canonical_json(value: Any) -> str:
    return json.dumps(
        json_value(value),
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    )


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


@dataclass(frozen=True, slots=True)
class PlannedRun:
    """Read-only execution plan assembled from normalized SQLite records."""

    run_id: int
    status: str
    campaign_config: Mapping[str, Any]
    algorithm: str
    optimizer_version: str | None
    algorithm_parameters: Mapping[str, Any]
    budget_evaluations: int | None
    budget_iterations: int | None
    population_size: int | None
    problem_family: str
    problem_name: str
    dimension: int | None
    optimum: float | None
    direction: str
    problem_parameters: Mapping[str, Any]
    data_sha256: str | None
    random_seed: int | None
    base_seed: int | None
    seed_protocol: str | None
    rng_engine: str | None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "campaign_config",
            freeze_json_mapping(self.campaign_config),
        )
        object.__setattr__(
            self,
            "algorithm_parameters",
            freeze_json_mapping(self.algorithm_parameters),
        )
        object.__setattr__(
            self,
            "problem_parameters",
            freeze_json_mapping(self.problem_parameters),
        )


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
        if not isinstance(value, (Mapping, list, tuple)):
            raise RepositoryError("Expected an object or list metric value")
        return StoredValue(value_json=_metric_json(value))
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
    if isinstance(value, (Mapping, list, tuple)):
        return StoredValue(value_json=_metric_json(value))
    raise RepositoryError(f"Unsupported metric value type: {type(value).__name__}")


def _metric_json(value: Any) -> str:
    try:
        return canonical_json(value)
    except (TypeError, ValueError) as error:
        raise RepositoryError(f"Invalid JSON metric value: {error}") from error


class ExperimentRepository:
    def __init__(self, connection: sqlite3.Connection, registry: MetricRegistry):
        validate_current_schema(connection)
        self.connection = connection
        self.registry = registry

    @property
    def database_path(self) -> Path:
        """Return the absolute main-database path required by worker processes."""

        row = self.connection.execute("PRAGMA database_list").fetchone()
        if row is None or not row["file"]:
            raise RepositoryError("Parallel execution requires a file-backed database")
        return Path(row["file"]).resolve()

    def campaign_config(self, campaign_id: str) -> Mapping[str, Any]:
        row = self.connection.execute(
            "SELECT config_json FROM campaigns WHERE campaign_id = ?", (campaign_id,)
        ).fetchone()
        if row is None:
            raise RepositoryError(f"Unknown campaign: {campaign_id!r}")
        return freeze_json_mapping(json.loads(row["config_json"]))

    @contextmanager
    def transaction(self):
        """Group repository operations into one atomic SQLite transaction."""

        if self.connection.in_transaction:
            with nullcontext():
                yield
            return
        # Acquire the single SQLite writer slot before any reads inside the
        # transaction. This avoids deferred-transaction upgrade deadlocks when
        # multiple worker processes persist completed replicas concurrently.
        self.connection.execute("BEGIN IMMEDIATE")
        try:
            yield
            self.connection.commit()
        except BaseException:
            self.connection.rollback()
            raise

    def _write_scope(self):
        if self.connection.in_transaction:
            return nullcontext()
        return self.connection

    def create_campaign(
        self,
        campaign_id: str,
        name: str,
        config: Mapping[str, Any],
        code_commit: str,
        metric_selection: object = "minimal",
        created_at: str | None = None,
        notes: str | None = None,
        base_seed: int | None = None,
        seed_protocol: str | None = None,
        rng_engine: str | None = None,
    ) -> tuple[str, ...]:
        randomness = (base_seed, seed_protocol, rng_engine)
        if any(value is not None for value in randomness) and not all(
            value is not None for value in randomness
        ):
            raise RepositoryError(
                "base_seed, seed_protocol and rng_engine must be set together"
            )
        if base_seed is not None and (
            isinstance(base_seed, bool)
            or not isinstance(base_seed, int)
            or not 0 <= base_seed <= MAX_SEED
        ):
            raise RepositoryError(
                f"base_seed must be an integer between 0 and {MAX_SEED}"
            )
        config_payload = canonical_json(config)
        timestamp = created_at or utc_now()
        with self._write_scope():
            self.connection.execute(
                """
                INSERT INTO campaigns (
                    campaign_id, name, config_json, config_sha256, code_commit,
                    metric_registry_version, schema_version, created_at, notes,
                    base_seed, seed_protocol, rng_engine
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    campaign_id,
                    name,
                    config_payload,
                    sha256_text(config_payload),
                    code_commit,
                    self.registry.schema_version,
                    current_schema_version(self.connection),
                    timestamp,
                    notes,
                    base_seed,
                    seed_protocol,
                    rng_engine,
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
        if optimum is not None and not math.isfinite(optimum):
            raise RepositoryError("Problem optimum must be finite or None")
        _validate_sha256(data_sha256, "data_sha256")
        with self._write_scope():
            existing = self.connection.execute(
                """
                SELECT instance_id, optimum, direction, data_sha256 FROM problem_instances
                WHERE problem_family = ? AND name = ? AND dimension IS ?
                  AND parameters_json = ?
                """,
                (problem_family, name, dimension, parameters_json),
            ).fetchone()
            if existing is not None:
                requested_identity = {
                    "optimum": optimum,
                    "direction": direction,
                    "data_sha256": data_sha256,
                }
                conflicts = [
                    field
                    for field, requested in requested_identity.items()
                    if existing[field] != requested
                ]
                if conflicts:
                    raise RepositoryError(
                        f"Problem identity conflict for instance {existing['instance_id']}: "
                        + ", ".join(
                            f"{field}: stored={existing[field]!r}, "
                            f"requested={requested_identity[field]!r}"
                            for field in conflicts
                        )
                    )
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
            if cursor.lastrowid is None:
                raise RepositoryError("Problem instance insert did not return an ID")
            return cursor.lastrowid

    def add_algorithm_configuration(
        self,
        configuration_id: str,
        campaign_id: str,
        algorithm: str,
        optimizer_version: str,
        parameters: Mapping[str, Any],
        budget_type: str,
        budget_evaluations: int | None = None,
        budget_iterations: int | None = None,
        population_size: int | None = None,
        created_at: str | None = None,
        treatment_id: str | None = None,
    ) -> None:
        self._require_campaign_status(campaign_id, "draft")
        if not isinstance(optimizer_version, str) or not optimizer_version.strip():
            raise RepositoryError("optimizer_version must be a non-empty string")
        local_id = configuration_id if treatment_id is None else treatment_id
        if not isinstance(local_id, str) or not local_id.strip():
            raise RepositoryError("treatment_id must be a non-empty string")
        parameters_json = canonical_json(parameters)
        with self._write_scope():
            self.connection.execute(
                """
                INSERT INTO algorithm_configurations (
                    configuration_id, campaign_id, algorithm, optimizer_version,
                    parameters_json,
                    parameters_sha256, budget_type, budget_evaluations,
                    budget_iterations, population_size, created_at, treatment_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    configuration_id,
                    campaign_id,
                    algorithm,
                    optimizer_version,
                    parameters_json,
                    sha256_text(parameters_json),
                    budget_type,
                    budget_evaluations,
                    budget_iterations,
                    population_size,
                    created_at or utc_now(),
                    local_id,
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
        if random_seed is not None and (
            isinstance(random_seed, bool)
            or not isinstance(random_seed, int)
            or not 0 <= random_seed <= MAX_SEED
        ):
            raise RepositoryError(
                f"random_seed must be an integer between 0 and {MAX_SEED}"
            )
        self._require_campaign_status(campaign_id, "draft")
        with self._write_scope():
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
            if cursor.lastrowid is None:
                raise RepositoryError("Run insert did not return an ID")
            return cursor.lastrowid

    def get_planned_run(self, run_id: int) -> PlannedRun:
        """Return the normalized database plan used for preflight validation."""

        row = self.connection.execute(
            """
            SELECT
                r.run_id, r.status, r.random_seed, c.config_json,
                ac.algorithm, ac.optimizer_version,
                ac.parameters_json AS algorithm_parameters_json,
                ac.budget_evaluations, ac.budget_iterations, ac.population_size,
                pi.problem_family, pi.name AS problem_name, pi.dimension,
                pi.optimum, pi.direction,
                pi.parameters_json AS problem_parameters_json, pi.data_sha256,
                c.base_seed, c.seed_protocol, c.rng_engine
            FROM runs AS r
            JOIN campaigns AS c ON c.campaign_id = r.campaign_id
            JOIN algorithm_configurations AS ac
              ON ac.configuration_id = r.configuration_id
             AND ac.campaign_id = r.campaign_id
            JOIN problem_instances AS pi ON pi.instance_id = r.instance_id
            WHERE r.run_id = ?
            """,
            (run_id,),
        ).fetchone()
        if row is None:
            raise RepositoryError(f"Unknown run: {run_id}")
        return PlannedRun(
            run_id=int(row["run_id"]),
            status=str(row["status"]),
            campaign_config=json.loads(row["config_json"]),
            algorithm=str(row["algorithm"]),
            optimizer_version=row["optimizer_version"],
            algorithm_parameters=json.loads(row["algorithm_parameters_json"]),
            budget_evaluations=row["budget_evaluations"],
            budget_iterations=row["budget_iterations"],
            population_size=row["population_size"],
            problem_family=str(row["problem_family"]),
            problem_name=str(row["problem_name"]),
            dimension=row["dimension"],
            optimum=row["optimum"],
            direction=str(row["direction"]),
            problem_parameters=json.loads(row["problem_parameters_json"]),
            data_sha256=row["data_sha256"],
            random_seed=row["random_seed"],
            base_seed=row["base_seed"],
            seed_protocol=row["seed_protocol"],
            rng_engine=row["rng_engine"],
        )

    def campaign_status(self, campaign_id: str) -> str:
        row = self.connection.execute(
            "SELECT status FROM campaigns WHERE campaign_id = ?", (campaign_id,)
        ).fetchone()
        if row is None:
            raise RepositoryError(f"Unknown campaign: {campaign_id!r}")
        return str(row["status"])

    def run_status(self, run_id: int) -> str:
        return str(self._get_run(run_id)["status"])

    def run_ids_by_status(
        self, campaign_id: str, status: str = "planned"
    ) -> tuple[int, ...]:
        allowed = {"planned", "running", "completed", "failed", "cancelled"}
        if status not in allowed:
            raise RepositoryError(f"Unsupported run status: {status!r}")
        self.campaign_status(campaign_id)
        rows = self.connection.execute(
            """
            SELECT run_id FROM runs
            WHERE campaign_id = ? AND status = ?
            ORDER BY run_id
            """,
            (campaign_id, status),
        ).fetchall()
        return tuple(int(row["run_id"]) for row in rows)

    def selected_metric_ids(self, campaign_id: str) -> tuple[str, ...]:
        self.campaign_status(campaign_id)
        selected = self._compatible_metric_contract(campaign_id)
        return tuple(
            metric_id for metric_id in self.registry.metrics if metric_id in selected
        )

    def selected_metric_ids_for_run(self, run_id: int) -> tuple[str, ...]:
        """Return the metric contract of the campaign that owns ``run_id``."""

        row = self.connection.execute(
            "SELECT campaign_id FROM runs WHERE run_id = ?", (run_id,)
        ).fetchone()
        if row is None:
            raise RepositoryError(f"Unknown run: {run_id}")
        return self.selected_metric_ids(str(row["campaign_id"]))

    def start_campaign(self, campaign_id: str, started_at: str | None = None) -> None:
        self._require_campaign_status(campaign_id, "draft")
        self._compatible_metric_contract(campaign_id)
        run_count = self.connection.execute(
            "SELECT COUNT(*) FROM runs WHERE campaign_id = ?", (campaign_id,)
        ).fetchone()[0]
        if run_count == 0:
            raise RepositoryError("A campaign cannot start without planned runs")
        with self._write_scope():
            self.connection.execute(
                "UPDATE campaigns SET status = 'running', started_at = ? WHERE campaign_id = ?",
                (started_at or utc_now(), campaign_id),
            )

    def start_run(self, run_id: int, started_at: str | None = None) -> None:
        row = self._get_run(run_id)
        self._require_campaign_status(row["campaign_id"], "running")
        self._compatible_metric_contract(row["campaign_id"])
        if row["status"] != "planned":
            raise RepositoryError(f"Run {run_id} is not planned")
        timestamp = started_at or utc_now()
        with self._write_scope():
            attempt_index = int(
                self.connection.execute(
                    """
                    SELECT COALESCE(MAX(attempt_index), 0) + 1
                    FROM run_attempts WHERE run_id = ?
                    """,
                    (run_id,),
                ).fetchone()[0]
            )
            self.connection.execute(
                """
                INSERT INTO run_attempts (
                    run_id, attempt_index, status, started_at
                ) VALUES (?, ?, 'running', ?)
                """,
                (run_id, attempt_index, timestamp),
            )
            self.connection.execute(
                "UPDATE runs SET status = 'running', started_at = ? WHERE run_id = ?",
                (timestamp, run_id),
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
        self._require_writable_campaign(row["campaign_id"])
        if row["status"] != "running":
            raise RepositoryError(
                "Trace metrics can only be recorded for a running run"
            )
        self._validate_selected_metrics(row["campaign_id"], metrics, "iteration")
        self._require_metric_values(run_id, metrics, "iteration", iteration_index)
        if (
            isinstance(checkpoint_index, bool)
            or not isinstance(checkpoint_index, int)
            or checkpoint_index < 0
            or isinstance(evaluations, bool)
            or not isinstance(evaluations, int)
            or evaluations < 0
        ):
            raise RepositoryError(
                "Trace checkpoint and evaluations must be non-negative integers"
            )
        budget = self.get_planned_run(run_id).budget_evaluations
        if budget is not None and evaluations > budget:
            raise RepositoryError("Trace evaluations exceed the planned budget")

        previous = self.connection.execute(
            """
            SELECT tp.checkpoint_index, tp.evaluations, tm.value_real AS objective
            FROM trace_points tp LEFT JOIN trace_metric_values tm
              ON tm.run_id=tp.run_id AND tm.checkpoint_index=tp.checkpoint_index
             AND tm.metric_id='objective_best'
            WHERE tp.run_id = ?
            ORDER BY tp.checkpoint_index DESC LIMIT 1
            """,
            (run_id,),
        ).fetchone()
        if checkpoint_index != (
            0 if previous is None else previous["checkpoint_index"] + 1
        ):
            raise RepositoryError("Trace checkpoints must be contiguous")
        if previous is not None and evaluations < previous["evaluations"]:
            raise RepositoryError("Trace checkpoints and evaluations must be monotonic")
        if (
            previous is not None
            and previous["objective"] is not None
            and "objective_best" in metrics
        ):
            value = encode_metric_value(metrics["objective_best"], "float").value_real
            direction = self.get_planned_run(run_id).direction
            if value is None:
                raise RepositoryError("Trace objective must be numeric")
            if (direction == "minimize" and value > previous["objective"]) or (
                direction == "maximize" and value < previous["objective"]
            ):
                raise RepositoryError("Trace best-so-far objective cannot worsen")

        with self._write_scope():
            self.connection.execute(
                """
                INSERT INTO trace_points (
                    run_id, checkpoint_index, iteration_index,
                    evaluations, elapsed_seconds
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (
                    run_id,
                    checkpoint_index,
                    iteration_index,
                    evaluations,
                    elapsed_seconds,
                ),
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
        initial_population_sha256: str | None = None,
        initial_velocity_sha256: str | None = None,
        initial_state_hash_version: str | None = None,
    ) -> None:
        row = self._get_run(run_id)
        self._require_writable_campaign(row["campaign_id"])
        if row["status"] != "running":
            raise RepositoryError(f"Run {run_id} is not running")
        if not math.isfinite(objective_best):
            raise RepositoryError("Completed objective_best must be finite")
        plan = self.get_planned_run(run_id)
        if not valid_solution(solution, plan.dimension):
            raise RepositoryError(
                "Completed solution must be finite and match planned dimension"
            )
        if (
            isinstance(evaluations, bool)
            or not isinstance(evaluations, int)
            or evaluations < 0
        ):
            raise RepositoryError(
                "Completed evaluations must be a non-negative integer"
            )
        if (
            isinstance(runtime_total_seconds, bool)
            or not isinstance(runtime_total_seconds, (int, float))
            or not math.isfinite(runtime_total_seconds)
            or runtime_total_seconds < 0
        ):
            raise RepositoryError(
                "Completed runtime_total_seconds must be finite and non-negative"
            )
        planned_budget = self.connection.execute(
            """
            SELECT ac.budget_evaluations
            FROM runs AS r
            JOIN algorithm_configurations AS ac
              ON ac.configuration_id = r.configuration_id
             AND ac.campaign_id = r.campaign_id
            WHERE r.run_id = ?
            """,
            (run_id,),
        ).fetchone()["budget_evaluations"]
        if planned_budget is not None and evaluations != int(planned_budget):
            raise RepositoryError(
                "Completed evaluations must equal the planned evaluation budget"
            )
        _validate_sha256(initial_population_sha256, "initial_population_sha256")
        _validate_sha256(initial_velocity_sha256, "initial_velocity_sha256")
        if initial_state_hash_version is not None:
            if (
                not isinstance(initial_state_hash_version, str)
                or not initial_state_hash_version.strip()
                or initial_population_sha256 is None
            ):
                raise RepositoryError(
                    "initial_state_hash_version requires a non-empty name and population hash"
                )
        selected_metrics = metrics or {}
        if POST_RUN_TIMING_METRICS.intersection(selected_metrics):
            raise RepositoryError(
                "Post-run timings must be observed after the result commit"
            )
        self._validate_selected_metrics(row["campaign_id"], selected_metrics, "replica")
        self._require_metric_values(run_id, selected_metrics, "replica")
        if (
            "objective_best" in selected_metrics
            and selected_metrics["objective_best"] != objective_best
        ):
            raise RepositoryError(
                "objective_best observation differs from completed objective"
            )
        issues = [
            message
            for _, message, issue_run_id in metric_evidence_issues(
                self.connection, row["campaign_id"], completing_run_id=run_id
            )
            if issue_run_id is None or issue_run_id == run_id
        ]
        if issues:
            raise RepositoryError(
                "Invalid completed metric evidence: " + "; ".join(issues)
            )
        trace_issues = trace_result_issues(
            self.connection, run_id, objective_best, evaluations
        )
        if trace_issues:
            raise RepositoryError("; ".join(message for _, message, _ in trace_issues))
        post_metrics = (
            set(self.selected_metric_ids(row["campaign_id"])) & POST_RUN_TIMING_METRICS
        )
        timestamp = finished_at or utc_now()

        with self._write_scope():
            attempt_id = self._active_attempt_id(run_id)
            self.connection.execute(
                """
                UPDATE runs
                SET status = 'completed', finished_at = ?, objective_best = ?,
                    solution_json = ?, evaluations = ?, runtime_total_seconds = ?,
                    feasible = ?, constraint_violation = ?,
                    initial_population_sha256 = ?, initial_velocity_sha256 = ?,
                    initial_state_hash_version = ?, finalization_status = ?
                WHERE run_id = ?
                """,
                (
                    timestamp,
                    objective_best,
                    canonical_json(solution),
                    evaluations,
                    runtime_total_seconds,
                    None if feasible is None else int(feasible),
                    constraint_violation,
                    initial_population_sha256,
                    initial_velocity_sha256,
                    initial_state_hash_version,
                    "pending" if post_metrics else "completed",
                    run_id,
                ),
            )
            self.connection.execute(
                """
                UPDATE run_attempts
                SET status = 'completed', finished_at = ?
                WHERE attempt_id = ?
                """,
                (timestamp, attempt_id),
            )
            for metric_id, value in selected_metrics.items():
                self._insert_run_metric(run_id, metric_id, value, "observed")

    def record_completed_run_metrics(
        self,
        run_id: int,
        metrics: Mapping[str, Any],
        provenance: str = "observed",
    ) -> None:
        """Append measurements only knowable after the completion transaction."""

        with self.transaction():
            row = self._get_run(run_id)
            self._require_writable_campaign(row["campaign_id"])
            if row["status"] != "completed" or row["finalization_status"] != "pending":
                raise RepositoryError(
                    "Post-run metrics require a completed run with pending finalization"
                )
            self._validate_selected_metrics(row["campaign_id"], metrics, "replica")
            selected = (
                set(self.selected_metric_ids(row["campaign_id"]))
                & POST_RUN_TIMING_METRICS
            )
            if set(metrics) != selected:
                raise RepositoryError(
                    "Finalization requires exactly the selected post-run timings"
                )
            values = {
                key: encode_metric_value(value, "float").value_real
                for key, value in metrics.items()
            }
            if any(value is None or value < 0 for value in values.values()):
                raise RepositoryError(
                    "Post-run timings must be finite and non-negative"
                )
            persistence = values.get("persistence_total_seconds")
            wall = values.get("run_wall_total_seconds")
            if persistence is not None and wall is not None and persistence > wall:
                raise RepositoryError(
                    "Run wall time cannot be smaller than persistence time"
                )
            for metric_id, value in metrics.items():
                self._insert_run_metric(run_id, metric_id, value, provenance)
            self.connection.execute(
                "UPDATE runs SET finalization_status='completed' WHERE run_id=?",
                (run_id,),
            )

    def fail_run_finalization(
        self, run_id: int, error_type: str, error_message: str
    ) -> None:
        """Preserve the committed scientific result and record a closure failure."""

        with self.transaction():
            row = self._get_run(run_id)
            self._require_writable_campaign(row["campaign_id"])
            if row["status"] != "completed":
                raise RepositoryError(
                    "Finalization failure requires a committed result"
                )
            self.connection.execute(
                "UPDATE runs SET finalization_status='failed',finalization_error_type=?,"
                "finalization_error_message=? WHERE run_id=?",
                (error_type, error_message, run_id),
            )

    def fail_run(
        self,
        run_id: int,
        error_type: str,
        error_message: str,
        finished_at: str | None = None,
        failure_phase: str = "optimization",
    ) -> None:
        row = self._get_run(run_id)
        self._require_writable_campaign(row["campaign_id"])
        if row["status"] not in {"planned", "running"}:
            raise RepositoryError(f"Run {run_id} cannot transition to failed")
        timestamp = finished_at or utc_now()
        with self._write_scope():
            if row["status"] == "running":
                attempt_id = self._active_attempt_id(run_id)
                self.connection.execute(
                    """
                    UPDATE run_attempts
                    SET status = 'failed', finished_at = ?,
                        error_type = ?, error_message = ?
                    WHERE attempt_id = ?
                    """,
                    (timestamp, error_type, error_message, attempt_id),
                )
            else:
                attempt_index = int(
                    self.connection.execute(
                        """
                        SELECT COALESCE(MAX(attempt_index), 0) + 1
                        FROM run_attempts WHERE run_id = ?
                        """,
                        (run_id,),
                    ).fetchone()[0]
                )
                self.connection.execute(
                    """
                    INSERT INTO run_attempts (
                        run_id, attempt_index, status, started_at, finished_at,
                        error_type, error_message
                    ) VALUES (?, ?, 'failed', ?, ?, ?, ?)
                    """,
                    (
                        run_id,
                        attempt_index,
                        row["started_at"] or timestamp,
                        timestamp,
                        error_type,
                        error_message,
                    ),
                )
            self.connection.execute(
                """
                UPDATE runs
                SET status = 'failed', finished_at = ?, error_type = ?, error_message = ?
                WHERE run_id = ?
                """,
                (timestamp, error_type, error_message, run_id),
            )
            self.connection.execute(
                "UPDATE runs SET failure_phase=? WHERE run_id=?",
                (failure_phase, run_id),
            )
            self.connection.execute(
                "UPDATE run_attempts SET failure_phase=? WHERE attempt_id=("
                "SELECT attempt_id FROM run_attempts WHERE run_id=? ORDER BY attempt_index DESC LIMIT 1)",
                (failure_phase, run_id),
            )

    def recover_interrupted_run(
        self,
        campaign_id: str,
        run_id: int,
        reason: str,
        recovered_at: str | None = None,
    ) -> int:
        """Abandon the active attempt and requeue its logical replica.

        Recovery is explicit and audit-preserving. Partial canonical traces are
        removed before the same run identity is returned to ``planned``; the
        attempt ledger retains their counts and the operator-supplied reason.
        """

        if not isinstance(reason, str) or not reason.strip():
            raise RepositoryError("Recovery reason must be a non-empty string")
        row = self._get_run(run_id)
        if row["campaign_id"] != campaign_id:
            raise RepositoryError(
                f"Run {run_id} does not belong to campaign {campaign_id!r}"
            )
        self._require_campaign_status(campaign_id, "running")
        if row["status"] != "running":
            raise RepositoryError(f"Run {run_id} is not interrupted/running")

        timestamp = recovered_at or utc_now()
        with self._write_scope():
            attempt_id = self._active_attempt_id(run_id)
            trace_count = int(
                self.connection.execute(
                    "SELECT COUNT(*) FROM trace_points WHERE run_id = ?", (run_id,)
                ).fetchone()[0]
            )
            metric_count = int(
                self.connection.execute(
                    "SELECT COUNT(*) FROM run_metric_values WHERE run_id = ?", (run_id,)
                ).fetchone()[0]
            )
            self.connection.execute(
                "DELETE FROM trace_points WHERE run_id = ?", (run_id,)
            )
            self.connection.execute(
                "DELETE FROM run_metric_values WHERE run_id = ?", (run_id,)
            )
            self.connection.execute(
                """
                UPDATE run_attempts
                SET status = 'abandoned', finished_at = ?,
                    error_type = 'InterruptedRunRecovery', error_message = ?,
                    recovery_reason = ?, discarded_trace_points = ?,
                    discarded_run_metrics = ?
                WHERE attempt_id = ?
                """,
                (
                    timestamp,
                    reason.strip(),
                    reason.strip(),
                    trace_count,
                    metric_count,
                    attempt_id,
                ),
            )
            self.connection.execute(
                """
                UPDATE runs
                SET status = 'planned', started_at = NULL, finished_at = NULL,
                    objective_best = NULL, solution_json = NULL,
                    evaluations = NULL, runtime_total_seconds = NULL,
                    feasible = NULL, constraint_violation = NULL,
                    error_type = NULL, error_message = NULL,
                    initial_population_sha256 = NULL,
                    initial_velocity_sha256 = NULL, initial_state_hash_version = NULL
                WHERE run_id = ?
                """,
                (run_id,),
            )
        return attempt_id

    def cancel_run(
        self,
        campaign_id: str,
        run_id: int,
        reason: str,
        cancelled_at: str | None = None,
    ) -> int | None:
        """Intentionally exclude a planned or running run from execution.

        Cancelling a running run closes its active attempt and removes partial
        canonical observations. Cancelling a planned run creates no attempt.
        In both cases the operator-supplied reason remains auditable.
        """

        if not isinstance(reason, str) or not reason.strip():
            raise RepositoryError("Cancellation reason must be a non-empty string")
        row = self._get_run(run_id)
        if row["campaign_id"] != campaign_id:
            raise RepositoryError(
                f"Run {run_id} does not belong to campaign {campaign_id!r}"
            )
        self._require_campaign_status(campaign_id, "running")
        if row["status"] not in {"planned", "running"}:
            raise RepositoryError(f"Run {run_id} cannot transition to cancelled")

        timestamp = cancelled_at or utc_now()
        reason = reason.strip()
        attempt_id: int | None = None
        with self._write_scope():
            trace_count = int(
                self.connection.execute(
                    "SELECT COUNT(*) FROM trace_points WHERE run_id = ?", (run_id,)
                ).fetchone()[0]
            )
            metric_count = int(
                self.connection.execute(
                    "SELECT COUNT(*) FROM run_metric_values WHERE run_id = ?", (run_id,)
                ).fetchone()[0]
            )
            self.connection.execute(
                "DELETE FROM trace_points WHERE run_id = ?", (run_id,)
            )
            self.connection.execute(
                "DELETE FROM run_metric_values WHERE run_id = ?", (run_id,)
            )
            if row["status"] == "running":
                attempt_id = self._active_attempt_id(run_id)
                self.connection.execute(
                    """
                    UPDATE run_attempts
                    SET status = 'cancelled', finished_at = ?, cancellation_reason = ?,
                        discarded_trace_points = ?, discarded_run_metrics = ?
                    WHERE attempt_id = ?
                    """,
                    (timestamp, reason, trace_count, metric_count, attempt_id),
                )
            self.connection.execute(
                """
                UPDATE runs
                SET status = 'cancelled', finished_at = ?, cancellation_reason = ?,
                    objective_best = NULL, solution_json = NULL, evaluations = NULL,
                    runtime_total_seconds = NULL, feasible = NULL,
                    constraint_violation = NULL, error_type = NULL,
                    error_message = NULL, initial_population_sha256 = NULL,
                    initial_velocity_sha256 = NULL, initial_state_hash_version = NULL
                WHERE run_id = ?
                """,
                (timestamp, reason, run_id),
            )
        return attempt_id

    def finish_campaign(self, campaign_id: str, finished_at: str | None = None) -> None:
        self._require_campaign_status(campaign_id, "running")
        finalization_issues = [
            message
            for code, message, _ in run_evidence_issues(self.connection, campaign_id)
            if code.startswith("run_finalization_")
            or code in {"missing_post_run_timing", "invalid_post_run_timing"}
        ]
        if finalization_issues:
            raise RepositoryError(
                "Campaign finalization incomplete: " + "; ".join(finalization_issues)
            )
        pending = self.connection.execute(
            """
            SELECT COUNT(*) FROM runs
            WHERE campaign_id = ? AND status NOT IN ('completed', 'failed', 'cancelled')
            """,
            (campaign_id,),
        ).fetchone()[0]
        if pending:
            raise RepositoryError("Campaign still has non-terminal runs")
        with self._write_scope():
            self.connection.execute(
                "UPDATE campaigns SET status = 'completed', finished_at = ? WHERE campaign_id = ?",
                (finished_at or utc_now(), campaign_id),
            )

    def seal_campaign(
        self,
        campaign_id: str,
        sealed_at: str | None = None,
        waiver_reason: str | None = None,
    ) -> None:
        self._require_campaign_status(campaign_id, "completed")
        counts = self.connection.execute(
            """
            SELECT
                SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) AS failed,
                SUM(CASE WHEN status = 'cancelled' THEN 1 ELSE 0 END) AS cancelled
            FROM runs WHERE campaign_id = ?
            """,
            (campaign_id,),
        ).fetchone()
        failed = int(counts["failed"] or 0)
        cancelled = int(counts["cancelled"] or 0)
        incomplete = failed + cancelled
        normalized_waiver = (
            waiver_reason.strip() if isinstance(waiver_reason, str) else ""
        )
        if incomplete and not normalized_waiver:
            raise RepositoryError(
                "Campaign has failed or cancelled runs; sealing requires an explicit waiver reason"
            )
        if not incomplete and waiver_reason is not None:
            raise RepositoryError(
                "A seal waiver is only valid for an incomplete campaign"
            )
        timestamp = sealed_at or utc_now()
        with self.transaction():
            from .integrity import audit_campaign_integrity

            self._require_campaign_status(campaign_id, "completed")
            report = audit_campaign_integrity(self.connection, campaign_id)
            if not report.is_valid:
                raise RepositoryError(
                    "Cannot seal campaign with invalid integrity: "
                    + "; ".join(issue.message for issue in report.issues)
                )
            if incomplete:
                self.connection.execute(
                    """
                    INSERT INTO campaign_seal_waivers (
                        campaign_id, reason, approved_at,
                        failed_run_count, cancelled_run_count
                    ) VALUES (?, ?, ?, ?, ?)
                    """,
                    (campaign_id, normalized_waiver, timestamp, failed, cancelled),
                )
            self.connection.execute(
                "UPDATE campaigns SET status = 'sealed', sealed_at = ? WHERE campaign_id = ?",
                (timestamp, campaign_id),
            )

    def _get_run(self, run_id: int) -> sqlite3.Row:
        row = self.connection.execute(
            "SELECT * FROM runs WHERE run_id = ?", (run_id,)
        ).fetchone()
        if row is None:
            raise RepositoryError(f"Unknown run: {run_id}")
        return row

    def _require_writable_campaign(self, campaign_id: str) -> None:
        if self.campaign_status(campaign_id) == "sealed":
            raise RepositoryError("Cannot modify a sealed campaign")

    def _active_attempt_id(self, run_id: int) -> int:
        rows = self.connection.execute(
            """
            SELECT attempt_id FROM run_attempts
            WHERE run_id = ? AND status = 'running'
            """,
            (run_id,),
        ).fetchall()
        if len(rows) != 1:
            raise RepositoryError(
                f"Run {run_id} must have exactly one active execution attempt"
            )
        return int(rows[0]["attempt_id"])

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
        selected = self._compatible_metric_contract(campaign_id)
        unknown = set(metrics) - set(selected)
        if unknown:
            raise RepositoryError(
                "Metrics were not selected for this campaign: "
                + ", ".join(sorted(unknown))
            )
        invalid_scope = {
            metric_id
            for metric_id in metrics
            if scope not in selected[metric_id].definition.scope
        }
        if invalid_scope:
            raise RepositoryError(
                f"Metrics do not support {scope!r} scope: "
                + ", ".join(sorted(invalid_scope))
            )

    def _compatible_metric_contract(
        self, campaign_id: str
    ) -> dict[str, SelectedMetric]:
        try:
            selected = selected_metric_contract(self.connection, campaign_id)
        except MetricContractError as error:
            raise RepositoryError(str(error)) from error
        for metric_id, item in selected.items():
            live = self.registry.metrics.get(metric_id)
            if (
                live is None
                or not live.available
                or live.version != item.definition.version
                or sha256_text(canonical_json(asdict(live))) != item.digest
            ):
                raise RepositoryError(
                    f"Metric definition mismatch for selected {metric_id}"
                )
        return selected

    def _require_metric_values(
        self,
        run_id: int,
        metrics: Mapping[str, Any],
        scope: str,
        iteration: int | None = None,
    ) -> None:
        row = self.connection.execute(
            "SELECT r.campaign_id,ac.algorithm,ac.parameters_json FROM runs r "
            "JOIN algorithm_configurations ac ON ac.configuration_id=r.configuration_id "
            "WHERE r.run_id=?",
            (run_id,),
        ).fetchone()
        contract = self._compatible_metric_contract(row["campaign_id"])
        missing = required_value_ids(
            contract,
            scope,
            algorithm=row["algorithm"],
            parameters=json.loads(row["parameters_json"]),
            iteration=iteration,
        ) - set(metrics)
        if missing:
            raise RepositoryError(
                f"Missing required {scope} metrics: " + ", ".join(sorted(missing))
            )

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
                definition.version,
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
                definition.version,
                provenance,
                encoded.value_real,
                encoded.value_integer,
                encoded.value_text,
                encoded.value_json,
            ),
        )


def _validate_sha256(value: str | None, label: str) -> None:
    if value is None:
        return
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise RepositoryError(f"{label} must be a lowercase SHA-256 digest")
