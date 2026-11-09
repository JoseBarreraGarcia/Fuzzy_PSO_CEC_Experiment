"""Result and best-so-far invariants shared by persistence and inspection."""

import json
import math
import sqlite3
from collections.abc import Mapping

POST_RUN_TIMING_METRICS = frozenset(
    {"persistence_total_seconds", "run_wall_total_seconds"}
)


def valid_solution(solution: object, dimension: int | None) -> bool:
    return (
        isinstance(solution, (list, tuple))
        and bool(solution)
        and (dimension is None or len(solution) == dimension)
        and all(
            not isinstance(value, bool)
            and isinstance(value, (int, float))
            and math.isfinite(value)
            for value in solution
        )
    )


def trace_result_issues(
    connection: sqlite3.Connection, run_id: int, objective: float, evaluations: int
) -> list[tuple[str, str, int]]:
    row = connection.execute(
        "SELECT pi.direction,c.config_json FROM runs r "
        "JOIN problem_instances pi ON pi.instance_id=r.instance_id "
        "JOIN campaigns c ON c.campaign_id=r.campaign_id WHERE r.run_id=?",
        (run_id,),
    ).fetchone()
    points = connection.execute(
        "SELECT tp.*,tm.value_real AS objective FROM trace_points tp "
        "LEFT JOIN trace_metric_values tm ON tm.run_id=tp.run_id "
        "AND tm.checkpoint_index=tp.checkpoint_index AND tm.metric_id='objective_best' "
        "WHERE tp.run_id=? ORDER BY tp.checkpoint_index",
        (run_id,),
    ).fetchall()
    issues = []
    previous = None
    for index, point in enumerate(points):
        if point["checkpoint_index"] != index:
            issues.append(
                ("trace_sequence", "Trace checkpoints must be contiguous", run_id)
            )
        if point["evaluations"] > evaluations or (
            index and point["evaluations"] < points[index - 1]["evaluations"]
        ):
            issues.append(
                (
                    "trace_nfe_order",
                    "Trace evaluations exceed result or are not monotonic",
                    run_id,
                )
            )
        value = point["objective"]
        if not isinstance(value, (int, float)) or not math.isfinite(value):
            issues.append(
                (
                    "trace_objective_nonfinite",
                    "Trace objective must be finite and numeric",
                    run_id,
                )
            )
        else:
            if previous is not None and (
                (row["direction"] == "minimize" and value > previous)
                or (row["direction"] == "maximize" and value < previous)
            ):
                issues.append(
                    (
                        "trace_objective_order",
                        "Trace best-so-far objective worsens",
                        run_id,
                    )
                )
            previous = value
    trace = json.loads(row["config_json"]).get("trace", {})
    if isinstance(trace, Mapping) and trace.get("enabled") is True:
        if not points or points[-1]["evaluations"] != evaluations:
            issues.append(
                (
                    "missing_final_trace",
                    "Enabled trace must reach final evaluation budget",
                    run_id,
                )
            )
    if points and points[-1]["evaluations"] != evaluations:
        issues.append(
            ("final_trace_nfe_mismatch", "Final trace NFE differs from result", run_id)
        )
    if (
        points
        and points[-1]["evaluations"] == evaluations
        and points[-1]["objective"] is not None
    ):
        if points[-1]["objective"] != objective:
            issues.append(
                (
                    "final_trace_objective_mismatch",
                    "Final trace objective differs from result",
                    run_id,
                )
            )
    return issues


def run_evidence_issues(
    connection: sqlite3.Connection, campaign_id: str
) -> list[tuple[str, str, int]]:
    issues = []
    selected = {
        row[0]
        for row in connection.execute(
            "SELECT metric_id FROM campaign_metrics WHERE campaign_id=?", (campaign_id,)
        )
    }
    for run in connection.execute(
        "SELECT * FROM runs WHERE campaign_id=? AND status='completed'", (campaign_id,)
    ):
        run_id = int(run["run_id"])
        state = run["finalization_status"]
        if state in {"pending", "failed"}:
            issues.append(
                (f"run_finalization_{state}", f"Run finalization is {state}", run_id)
            )
        observed = {
            row[0]
            for row in connection.execute(
                "SELECT metric_id FROM run_metric_values WHERE run_id=?", (run_id,)
            )
        }
        missing = (selected & POST_RUN_TIMING_METRICS) - observed
        if missing:
            issues.append(
                (
                    "missing_post_run_timing",
                    "Missing selected post-run timing: " + ", ".join(sorted(missing)),
                    run_id,
                )
            )
        timings = dict(
            connection.execute(
                "SELECT metric_id,value_real FROM run_metric_values "
                "WHERE run_id=? AND metric_id IN ('persistence_total_seconds','run_wall_total_seconds')",
                (run_id,),
            )
        )
        if any(
            not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0
            for value in timings.values()
        ):
            issues.append(
                (
                    "invalid_post_run_timing",
                    "Post-run timings must be finite and non-negative",
                    run_id,
                )
            )
        elif timings.get("persistence_total_seconds", 0) > timings.get(
            "run_wall_total_seconds", math.inf
        ):
            issues.append(
                (
                    "invalid_post_run_timing",
                    "Persistence time exceeds run wall time",
                    run_id,
                )
            )
        dimension = connection.execute(
            "SELECT dimension FROM problem_instances WHERE instance_id=?",
            (run["instance_id"],),
        ).fetchone()[0]
        try:
            solution = (
                json.loads(run["solution_json"]) if run["solution_json"] else None
            )
        except (ValueError, TypeError):
            solution = None
        if not valid_solution(solution, dimension):
            issues.append(
                (
                    "invalid_completed_solution",
                    "Completed solution must be finite and match dimension",
                    run_id,
                )
            )
        objective_metric = connection.execute(
            "SELECT value_real FROM run_metric_values WHERE run_id=? AND metric_id='objective_best'",
            (run_id,),
        ).fetchone()
        if (
            objective_metric is not None
            and objective_metric[0] != run["objective_best"]
        ):
            issues.append(
                (
                    "result_objective_mismatch",
                    "Objective observation differs from result",
                    run_id,
                )
            )
        if run["objective_best"] is not None and run["evaluations"] is not None:
            issues.extend(
                trace_result_issues(
                    connection, run_id, run["objective_best"], run["evaluations"]
                )
            )
    return issues
