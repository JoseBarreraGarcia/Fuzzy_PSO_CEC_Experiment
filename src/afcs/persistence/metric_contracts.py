"""Persisted metric contracts shared by writes, audits and CSV projections."""

import hashlib
import json
import sqlite3
from dataclasses import dataclass
from typing import Any, Mapping

from afcs.metrics.registry import MetricDefinition


class MetricContractError(ValueError):
    """Persisted selection or observation violates its metric definition."""


@dataclass(frozen=True)
class SelectedMetric:
    definition: MetricDefinition
    required: bool
    digest: str


def selected_metric_contract(
    connection: sqlite3.Connection, campaign_id: str
) -> dict[str, SelectedMetric]:
    result = {}
    rows = connection.execute(
        """
        SELECT cm.metric_id, cm.metric_version, cm.required,
               md.definition_json, md.definition_sha256
        FROM campaign_metrics cm
        LEFT JOIN metric_definitions md
          ON md.metric_id=cm.metric_id AND md.metric_version=cm.metric_version
        WHERE cm.campaign_id=? ORDER BY cm.metric_id
        """,
        (campaign_id,),
    )
    for row in rows:
        payload = row["definition_json"]
        if not isinstance(payload, str):
            raise MetricContractError(
                f"Missing selected definition: {row['metric_id']}"
            )
        if (
            hashlib.sha256(payload.encode("utf-8")).hexdigest()
            != row["definition_sha256"]
        ):
            raise MetricContractError(
                f"Selected definition hash mismatch: {row['metric_id']}"
            )
        try:
            raw = json.loads(payload)
            definition = MetricDefinition(**{**raw, "scope": tuple(raw["scope"])})
        except (TypeError, ValueError, KeyError) as error:
            raise MetricContractError(
                f"Invalid selected definition: {row['metric_id']}: {error}"
            ) from error
        if (definition.metric_id, definition.version) != (
            row["metric_id"],
            row["metric_version"],
        ):
            raise MetricContractError(
                f"Selected definition identity mismatch: {row['metric_id']}"
            )
        result[definition.metric_id] = SelectedMetric(
            definition, bool(row["required"]), row["definition_sha256"]
        )
    return result


_RUN_FIELDS = {
    "run_status": "status",
    "replica_index": "replica_index",
    "random_seed": "random_seed",
    "evaluations": "evaluations",
    "runtime_total_seconds": "runtime_total_seconds",
    "feasible": "feasible",
    "constraint_violation": "constraint_violation",
}
_TRACE_FIELDS = {"evaluations": "evaluations", "iteration_index": "iteration_index"}


def required_value_ids(
    contract: Mapping[str, SelectedMetric],
    scope: str,
    *,
    algorithm: str,
    parameters: Mapping[str, Any],
    iteration: int | None = None,
) -> set[str]:
    """Required EAV observations; structural columns are validated separately."""

    structural = _RUN_FIELDS if scope == "replica" else _TRACE_FIELDS
    return {
        key
        for key, item in contract.items()
        if item.required
        and scope in item.definition.scope
        and key not in structural
        and metric_applies(item.definition, algorithm, parameters, iteration)
    }


def metric_applies(
    definition: MetricDefinition,
    algorithm: str,
    parameters: Mapping[str, Any],
    iteration: int | None,
) -> bool:
    if definition.missing_policy == "not_applicable_for_unconstrained_problem":
        return False
    if definition.source == "optimizer.pso":
        return algorithm in {"PSO", "PSO_FCS"} and iteration != 0
    if definition.source == "optimizer.ga":
        return algorithm == "GA" and iteration != 0
    if definition.missing_policy == "not_applicable_without_fuzzy_controller":
        policy = parameters.get("inertia_policy", {})
        return (
            isinstance(policy, Mapping)
            and policy.get("policy_id") == "fuzzy_inertia_mamdani"
            and iteration != 0
        )
    return True


def metric_evidence_issues(
    connection: sqlite3.Connection,
    campaign_id: str,
    *,
    completing_run_id: int | None = None,
) -> list[tuple[str, str, int | None]]:
    """Inspect persisted definitions/observations without consulting a live registry."""

    try:
        contract = selected_metric_contract(connection, campaign_id)
    except MetricContractError as error:
        return [("invalid_metric_contract", str(error), None)]
    issues: list[tuple[str, str, int | None]] = []
    for table, scope in (
        ("run_metric_values", "replica"),
        ("trace_metric_values", "iteration"),
    ):
        for row in connection.execute(
            f"SELECT m.* FROM {table} m JOIN runs r ON r.run_id=m.run_id "
            "WHERE r.campaign_id=? AND (? IS NULL OR r.run_id=?)",
            (campaign_id, completing_run_id, completing_run_id),
        ):
            selected = contract.get(row["metric_id"])
            if selected is None or scope not in selected.definition.scope:
                issues.append(
                    (
                        "unselected_metric",
                        f"Unselected {scope} metric {row['metric_id']}",
                        row["run_id"],
                    )
                )
            elif row["metric_version"] != selected.definition.version:
                issues.append(
                    (
                        "metric_version_mismatch",
                        f"{row['metric_id']}: selected={selected.definition.version}, "
                        f"observed={row['metric_version']}",
                        row["run_id"],
                    )
                )

    for run in connection.execute(
        "SELECT r.*,c.base_seed,ac.algorithm,ac.parameters_json FROM runs r "
        "JOIN campaigns c ON c.campaign_id=r.campaign_id "
        "JOIN algorithm_configurations ac ON ac.configuration_id=r.configuration_id "
        "WHERE r.campaign_id=? AND (r.status='completed' OR r.run_id=?) "
        "AND (? IS NULL OR r.run_id=?)",
        (campaign_id, completing_run_id, completing_run_id, completing_run_id),
    ):
        run_id = int(run["run_id"])
        parameters = json.loads(run["parameters_json"])
        observed = {
            row[0]
            for row in connection.execute(
                "SELECT metric_id FROM run_metric_values WHERE run_id=?", (run_id,)
            )
        }
        missing: set[str] = set()
        if run["status"] == "completed":
            missing = (
                required_value_ids(
                    contract,
                    "replica",
                    algorithm=run["algorithm"],
                    parameters=parameters,
                )
                - observed
            )
            for key, field in _RUN_FIELDS.items():
                selected = contract.get(key)
                if selected is None or not selected.required or run[field] is not None:
                    continue
                if key == "random_seed" and run["base_seed"] is None:
                    continue
                if (
                    selected.definition.missing_policy
                    == "not_applicable_for_unconstrained_problem"
                ):
                    continue
                missing.add(key)
        if missing:
            issues.append(
                (
                    "missing_required_metric",
                    "Missing required replica metrics: " + ", ".join(sorted(missing)),
                    run_id,
                )
            )
        for point in connection.execute(
            "SELECT * FROM trace_points WHERE run_id=?", (run_id,)
        ):
            required_trace = required_value_ids(
                contract,
                "iteration",
                algorithm=run["algorithm"],
                parameters=parameters,
                iteration=point["iteration_index"],
            )
            observed = {
                row[0]
                for row in connection.execute(
                    "SELECT metric_id FROM trace_metric_values WHERE run_id=? AND checkpoint_index=?",
                    (run_id, point["checkpoint_index"]),
                )
            }
            missing = required_trace - observed
            for key, field in _TRACE_FIELDS.items():
                item = contract.get(key)
                if item is not None and item.required and point[field] is None:
                    missing.add(key)
            if missing:
                issues.append(
                    (
                        "missing_required_metric",
                        f"Checkpoint {point['checkpoint_index']} missing required metrics: "
                        + ", ".join(sorted(missing)),
                        run_id,
                    )
                )
    return issues
