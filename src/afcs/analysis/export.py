"""Read-only, provenance-preserving CSV exports for v2 campaigns."""

from __future__ import annotations

import csv
import json
import os
import sqlite3
import tempfile
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Generator

from afcs.persistence.database import validate_current_schema
from afcs.persistence.metric_contracts import metric_evidence_issues
from afcs.persistence.run_contracts import run_evidence_issues

RUN_COLUMNS = (
    "campaign_id",
    "campaign_name",
    "campaign_status",
    "campaign_config_json",
    "campaign_config_sha256",
    "code_commit",
    "metric_registry_version",
    "schema_version",
    "campaign_created_at",
    "base_seed",
    "seed_protocol",
    "rng_engine",
    "configuration_id",
    "configuration_key",
    "algorithm",
    "optimizer_version",
    "algorithm_parameters_json",
    "parameters_sha256",
    "budget_type",
    "budget_evaluations",
    "budget_iterations",
    "population_size",
    "instance_id",
    "problem_family",
    "instance",
    "dimension",
    "optimum",
    "direction",
    "problem_parameters_json",
    "data_sha256",
    "run_id",
    "replica_index",
    "random_seed",
    "initial_population_sha256",
    "initial_velocity_sha256",
    "initial_state_hash_version",
    "run_status",
    "started_at",
    "finished_at",
    "objective_best",
    "solution_json",
    "evaluations",
    "runtime_total_seconds",
    "feasible",
    "constraint_violation",
    "error_type",
    "error_message",
    "failure_phase",
    "finalization_status",
    "finalization_error_type",
    "finalization_error_message",
)

TRACE_COLUMNS = (
    "campaign_id",
    "configuration_id",
    "configuration_key",
    "algorithm",
    "optimizer_version",
    "instance_id",
    "problem_family",
    "instance",
    "dimension",
    "run_id",
    "replica_index",
    "random_seed",
    "run_status",
    "checkpoint_index",
    "iteration_index",
    "evaluations",
    "elapsed_seconds",
)

VALUE_COLUMNS = ("value_real", "value_integer", "value_text", "value_json")


class AnalysisExportError(ValueError):
    """Raised when a campaign cannot be exported as a canonical dataset."""


@dataclass(frozen=True, slots=True)
class CampaignExportSummary:
    """Counts of rows and columns written by :func:`export_campaign_csv`."""

    run_rows: int
    trace_rows: int
    run_columns: tuple[str, ...]
    trace_columns: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class CsvMismatch:
    kind: str
    csv_line: int | None
    column: str | None
    expected: str | None
    actual: str | None


@dataclass(frozen=True, slots=True)
class CsvReconciliation:
    dataset: str
    path: str
    expected_columns: tuple[str, ...]
    actual_columns: tuple[str, ...]
    expected_row_count: int
    actual_row_count: int | None
    mismatch_count: int
    mismatches: tuple[CsvMismatch, ...]
    examples_truncated: bool

    @property
    def matches(self) -> bool:
        return self.mismatch_count == 0


@dataclass(frozen=True, slots=True)
class CampaignCsvReconciliation:
    campaign_id: str
    runs: CsvReconciliation
    traces: CsvReconciliation

    @property
    def reconciled(self) -> bool:
        return self.runs.matches and self.traces.matches


_MAX_RECONCILIATION_EXAMPLES = 50


@contextmanager
def _read_snapshot(connection: sqlite3.Connection) -> Generator[None, None, None]:
    validate_current_schema(connection)
    owns_transaction = not connection.in_transaction
    if owns_transaction:
        connection.execute("BEGIN")
    try:
        yield
    finally:
        if owns_transaction and connection.in_transaction:
            connection.rollback()


def _query_rows(
    connection: sqlite3.Connection, query: str, parameters: tuple[Any, ...] = ()
) -> list[dict[str, Any]]:
    cursor = connection.execute(query, parameters)
    columns = tuple(column[0] for column in cursor.description or ())
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def _metric_value(row: dict[str, Any], dtype: str) -> Any:
    for column in VALUE_COLUMNS:
        value = row[column]
        if value is not None:
            if column == "value_integer" and dtype == "boolean":
                return bool(value)
            return value
    raise AnalysisExportError(f"Metric {row['metric_id']!r} has no stored value")


def _metric_columns(metric_ids: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(
        column
        for metric_id in metric_ids
        for column in (f"metric__{metric_id}", f"provenance__{metric_id}")
    )


def _csv_value(value: Any) -> Any:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    return value


def _write_csv(
    path: Path, columns: tuple[str, ...], rows: list[dict[str, Any]]
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=columns, extrasaction="raise")
        writer.writeheader()
        writer.writerows(
            {column: _csv_value(row.get(column)) for column in columns} for row in rows
        )


def _read_csv_matrix(path: Path) -> tuple[tuple[str, ...], list[list[str]]]:
    try:
        with path.open(newline="", encoding="utf-8") as file:
            rows = list(csv.reader(file))
    except (OSError, UnicodeError, csv.Error) as error:
        raise AnalysisExportError(f"Could not read CSV {path}: {error}") from error
    if not rows:
        return (), []
    return tuple(rows[0]), rows[1:]


def _reconcile_csv(
    dataset: str,
    expected_path: Path,
    actual_path: str | Path,
) -> CsvReconciliation:
    expected_columns, expected_rows = _read_csv_matrix(expected_path)
    path = Path(actual_path)
    mismatches: list[CsvMismatch] = []
    mismatch_count = 0

    def record(
        kind: str,
        csv_line: int | None = None,
        column: str | None = None,
        expected: str | None = None,
        actual: str | None = None,
    ) -> None:
        nonlocal mismatch_count
        mismatch_count += 1
        if len(mismatches) < _MAX_RECONCILIATION_EXAMPLES:
            mismatches.append(CsvMismatch(kind, csv_line, column, expected, actual))

    if not path.is_file():
        record("file_missing", expected=str(path), actual=None)
        return CsvReconciliation(
            dataset=dataset,
            path=str(path),
            expected_columns=expected_columns,
            actual_columns=(),
            expected_row_count=len(expected_rows),
            actual_row_count=None,
            mismatch_count=mismatch_count,
            mismatches=tuple(mismatches),
            examples_truncated=False,
        )

    actual_columns, actual_rows = _read_csv_matrix(path)
    if actual_columns != expected_columns:
        record(
            "header",
            expected=json.dumps(expected_columns),
            actual=json.dumps(actual_columns),
        )
    if len(expected_rows) != len(actual_rows):
        record(
            "row_count",
            expected=str(len(expected_rows)),
            actual=str(len(actual_rows)),
        )
    if actual_columns == expected_columns:
        for row_index in range(max(len(expected_rows), len(actual_rows))):
            csv_line = row_index + 2
            if row_index >= len(expected_rows):
                record("row_extra", csv_line, expected=None, actual="present")
                continue
            if row_index >= len(actual_rows):
                record("row_missing", csv_line, expected="present", actual=None)
                continue

            expected_row = expected_rows[row_index]
            actual_row = actual_rows[row_index]
            if len(expected_row) != len(actual_row):
                record(
                    "row_width",
                    csv_line,
                    expected=str(len(expected_row)),
                    actual=str(len(actual_row)),
                )
            for column_index, (expected, actual) in enumerate(
                zip(expected_row, actual_row)
            ):
                if expected != actual:
                    record(
                        "cell_value",
                        csv_line,
                        expected_columns[column_index],
                        expected,
                        actual,
                    )

    return CsvReconciliation(
        dataset=dataset,
        path=str(path),
        expected_columns=expected_columns,
        actual_columns=actual_columns,
        expected_row_count=len(expected_rows),
        actual_row_count=len(actual_rows),
        mismatch_count=mismatch_count,
        mismatches=tuple(mismatches),
        examples_truncated=mismatch_count > len(mismatches),
    )


def _reconcile_campaign_csv(
    connection: sqlite3.Connection,
    campaign_id: str,
    runs_path: str | Path,
    traces_path: str | Path,
    expected_directory: Path,
) -> CampaignCsvReconciliation:
    expected_runs = expected_directory / "runs.csv"
    expected_traces = expected_directory / "traces.csv"
    export_campaign_csv(connection, campaign_id, expected_runs, expected_traces)
    return CampaignCsvReconciliation(
        campaign_id=campaign_id,
        runs=_reconcile_csv("runs", expected_runs, runs_path),
        traces=_reconcile_csv("traces", expected_traces, traces_path),
    )


def reconcile_campaign_csv(
    connection: sqlite3.Connection,
    campaign_id: str,
    runs_path: str | Path,
    traces_path: str | Path,
) -> CampaignCsvReconciliation:
    """Compare supplied run and trace CSVs with a fresh SQLite projection.

    The database is read-only for this operation. Temporary canonical exports
    are removed before returning. Mismatch examples are capped at 50 per file;
    ``mismatch_count`` still reports the full number of detected differences.
    """

    with tempfile.TemporaryDirectory(prefix="afcs-reconcile-") as directory:
        return _reconcile_campaign_csv(
            connection,
            campaign_id,
            runs_path,
            traces_path,
            Path(directory),
        )


def load_reconciled_run_rows(
    connection: sqlite3.Connection,
    campaign_id: str,
    runs_path: str | Path,
    traces_path: str | Path,
) -> tuple[dict[str, Any], ...]:
    """Return canonical run rows only when both supplied CSVs reconcile.

    Rows are read from the temporary SQLite projection that was compared with
    the supplied files, avoiding downstream use of unverified CSV contents.
    """

    rows, _, _ = load_reconciled_campaign_data(
        connection, campaign_id, runs_path, traces_path
    )
    return rows


def load_reconciled_campaign_data(
    connection: sqlite3.Connection,
    campaign_id: str,
    runs_path: str | Path,
    traces_path: str | Path,
) -> tuple[
    tuple[dict[str, Any], ...],
    tuple[dict[str, Any], ...],
    CampaignCsvReconciliation,
]:
    """Load canonical run/trace rows and reconciliation from one snapshot."""

    with tempfile.TemporaryDirectory(prefix="afcs-reconcile-") as directory:
        expected_runs = Path(directory) / "runs.csv"
        expected_traces = Path(directory) / "traces.csv"
        reconciliation = _reconcile_campaign_csv(
            connection,
            campaign_id,
            runs_path,
            traces_path,
            Path(directory),
        )
        if not reconciliation.reconciled:
            raise AnalysisExportError(
                f"Campaign {campaign_id!r} exports do not reconcile: "
                f"runs={reconciliation.runs.mismatch_count} mismatch(es), "
                f"traces={reconciliation.traces.mismatch_count} mismatch(es)"
            )
        try:
            with expected_runs.open(newline="", encoding="utf-8") as file:
                run_rows = tuple(dict(row) for row in csv.DictReader(file))
            with expected_traces.open(newline="", encoding="utf-8") as file:
                trace_rows = tuple(dict(row) for row in csv.DictReader(file))
            return run_rows, trace_rows, reconciliation
        except (OSError, UnicodeError, csv.Error) as error:
            raise AnalysisExportError(
                f"Could not load canonical run rows for campaign "
                f"{campaign_id!r}: {error}"
            ) from error


def export_campaign_csv(
    connection: sqlite3.Connection,
    campaign_id: str,
    runs_path: str | Path,
    traces_path: str | Path,
) -> CampaignExportSummary:
    """Export a campaign's run and trace records to two deterministic CSV files.

    Each metric is exported into a ``metric__<id>`` column with a paired
    ``provenance__<id>`` column. The metric columns are determined by the
    campaign's immutable metric selection and definitions. All run statuses
    are included; callers can explicitly select completed runs for summaries.
    """

    runs_file = Path(runs_path)
    traces_file = Path(traces_path)
    if os.path.normcase(str(runs_file.resolve())) == os.path.normcase(
        str(traces_file.resolve())
    ):
        raise AnalysisExportError("Run and trace exports must use different paths")

    with _read_snapshot(connection):
        issues = metric_evidence_issues(connection, campaign_id) + run_evidence_issues(
            connection, campaign_id
        )
        if issues:
            raise AnalysisExportError(
                "Invalid metric evidence: "
                + "; ".join(f"{code}: {message}" for code, message, _ in issues)
            )
        campaign_rows = _query_rows(
            connection,
            "SELECT campaign_id FROM campaigns WHERE campaign_id = ?",
            (campaign_id,),
        )
        if not campaign_rows:
            raise AnalysisExportError(f"Unknown campaign: {campaign_id!r}")

        metric_rows = _query_rows(
            connection,
            """
            SELECT cm.metric_id, md.definition_json
            FROM campaign_metrics AS cm
            JOIN metric_definitions AS md
              ON md.metric_id = cm.metric_id
             AND md.metric_version = cm.metric_version
            WHERE cm.campaign_id = ?
            ORDER BY cm.metric_id
            """,
            (campaign_id,),
        )
        metric_specs: dict[str, tuple[tuple[str, ...], str]] = {}
        for row in metric_rows:
            definition = json.loads(row["definition_json"])
            scope = definition.get("scope")
            dtype = definition.get("dtype")
            if (
                not isinstance(scope, list)
                or not all(isinstance(item, str) for item in scope)
                or not isinstance(dtype, str)
            ):
                raise AnalysisExportError(
                    f"Invalid persisted definition for metric {row['metric_id']!r}"
                )
            metric_specs[row["metric_id"]] = (tuple(scope), dtype)

        run_metric_ids = tuple(
            metric_id
            for metric_id, (scope, _) in metric_specs.items()
            if "replica" in scope
        )
        trace_metric_ids = tuple(
            metric_id
            for metric_id, (scope, _) in metric_specs.items()
            if "iteration" in scope
        )

        run_rows = _query_rows(
            connection,
            """
            SELECT
                c.campaign_id,
                c.name AS campaign_name,
                c.status AS campaign_status,
                c.config_json AS campaign_config_json,
                c.config_sha256 AS campaign_config_sha256,
                c.code_commit,
                c.metric_registry_version,
                c.schema_version,
                c.created_at AS campaign_created_at,
                c.base_seed,
                c.seed_protocol,
                c.rng_engine,
                COALESCE(ac.treatment_id, ac.configuration_id) AS configuration_id,
                ac.configuration_id AS configuration_key,
                ac.algorithm,
                ac.optimizer_version,
                ac.parameters_json AS algorithm_parameters_json,
                ac.parameters_sha256,
                ac.budget_type,
                ac.budget_evaluations,
                ac.budget_iterations,
                ac.population_size,
                pi.instance_id,
                pi.problem_family,
                pi.name AS instance,
                pi.dimension,
                pi.optimum,
                pi.direction,
                pi.parameters_json AS problem_parameters_json,
                pi.data_sha256,
                r.run_id,
                r.replica_index,
                r.random_seed,
                r.initial_population_sha256,
                r.initial_velocity_sha256,
                r.initial_state_hash_version,
                r.status AS run_status,
                r.started_at,
                r.finished_at,
                r.objective_best,
                r.solution_json,
                r.evaluations,
                r.runtime_total_seconds,
                r.feasible,
                r.constraint_violation,
                r.error_type,
                r.error_message,
                r.failure_phase,
                r.finalization_status,
                r.finalization_error_type,
                r.finalization_error_message
            FROM runs AS r
            JOIN campaigns AS c ON c.campaign_id = r.campaign_id
            JOIN algorithm_configurations AS ac
              ON ac.configuration_id = r.configuration_id
             AND ac.campaign_id = r.campaign_id
            JOIN problem_instances AS pi ON pi.instance_id = r.instance_id
            WHERE r.campaign_id = ?
            ORDER BY ac.configuration_id, pi.instance_id, r.replica_index, r.run_id
            """,
            (campaign_id,),
        )

        run_metric_rows = _query_rows(
            connection,
            """
            SELECT rmv.run_id, rmv.metric_id, rmv.provenance,
                   rmv.value_real, rmv.value_integer,
                   rmv.value_text, rmv.value_json
            FROM run_metric_values AS rmv
            JOIN runs AS r ON r.run_id = rmv.run_id
            WHERE r.campaign_id = ?
            ORDER BY rmv.run_id, rmv.metric_id
            """,
            (campaign_id,),
        )

        trace_rows = _query_rows(
            connection,
            """
            SELECT
                c.campaign_id,
                COALESCE(ac.treatment_id, ac.configuration_id) AS configuration_id,
                ac.configuration_id AS configuration_key,
                ac.algorithm,
                ac.optimizer_version,
                pi.instance_id,
                pi.problem_family,
                pi.name AS instance,
                pi.dimension,
                r.run_id,
                r.replica_index,
                r.random_seed,
                r.status AS run_status,
                tp.checkpoint_index,
                tp.iteration_index,
                tp.evaluations,
                tp.elapsed_seconds
            FROM trace_points AS tp
            JOIN runs AS r ON r.run_id = tp.run_id
            JOIN campaigns AS c ON c.campaign_id = r.campaign_id
            JOIN algorithm_configurations AS ac
              ON ac.configuration_id = r.configuration_id
             AND ac.campaign_id = r.campaign_id
            JOIN problem_instances AS pi ON pi.instance_id = r.instance_id
            WHERE r.campaign_id = ?
            ORDER BY r.run_id, tp.checkpoint_index
            """,
            (campaign_id,),
        )

        trace_metric_rows = _query_rows(
            connection,
            """
            SELECT tmv.run_id, tmv.checkpoint_index, tmv.metric_id,
                   tmv.provenance, tmv.value_real, tmv.value_integer,
                   tmv.value_text, tmv.value_json
            FROM trace_metric_values AS tmv
            JOIN runs AS r ON r.run_id = tmv.run_id
            WHERE r.campaign_id = ?
            ORDER BY tmv.run_id, tmv.checkpoint_index, tmv.metric_id
            """,
            (campaign_id,),
        )

    run_metrics: dict[int, dict[str, dict[str, Any]]] = {}
    for row in run_metric_rows:
        metric_id = row["metric_id"]
        spec = metric_specs.get(metric_id)
        if spec is None or "replica" not in spec[0]:
            raise AnalysisExportError(
                f"Run {row['run_id']} contains unselected metric {metric_id!r}"
            )
        run_metrics.setdefault(row["run_id"], {})[metric_id] = {
            "value": _metric_value(row, spec[1]),
            "provenance": row["provenance"],
        }

    trace_metrics: dict[tuple[int, int], dict[str, dict[str, Any]]] = {}
    for row in trace_metric_rows:
        metric_id = row["metric_id"]
        spec = metric_specs.get(metric_id)
        if spec is None or "iteration" not in spec[0]:
            raise AnalysisExportError(
                f"Run {row['run_id']} contains unselected trace metric {metric_id!r}"
            )
        key = (row["run_id"], row["checkpoint_index"])
        trace_metrics.setdefault(key, {})[metric_id] = {
            "value": _metric_value(row, spec[1]),
            "provenance": row["provenance"],
        }

    run_columns = RUN_COLUMNS + _metric_columns(run_metric_ids)
    trace_columns = TRACE_COLUMNS + _metric_columns(trace_metric_ids)

    for row in run_rows:
        row["feasible"] = None if row["feasible"] is None else bool(row["feasible"])
        for metric_id in run_metric_ids:
            metric = run_metrics.get(row["run_id"], {}).get(metric_id, {})
            row[f"metric__{metric_id}"] = metric.get("value")
            row[f"provenance__{metric_id}"] = metric.get("provenance")

    for row in trace_rows:
        metrics = trace_metrics.get((row["run_id"], row["checkpoint_index"]), {})
        for metric_id in trace_metric_ids:
            metric = metrics.get(metric_id, {})
            row[f"metric__{metric_id}"] = metric.get("value")
            row[f"provenance__{metric_id}"] = metric.get("provenance")

    _write_csv(runs_file, run_columns, run_rows)
    _write_csv(traces_file, trace_columns, trace_rows)
    return CampaignExportSummary(
        run_rows=len(run_rows),
        trace_rows=len(trace_rows),
        run_columns=run_columns,
        trace_columns=trace_columns,
    )
