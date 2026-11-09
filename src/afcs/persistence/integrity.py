"""Read-only integrity audit for persisted experimental campaigns."""

from __future__ import annotations

import json
import math
import sqlite3
from dataclasses import dataclass

from .database import validate_current_schema
from .metric_contracts import metric_evidence_issues
from .run_contracts import run_evidence_issues


@dataclass(frozen=True, slots=True)
class CampaignIntegrityIssue:
    code: str
    message: str
    run_id: int | None = None


@dataclass(frozen=True, slots=True)
class CampaignIntegrityWarning:
    code: str
    message: str
    run_id: int | None = None


@dataclass(frozen=True, slots=True)
class CampaignIntegrityReport:
    campaign_id: str
    campaign_status: str
    run_count: int
    attempt_count: int
    trace_point_count: int
    issues: tuple[CampaignIntegrityIssue, ...]
    warnings: tuple[CampaignIntegrityWarning, ...]

    @property
    def is_valid(self) -> bool:
        return not self.issues


def audit_campaign_integrity(
    connection: sqlite3.Connection, campaign_id: str
) -> CampaignIntegrityReport:
    """Inspect relational and lifecycle invariants without changing campaign data."""

    validate_current_schema(connection)
    campaign = connection.execute(
        "SELECT status FROM campaigns WHERE campaign_id = ?", (campaign_id,)
    ).fetchone()
    if campaign is None:
        raise ValueError(f"Unknown campaign: {campaign_id!r}")

    issues = [
        CampaignIntegrityIssue(code, message, run_id)
        for code, message, run_id in (
            metric_evidence_issues(connection, campaign_id)
            + run_evidence_issues(connection, campaign_id)
        )
    ]
    warnings: list[CampaignIntegrityWarning] = []
    integrity = connection.execute("PRAGMA integrity_check").fetchall()
    if [row[0] for row in integrity] != ["ok"]:
        issues.append(
            CampaignIntegrityIssue(
                "sqlite_integrity", "SQLite integrity_check did not return 'ok'"
            )
        )
    if connection.execute("PRAGMA foreign_key_check").fetchone() is not None:
        issues.append(
            CampaignIntegrityIssue(
                "foreign_key_violation", "SQLite foreign_key_check found violations"
            )
        )

    runs = connection.execute(
        """
        SELECT r.*, ac.budget_evaluations, pi.dimension
        FROM runs AS r
        JOIN algorithm_configurations AS ac
          ON ac.configuration_id = r.configuration_id
         AND ac.campaign_id = r.campaign_id
        JOIN problem_instances AS pi ON pi.instance_id = r.instance_id
        WHERE r.campaign_id = ?
        ORDER BY r.run_id
        """,
        (campaign_id,),
    ).fetchall()
    status = str(campaign["status"])
    if status in {"completed", "sealed"}:
        unfinished = [
            int(row["run_id"])
            for row in runs
            if row["status"] in {"planned", "running"}
        ]
        if unfinished:
            issues.append(
                CampaignIntegrityIssue(
                    "terminal_campaign_has_unfinished_runs",
                    f"Terminal campaign contains unfinished run_ids={unfinished}",
                )
            )

    attempt_count = 0
    trace_point_count = 0
    for run in runs:
        run_id = int(run["run_id"])
        attempts = connection.execute(
            """
            SELECT * FROM run_attempts
            WHERE run_id = ? ORDER BY attempt_index
            """,
            (run_id,),
        ).fetchall()
        attempt_count += len(attempts)
        if not attempts and run["status"] in {"completed", "failed", "running"}:
            issues.append(
                CampaignIntegrityIssue(
                    "missing_execution_attempt",
                    "Executed run lacks an execution attempt",
                    run_id,
                )
            )
        expected_indices = list(range(1, len(attempts) + 1))
        observed_indices = [int(row["attempt_index"]) for row in attempts]
        if observed_indices != expected_indices:
            issues.append(
                CampaignIntegrityIssue(
                    "attempt_sequence", "Attempt indices are not contiguous", run_id
                )
            )
        running_attempts = [row for row in attempts if row["status"] == "running"]
        if (run["status"] == "running") != (len(running_attempts) == 1):
            issues.append(
                CampaignIntegrityIssue(
                    "active_attempt_mismatch",
                    "Run status and active attempt do not agree",
                    run_id,
                )
            )
        if attempts and run["status"] in {"completed", "failed", "cancelled"}:
            if attempts[-1]["status"] != run["status"]:
                issues.append(
                    CampaignIntegrityIssue(
                        "terminal_attempt_mismatch",
                        "Run terminal status differs from its latest attempt",
                        run_id,
                    )
                )
            if run["status"] == "cancelled":
                attempt_reason = attempts[-1]["cancellation_reason"]
                if not isinstance(attempt_reason, str) or not attempt_reason.strip():
                    issues.append(
                        CampaignIntegrityIssue(
                            "cancelled_attempt_missing_reason",
                            "Cancelled execution attempt lacks a cancellation reason",
                            run_id,
                        )
                    )

        traces = connection.execute(
            """
            SELECT checkpoint_index, evaluations
            FROM trace_points WHERE run_id = ? ORDER BY checkpoint_index
            """,
            (run_id,),
        ).fetchall()
        trace_point_count += len(traces)
        if run["status"] == "planned" and traces:
            issues.append(
                CampaignIntegrityIssue(
                    "planned_run_has_traces",
                    "Planned run contains canonical trace points",
                    run_id,
                )
            )
        if run["status"] == "cancelled":
            warnings.append(
                CampaignIntegrityWarning(
                    "cancelled_run",
                    "Run was intentionally excluded from execution",
                    run_id,
                )
            )
            reason = run["cancellation_reason"]
            if not isinstance(reason, str) or not reason.strip():
                issues.append(
                    CampaignIntegrityIssue(
                        "cancelled_run_missing_reason",
                        "Cancelled run lacks a non-empty cancellation reason",
                        run_id,
                    )
                )
            if traces:
                issues.append(
                    CampaignIntegrityIssue(
                        "cancelled_run_has_traces",
                        "Cancelled run contains canonical trace points",
                        run_id,
                    )
                )
            run_metric_count = int(
                connection.execute(
                    "SELECT COUNT(*) FROM run_metric_values WHERE run_id = ?", (run_id,)
                ).fetchone()[0]
            )
            if run_metric_count:
                issues.append(
                    CampaignIntegrityIssue(
                        "cancelled_run_has_metrics",
                        "Cancelled run contains canonical run metrics",
                        run_id,
                    )
                )
        elif run["status"] == "failed":
            warnings.append(
                CampaignIntegrityWarning(
                    "failed_run", "Run ended with an execution failure", run_id
                )
            )
        if traces:
            checkpoints = [int(row["checkpoint_index"]) for row in traces]
            evaluations = [int(row["evaluations"]) for row in traces]
            if checkpoints != list(range(len(checkpoints))):
                issues.append(
                    CampaignIntegrityIssue(
                        "trace_sequence", "Trace checkpoints are not contiguous", run_id
                    )
                )
            if evaluations != sorted(evaluations):
                issues.append(
                    CampaignIntegrityIssue(
                        "trace_nfe_order", "Trace NFE values are not monotonic", run_id
                    )
                )

        if run["status"] == "completed":
            _audit_completed_run(run, traces, issues)

    failed_count = sum(run["status"] == "failed" for run in runs)
    cancelled_count = sum(run["status"] == "cancelled" for run in runs)
    if status == "sealed" and (failed_count or cancelled_count):
        waiver = connection.execute(
            "SELECT * FROM campaign_seal_waivers WHERE campaign_id = ?", (campaign_id,)
        ).fetchone()
        if waiver is None:
            issues.append(
                CampaignIntegrityIssue(
                    "sealed_incomplete_without_waiver",
                    "Sealed campaign has failed/cancelled runs but no approved waiver",
                )
            )
        else:
            warnings.append(
                CampaignIntegrityWarning(
                    "scientific_completeness_waived",
                    "Scientific completeness was explicitly waived when sealing",
                )
            )
            if (
                int(waiver["failed_run_count"]) != failed_count
                or int(waiver["cancelled_run_count"]) != cancelled_count
            ):
                issues.append(
                    CampaignIntegrityIssue(
                        "seal_waiver_count_mismatch",
                        "Seal waiver snapshot differs from current terminal run counts",
                    )
                )

    return CampaignIntegrityReport(
        campaign_id=campaign_id,
        campaign_status=status,
        run_count=len(runs),
        attempt_count=attempt_count,
        trace_point_count=trace_point_count,
        issues=tuple(issues),
        warnings=tuple(warnings),
    )


def _audit_completed_run(run, traces, issues: list[CampaignIntegrityIssue]) -> None:
    run_id = int(run["run_id"])
    required = (
        "finished_at",
        "objective_best",
        "solution_json",
        "evaluations",
        "runtime_total_seconds",
    )
    missing = [name for name in required if run[name] is None]
    if missing:
        issues.append(
            CampaignIntegrityIssue(
                "completed_run_missing_result",
                f"Completed run lacks required fields: {missing}",
                run_id,
            )
        )
        return
    objective = float(run["objective_best"])
    runtime = float(run["runtime_total_seconds"])
    if not math.isfinite(objective) or not math.isfinite(runtime) or runtime < 0.0:
        issues.append(
            CampaignIntegrityIssue(
                "non_finite_result", "Completed result is not finite", run_id
            )
        )
    evaluations = int(run["evaluations"])
    budget = run["budget_evaluations"]
    if budget is not None and evaluations != int(budget):
        issues.append(
            CampaignIntegrityIssue(
                "evaluation_budget_mismatch",
                f"Observed NFE={evaluations}, planned NFE={int(budget)}",
                run_id,
            )
        )
    if traces and int(traces[-1]["evaluations"]) != evaluations:
        issues.append(
            CampaignIntegrityIssue(
                "final_trace_nfe_mismatch",
                "Final trace NFE differs from the completed result",
                run_id,
            )
        )
    try:
        solution = json.loads(run["solution_json"])
        valid_solution = (
            isinstance(solution, list)
            and len(solution) == int(run["dimension"])
            and all(
                not isinstance(value, bool)
                and isinstance(value, (int, float))
                and math.isfinite(float(value))
                for value in solution
            )
        )
    except (TypeError, ValueError, json.JSONDecodeError):
        valid_solution = False
    if not valid_solution:
        issues.append(
            CampaignIntegrityIssue(
                "invalid_solution", "Stored solution is invalid or wrong-sized", run_id
            )
        )
