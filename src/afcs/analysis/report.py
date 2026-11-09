"""Reconciled, reproducible campaign analysis reports."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import os
import sqlite3
import tempfile
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .export import (
    AnalysisExportError,
    CsvReconciliation,
    _reconcile_csv,
    export_campaign_csv,
    load_reconciled_campaign_data,
)
from .statistics import (
    AggregateObjectiveRank,
    AnalysisError,
    ConvergenceCoverage,
    ConvergenceSummary,
    FriedmanPostHocResult,
    FriedmanResult,
    InstanceIdentity,
    ObjectiveSummary,
    aggregate_objective_ranks,
    friedman_objective_test,
    friedman_posthoc_objective_tests,
    summarize_convergence,
    summarize_objectives,
)

ANALYSIS_REPORT_SCHEMA_VERSION = 4
ANALYSIS_TABLES_SCHEMA_VERSION = 4
ANALYSIS_FIGURES_SCHEMA_VERSION = 4
_FIGURE_FILENAMES = (
    "aggregate_mean_ranks.png",
    "friedman_mean_ranks.png",
    "convergence_curves.png",
)
_TABLE_COLUMNS = {
    "run_status_counts.csv": ("campaign_id", "run_status", "run_count"),
    "objective_summaries.csv": (
        "campaign_id",
        "instance_identity_json",
        "problem_family",
        "instance",
        "dimension",
        "direction",
        "configuration_id",
        "algorithm",
        "optimizer_version",
        "run_count",
        "completed_count",
        "status_counts_json",
        "objective_provenance_counts_json",
        "mean",
        "sample_std",
        "median",
        "q25",
        "q75",
        "minimum",
        "maximum",
    ),
    "convergence_summaries.csv": (
        "campaign_id",
        "instance_identity_json",
        "problem_family",
        "instance",
        "dimension",
        "direction",
        "configuration_id",
        "algorithm",
        "optimizer_version",
        "evaluations",
        "checkpoint_count",
        "median_objective",
        "q25_objective",
        "q75_objective",
        "observed_value_count",
        "reconstructed_value_count",
        "expected_value_count",
        "provenance_counts_json",
    ),
    "convergence_coverage.csv": (
        "campaign_id",
        "instance_identity_json",
        "problem_family",
        "instance",
        "dimension",
        "configuration_id",
        "completed_run_count",
        "completed_runs_with_trace",
        "completed_runs_without_trace",
        "noncompleted_runs_with_trace",
        "completed_trace_points_without_objective",
    ),
    "aggregate_ranks.csv": (
        "campaign_id",
        "configuration_id",
        "algorithm",
        "optimizer_version",
        "instances_ranked",
        "total_instances",
        "ranked_instances_json",
        "available_instances_json",
        "mean_rank",
        "median_rank",
        "unique_best_count",
        "tied_best_count",
        "worst_count",
    ),
    "friedman_results.csv": (
        "campaign_id",
        "problem_family",
        "configurations_json",
        "included_instances_json",
        "excluded_instances_json",
        "block_count",
        "incomplete_block_count",
        "statistic",
        "p_value",
        "kendall_w",
        "ties_present",
        "average_ranks_json",
        "alpha",
        "reject_null",
        "test",
        "p_value_method",
        "p_value_approximation_recommended",
        "scipy_version",
    ),
    "friedman_posthoc.csv": (
        "campaign_id",
        "problem_family",
        "baseline_configuration_id",
        "candidate_configuration_id",
        "omnibus_p_value",
        "omnibus_reject_null",
        "omnibus_p_value_approximation_recommended",
        "paired_instance_count",
        "status",
        "family_id",
        "family_size",
        "alpha",
        "mean_rank_difference",
        "studentized_range_statistic",
        "p_value",
        "reject_null",
        "p_value_method",
        "scipy_version",
    ),
    "skipped_friedman_families.csv": (
        "campaign_id",
        "problem_family",
        "configuration_count",
        "status",
    ),
}


@dataclass(frozen=True, slots=True)
class SkippedFriedmanFamily:
    problem_family: str
    configuration_count: int
    status: str


@dataclass(frozen=True, slots=True)
class CampaignAnalysisReport:
    schema_version: int
    campaign_id: str
    alpha: float
    run_row_count: int
    trace_row_count: int
    run_status_counts: tuple[tuple[str, int], ...]
    objective_summaries: tuple[ObjectiveSummary, ...]
    convergence_summaries: tuple[ConvergenceSummary, ...]
    convergence_coverage: tuple[ConvergenceCoverage, ...]
    aggregate_ranks: tuple[AggregateObjectiveRank, ...]
    friedman_results: tuple[FriedmanResult, ...]
    friedman_posthoc_results: tuple[FriedmanPostHocResult, ...]
    skipped_friedman_families: tuple[SkippedFriedmanFamily, ...]


@dataclass(frozen=True, slots=True)
class AnalysisReportReconciliation:
    path: str
    matches: bool
    mismatch_kind: str | None
    expected_sha256: str
    actual_sha256: str | None


@dataclass(frozen=True, slots=True)
class CampaignAnalysisTablesExport:
    campaign_id: str
    directory: str
    files: tuple[str, ...]
    row_counts: tuple[tuple[str, int], ...]
    manifest_path: str


@dataclass(frozen=True, slots=True)
class CampaignAnalysisTablesReconciliation:
    campaign_id: str
    tables: tuple[CsvReconciliation, ...]
    manifest_path: str
    manifest_matches: bool
    manifest_mismatch_kind: str | None
    expected_manifest_sha256: str
    actual_manifest_sha256: str | None

    @property
    def matches(self) -> bool:
        return self.manifest_matches and all(table.matches for table in self.tables)


@dataclass(frozen=True, slots=True)
class CampaignAnalysisFiguresExport:
    campaign_id: str
    directory: str
    files: tuple[str, ...]
    manifest_path: str
    matplotlib_version: str


@dataclass(frozen=True, slots=True)
class FigureArtifactReconciliation:
    filename: str
    path: str
    matches: bool
    expected_sha256: str
    actual_sha256: str | None
    mismatch_kind: str | None


@dataclass(frozen=True, slots=True)
class CampaignAnalysisFiguresReconciliation:
    campaign_id: str
    figures: tuple[FigureArtifactReconciliation, ...]
    manifest_path: str
    manifest_matches: bool
    manifest_mismatch_kind: str | None
    expected_manifest_sha256: str
    actual_manifest_sha256: str | None

    @property
    def matches(self) -> bool:
        return self.manifest_matches and all(figure.matches for figure in self.figures)


@dataclass(frozen=True, slots=True)
class CampaignAnalysisPipelineResult:
    campaign_id: str
    output_directory: str
    run_row_count: int
    trace_row_count: int
    report_path: str
    tables_directory: str
    figures_directory: str


def build_campaign_analysis_report(
    connection: sqlite3.Connection,
    campaign_id: str,
    runs_path: str | Path,
    traces_path: str | Path,
    alpha: float = 0.05,
) -> CampaignAnalysisReport:
    """Analyze canonical SQLite run rows after both exports reconcile."""

    if not math.isfinite(alpha) or alpha <= 0 or alpha >= 1:
        raise AnalysisError("alpha must be finite and strictly between 0 and 1")
    run_rows, trace_rows, reconciliation = load_reconciled_campaign_data(
        connection, campaign_id, runs_path, traces_path
    )
    _validate_objective_provenance(run_rows, trace_rows)
    run_status_counts = Counter(str(row.get("run_status", "")) for row in run_rows)
    summaries = summarize_objectives(run_rows)
    convergence, convergence_coverage = summarize_convergence(run_rows, trace_rows)
    ranks = aggregate_objective_ranks(run_rows)

    configurations_by_family: dict[str, set[str]] = defaultdict(set)
    rows_by_family: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in run_rows:
        family = row.get("problem_family")
        configuration_id = row.get("configuration_id")
        if not isinstance(family, str) or not family:
            raise AnalysisExportError("Canonical run row is missing a problem family")
        if not isinstance(configuration_id, str) or not configuration_id:
            raise AnalysisExportError("Canonical run row is missing a configuration ID")
        configurations_by_family[family].add(configuration_id)
        rows_by_family[family].append(row)

    friedman_results: list[FriedmanResult] = []
    posthoc_results: list[FriedmanPostHocResult] = []
    skipped_families: list[SkippedFriedmanFamily] = []
    for family in sorted(configurations_by_family):
        configuration_count = len(configurations_by_family[family])
        if configuration_count < 3:
            skipped_families.append(
                SkippedFriedmanFamily(
                    problem_family=family,
                    configuration_count=configuration_count,
                    status="fewer_than_three_configurations",
                )
            )
            continue
        family_rows = rows_by_family[family]
        family_friedman = friedman_objective_test(family_rows, alpha)
        friedman_results.extend(family_friedman)
        posthoc_results.extend(friedman_posthoc_objective_tests(family_rows, alpha))

    return CampaignAnalysisReport(
        schema_version=ANALYSIS_REPORT_SCHEMA_VERSION,
        campaign_id=campaign_id,
        alpha=alpha,
        run_row_count=len(run_rows),
        trace_row_count=reconciliation.traces.expected_row_count,
        run_status_counts=tuple(sorted(run_status_counts.items())),
        objective_summaries=summaries,
        convergence_summaries=convergence,
        convergence_coverage=convergence_coverage,
        aggregate_ranks=ranks,
        friedman_results=tuple(friedman_results),
        friedman_posthoc_results=tuple(posthoc_results),
        skipped_friedman_families=tuple(skipped_families),
    )


def _validate_objective_provenance(
    run_rows: tuple[dict[str, Any], ...],
    trace_rows: tuple[dict[str, Any], ...],
) -> None:
    allowed_provenance = {"observed", "reconstructed", "expected"}
    for row in run_rows:
        if row.get("run_status") != "completed":
            continue
        metric_value = row.get("metric__objective_best")
        provenance = row.get("provenance__objective_best")
        if not isinstance(provenance, str) or provenance not in allowed_provenance:
            raise AnalysisExportError(
                f"Completed run {row.get('run_id')!r} is missing valid "
                "objective_best provenance"
            )
        try:
            if metric_value is None or row.get("objective_best") is None:
                raise TypeError("objective_best cannot be None")
            metric_objective = float(metric_value)
            run_objective = float(row["objective_best"])
        except (TypeError, ValueError) as error:
            raise AnalysisExportError(
                f"Completed run {row.get('run_id')!r} has no numeric "
                "objective_best metric value"
            ) from error
        if (
            not math.isfinite(metric_objective)
            or not math.isfinite(run_objective)
            or metric_objective != run_objective
        ):
            raise AnalysisExportError(
                f"Completed run {row.get('run_id')!r} has inconsistent "
                "objective_best values in its run and metric records"
            )

    for row in trace_rows:
        if row.get("run_status") != "completed":
            continue
        metric_value = row.get("metric__objective_best")
        if metric_value in (None, ""):
            continue
        provenance = row.get("provenance__objective_best")
        if not isinstance(provenance, str) or provenance not in allowed_provenance:
            raise AnalysisExportError(
                f"Completed trace point for run {row.get('run_id')!r} is "
                "missing valid objective_best provenance"
            )


def _report_json(report: CampaignAnalysisReport) -> str:
    try:
        return (
            json.dumps(
                asdict(report),
                ensure_ascii=False,
                allow_nan=False,
                indent=2,
                sort_keys=True,
            )
            + "\n"
        )
    except (TypeError, ValueError) as error:
        raise AnalysisExportError(
            f"Campaign {report.campaign_id!r} report is not valid JSON: {error}"
        ) from error


def _json_value(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
    )


def _table_value(value: Any) -> Any:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    return value


def _analysis_table_rows(
    report: CampaignAnalysisReport,
) -> dict[str, list[dict[str, Any]]]:
    tables: dict[str, list[dict[str, Any]]] = {
        "run_status_counts.csv": [
            {
                "campaign_id": report.campaign_id,
                "run_status": status,
                "run_count": count,
            }
            for status, count in report.run_status_counts
        ],
        "objective_summaries.csv": [],
        "convergence_summaries.csv": [
            asdict(result) for result in report.convergence_summaries
        ],
        "convergence_coverage.csv": [
            asdict(result) for result in report.convergence_coverage
        ],
        "aggregate_ranks.csv": [asdict(result) for result in report.aggregate_ranks],
        "friedman_results.csv": [],
        "friedman_posthoc.csv": [
            asdict(result) for result in report.friedman_posthoc_results
        ],
        "skipped_friedman_families.csv": [
            {
                "campaign_id": report.campaign_id,
                **asdict(result),
            }
            for result in report.skipped_friedman_families
        ],
    }

    for summary in report.objective_summaries:
        row = asdict(summary)
        row["status_counts_json"] = _json_value(row.pop("status_counts"))
        row["objective_provenance_counts_json"] = _json_value(
            row.pop("objective_provenance_counts")
        )
        tables["objective_summaries.csv"].append(row)

    for row in tables["convergence_summaries.csv"]:
        row["provenance_counts_json"] = _json_value(row.pop("provenance_counts"))

    for result in report.friedman_results:
        row = asdict(result)
        row["configurations_json"] = _json_value(row.pop("configurations"))
        row["included_instances_json"] = _json_value(row.pop("included_instances"))
        row["excluded_instances_json"] = _json_value(row.pop("excluded_instances"))
        row["average_ranks_json"] = _json_value(row.pop("average_ranks"))
        tables["friedman_results.csv"].append(row)

    for row in tables["aggregate_ranks.csv"]:
        row["ranked_instances_json"] = _json_value(row.pop("ranked_instances"))
        row["available_instances_json"] = _json_value(row.pop("available_instances"))

    for name in (
        "objective_summaries.csv",
        "convergence_summaries.csv",
        "convergence_coverage.csv",
    ):
        for row in tables[name]:
            row["instance_identity_json"] = _json_value(row.pop("instance_identity"))

    return tables


def _write_analysis_tables_to_directory(
    report: CampaignAnalysisReport,
    directory: Path,
) -> tuple[tuple[str, int], ...]:
    directory.mkdir(parents=True, exist_ok=True)
    tables = _analysis_table_rows(report)
    row_counts: list[tuple[str, int]] = []
    for filename, columns in _TABLE_COLUMNS.items():
        path = directory / filename
        try:
            with path.open("w", newline="", encoding="utf-8") as file:
                writer = csv.DictWriter(
                    file,
                    fieldnames=columns,
                    extrasaction="raise",
                    lineterminator="\n",
                )
                writer.writeheader()
                writer.writerows(
                    {column: _table_value(row.get(column)) for column in columns}
                    for row in tables[filename]
                )
        except (OSError, csv.Error, TypeError, ValueError) as error:
            raise AnalysisExportError(
                f"Could not generate analysis table {path}: {error}"
            ) from error
        row_counts.append((filename, len(tables[filename])))

    manifest = _analysis_tables_manifest(report, directory, row_counts)
    manifest_path = directory / "manifest.json"
    try:
        manifest_path.write_text(
            json.dumps(
                manifest,
                ensure_ascii=False,
                allow_nan=False,
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
            newline="\n",
        )
    except (OSError, TypeError, ValueError) as error:
        raise AnalysisExportError(
            f"Could not generate analysis tables manifest {manifest_path}: {error}"
        ) from error
    return tuple(row_counts)


def _analysis_tables_manifest(
    report: CampaignAnalysisReport,
    directory: Path,
    row_counts: tuple[tuple[str, int], ...] | list[tuple[str, int]],
) -> dict[str, Any]:
    files: dict[str, dict[str, Any]] = {}
    for filename, row_count in row_counts:
        path = directory / filename
        try:
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
        except OSError as error:
            raise AnalysisExportError(
                f"Could not hash analysis table {path}: {error}"
            ) from error
        files[filename] = {"row_count": row_count, "sha256": digest}
    report_digest = hashlib.sha256(_report_json(report).encode("utf-8")).hexdigest()
    return {
        "schema_version": ANALYSIS_TABLES_SCHEMA_VERSION,
        "campaign_id": report.campaign_id,
        "analysis_report_sha256": report_digest,
        "tables": files,
    }


def write_campaign_analysis_tables(
    report: CampaignAnalysisReport,
    directory: str | Path,
) -> CampaignAnalysisTablesExport:
    """Write all deterministic analysis tables and manifest to a directory."""

    _report_json(report)
    output_directory = Path(directory)
    try:
        output_directory.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(
            prefix=".afcs-analysis-tables-",
            dir=output_directory,
        ) as staged_name:
            staged_directory = Path(staged_name)
            row_counts = _write_analysis_tables_to_directory(report, staged_directory)
            filenames = tuple(_TABLE_COLUMNS)
            for filename in filenames:
                os.replace(
                    staged_directory / filename,
                    output_directory / filename,
                )
            manifest_name = "manifest.json"
            os.replace(
                staged_directory / manifest_name,
                output_directory / manifest_name,
            )
    except OSError as error:
        raise AnalysisExportError(
            f"Could not write campaign analysis tables to {output_directory}: {error}"
        ) from error
    return CampaignAnalysisTablesExport(
        campaign_id=report.campaign_id,
        directory=str(output_directory),
        files=tuple(_TABLE_COLUMNS),
        row_counts=row_counts,
        manifest_path=str(output_directory / "manifest.json"),
    )


def reconcile_campaign_analysis_tables(
    report: CampaignAnalysisReport,
    directory: str | Path,
) -> CampaignAnalysisTablesReconciliation:
    """Compare persisted analysis tables and manifest with a fresh projection."""

    output_directory = Path(directory)
    with tempfile.TemporaryDirectory(prefix="afcs-analysis-tables-") as name:
        expected_directory = Path(name)
        _write_analysis_tables_to_directory(report, expected_directory)
        table_results = tuple(
            _reconcile_csv(
                filename.removesuffix(".csv"),
                expected_directory / filename,
                output_directory / filename,
            )
            for filename in _TABLE_COLUMNS
        )
        expected_manifest_path = expected_directory / "manifest.json"
        actual_manifest_path = output_directory / "manifest.json"
        expected_manifest_text = expected_manifest_path.read_text(encoding="utf-8")
        expected_manifest_hash = hashlib.sha256(
            expected_manifest_text.encode("utf-8")
        ).hexdigest()
        if not actual_manifest_path.is_file():
            return CampaignAnalysisTablesReconciliation(
                campaign_id=report.campaign_id,
                tables=table_results,
                manifest_path=str(actual_manifest_path),
                manifest_matches=False,
                manifest_mismatch_kind="file_missing",
                expected_manifest_sha256=expected_manifest_hash,
                actual_manifest_sha256=None,
            )
        try:
            actual_manifest_text = actual_manifest_path.read_text(encoding="utf-8")
            actual_manifest = json.loads(actual_manifest_text)
        except (OSError, UnicodeError, json.JSONDecodeError) as error:
            if isinstance(error, OSError):
                raise AnalysisExportError(
                    f"Could not read analysis tables manifest "
                    f"{actual_manifest_path}: {error}"
                ) from error
            return CampaignAnalysisTablesReconciliation(
                campaign_id=report.campaign_id,
                tables=table_results,
                manifest_path=str(actual_manifest_path),
                manifest_matches=False,
                manifest_mismatch_kind="invalid_json",
                expected_manifest_sha256=expected_manifest_hash,
                actual_manifest_sha256=None,
            )
        actual_manifest_hash = hashlib.sha256(
            actual_manifest_text.encode("utf-8")
        ).hexdigest()
        matches = actual_manifest == json.loads(expected_manifest_text)
        return CampaignAnalysisTablesReconciliation(
            campaign_id=report.campaign_id,
            tables=table_results,
            manifest_path=str(actual_manifest_path),
            manifest_matches=matches,
            manifest_mismatch_kind=None if matches else "content_mismatch",
            expected_manifest_sha256=expected_manifest_hash,
            actual_manifest_sha256=actual_manifest_hash,
        )


def _render_campaign_analysis_figures(
    report: CampaignAnalysisReport,
    directory: Path,
) -> str:
    try:
        import matplotlib
        from matplotlib.backends.backend_agg import FigureCanvasAgg
        from matplotlib.figure import Figure
    except ImportError as error:
        raise AnalysisExportError(
            "Analysis figures require Matplotlib; install the 'analysis' extra"
        ) from error

    directory.mkdir(parents=True, exist_ok=True)
    figure = Figure(figsize=(10, 5), dpi=160)
    FigureCanvasAgg(figure)
    axis = figure.add_subplot(1, 1, 1)
    ranked = sorted(
        (item for item in report.aggregate_ranks if item.mean_rank is not None),
        key=lambda item: (item.mean_rank, item.configuration_id),
    )
    if ranked:
        labels = [f"{item.algorithm} ({item.configuration_id})" for item in ranked]
        values = [item.mean_rank for item in ranked if item.mean_rank is not None]
        positions = list(range(len(ranked)))
        axis.barh(positions, values, color="#4472C4")
        axis.set_yticks(positions, labels)
        axis.invert_yaxis()
        axis.set_xlabel("Mean within-instance rank (lower is better)")
        axis.set_title("Campaign-wide descriptive aggregate ranks")
        axis.grid(axis="x", linestyle=":", alpha=0.5)
        figure.set_size_inches(10, max(3.2, 0.42 * len(ranked) + 1.5))
    else:
        axis.text(
            0.5,
            0.5,
            "No aggregate rank data available",
            ha="center",
            va="center",
        )
        axis.set_axis_off()
        axis.set_title("Campaign-wide descriptive aggregate ranks")
    try:
        figure.savefig(
            directory / _FIGURE_FILENAMES[0],
            format="png",
            dpi=160,
            bbox_inches="tight",
            metadata={"Software": "AFCS"},
        )
    except OSError as error:
        raise AnalysisExportError(
            f"Could not render analysis figure "
            f"{directory / _FIGURE_FILENAMES[0]}: {error}"
        ) from error
    finally:
        figure.clear()

    figure_height = max(
        3.2,
        sum(
            max(
                2.2,
                0.32 * max(1, len(result.configurations)) + 1.3,
            )
            for result in report.friedman_results
        ),
    )
    figure = Figure(figsize=(10, figure_height), dpi=160)
    FigureCanvasAgg(figure)
    if report.friedman_results:
        for panel_index, result in enumerate(report.friedman_results, start=1):
            axis = figure.add_subplot(len(report.friedman_results), 1, panel_index)
            rank_values = [
                (configuration_id, value)
                for configuration_id, value in result.average_ranks
                if value is not None
            ]
            if not rank_values:
                axis.text(
                    0.5,
                    0.5,
                    "No complete blocks available",
                    ha="center",
                    va="center",
                )
                axis.set_axis_off()
            else:
                labels = [configuration_id for configuration_id, _ in rank_values]
                values = [value for _, value in rank_values]
                positions = list(range(len(rank_values)))
                axis.barh(positions, values, color="#70AD47")
                axis.set_yticks(positions, labels)
                axis.invert_yaxis()
                axis.set_xlabel("Mean rank (lower is better)")
                axis.grid(axis="x", linestyle=":", alpha=0.5)
            axis.set_title(
                f"{result.problem_family}: complete blocks={result.block_count}; "
                f"ties={str(result.ties_present).lower()}"
            )
        figure.suptitle("Friedman complete-block mean ranks")
    else:
        axis = figure.add_subplot(1, 1, 1)
        axis.text(
            0.5,
            0.5,
            "No eligible Friedman families",
            ha="center",
            va="center",
        )
        axis.set_axis_off()
        axis.set_title("Friedman complete-block mean ranks")
    try:
        figure.savefig(
            directory / _FIGURE_FILENAMES[1],
            format="png",
            dpi=160,
            bbox_inches="tight",
            metadata={"Software": "AFCS"},
        )
    except OSError as error:
        raise AnalysisExportError(
            f"Could not render analysis figure "
            f"{directory / _FIGURE_FILENAMES[1]}: {error}"
        ) from error
    finally:
        figure.clear()

    convergence_groups: dict[InstanceIdentity, list[ConvergenceSummary]] = defaultdict(
        list
    )
    for summary in report.convergence_summaries:
        convergence_groups[summary.instance_identity].append(summary)
    sorted_groups = sorted(
        convergence_groups.items(),
        key=lambda item: (
            item[0].problem_family,
            item[0].instance,
            -1 if item[0].dimension is None else item[0].dimension,
            item[0].direction,
            item[0].instance_id,
        ),
    )
    figure_height = max(3.2, 3.2 * max(1, len(sorted_groups)))
    figure = Figure(figsize=(10, figure_height), dpi=160)
    FigureCanvasAgg(figure)
    if sorted_groups:
        for panel_index, (group_key, summaries) in enumerate(sorted_groups, start=1):
            axis = figure.add_subplot(len(sorted_groups), 1, panel_index)
            for configuration_id in sorted(
                {item.configuration_id for item in summaries}
            ):
                points = sorted(
                    (
                        item
                        for item in summaries
                        if item.configuration_id == configuration_id
                    ),
                    key=lambda item: item.evaluations,
                )
                evaluations = [item.evaluations for item in points]
                medians = [item.median_objective for item in points]
                lower = [item.q25_objective for item in points]
                upper = [item.q75_objective for item in points]
                (line,) = axis.plot(evaluations, medians, label=configuration_id)
                axis.fill_between(
                    evaluations,
                    lower,
                    upper,
                    color=line.get_color(),
                    alpha=0.16,
                )
            family = group_key.problem_family
            instance = group_key.instance
            dimension = group_key.dimension
            direction = group_key.direction
            dimension_label = "unspecified" if dimension is None else str(dimension)
            axis.set_title(
                f"{family} {instance} (dimension={dimension_label}, "
                f"{direction}, instance_id={group_key.instance_id}, "
                f"identity={group_key.semantic_sha256[:12]})"
            )
            axis.set_xlabel("Objective evaluations")
            axis.set_ylabel("Best objective (median; IQR)")
            axis.grid(linestyle=":", alpha=0.5)
            axis.legend()
    else:
        axis = figure.add_subplot(1, 1, 1)
        axis.text(
            0.5,
            0.5,
            "No completed-run convergence data available",
            ha="center",
            va="center",
        )
        axis.set_axis_off()
        axis.set_title("Convergence at observed evaluation checkpoints")
    figure.suptitle("Convergence at observed evaluation checkpoints")
    try:
        figure.savefig(
            directory / _FIGURE_FILENAMES[2],
            format="png",
            dpi=160,
            bbox_inches="tight",
            metadata={"Software": "AFCS"},
        )
    except OSError as error:
        raise AnalysisExportError(
            f"Could not render analysis figure "
            f"{directory / _FIGURE_FILENAMES[2]}: {error}"
        ) from error
    finally:
        figure.clear()
    return matplotlib.__version__


def _analysis_figures_manifest(
    report: CampaignAnalysisReport,
    directory: Path,
    matplotlib_version: str,
) -> dict[str, Any]:
    figures: dict[str, dict[str, Any]] = {}
    for filename in _FIGURE_FILENAMES:
        path = directory / filename
        try:
            data = path.read_bytes()
        except OSError as error:
            raise AnalysisExportError(
                f"Could not read generated analysis figure {path}: {error}"
            ) from error
        figures[filename] = {
            "sha256": hashlib.sha256(data).hexdigest(),
            "size_bytes": len(data),
        }
    return {
        "schema_version": ANALYSIS_FIGURES_SCHEMA_VERSION,
        "campaign_id": report.campaign_id,
        "analysis_report_sha256": hashlib.sha256(
            _report_json(report).encode("utf-8")
        ).hexdigest(),
        "matplotlib_version": matplotlib_version,
        "figures": figures,
    }


def _write_analysis_figures_to_directory(
    report: CampaignAnalysisReport,
    directory: Path,
) -> str:
    matplotlib_version = _render_campaign_analysis_figures(report, directory)
    manifest = _analysis_figures_manifest(report, directory, matplotlib_version)
    try:
        (directory / "manifest.json").write_text(
            json.dumps(
                manifest,
                ensure_ascii=False,
                allow_nan=False,
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
            newline="\n",
        )
    except (OSError, TypeError, ValueError) as error:
        raise AnalysisExportError(
            f"Could not generate analysis figures manifest in {directory}: {error}"
        ) from error
    return matplotlib_version


def write_campaign_analysis_figures(
    report: CampaignAnalysisReport,
    directory: str | Path,
) -> CampaignAnalysisFiguresExport:
    """Render deterministic rank figures and install a hash manifest last."""

    _report_json(report)
    output_directory = Path(directory)
    try:
        output_directory.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(
            prefix=".afcs-analysis-figures-",
            dir=output_directory,
        ) as staged_name:
            staged_directory = Path(staged_name)
            matplotlib_version = _write_analysis_figures_to_directory(
                report, staged_directory
            )
            for filename in _FIGURE_FILENAMES:
                os.replace(
                    staged_directory / filename,
                    output_directory / filename,
                )
            os.replace(
                staged_directory / "manifest.json",
                output_directory / "manifest.json",
            )
    except OSError as error:
        raise AnalysisExportError(
            f"Could not write campaign analysis figures to {output_directory}: {error}"
        ) from error
    return CampaignAnalysisFiguresExport(
        campaign_id=report.campaign_id,
        directory=str(output_directory),
        files=_FIGURE_FILENAMES,
        manifest_path=str(output_directory / "manifest.json"),
        matplotlib_version=matplotlib_version,
    )


def reconcile_campaign_analysis_figures(
    report: CampaignAnalysisReport,
    directory: str | Path,
) -> CampaignAnalysisFiguresReconciliation:
    """Regenerate expected figures and compare them and their manifest."""

    output_directory = Path(directory)
    with tempfile.TemporaryDirectory(prefix="afcs-analysis-figures-") as name:
        expected_directory = Path(name)
        _write_analysis_figures_to_directory(report, expected_directory)
        figure_results: list[FigureArtifactReconciliation] = []
        for filename in _FIGURE_FILENAMES:
            expected_path = expected_directory / filename
            actual_path = output_directory / filename
            expected_hash = hashlib.sha256(expected_path.read_bytes()).hexdigest()
            if not actual_path.is_file():
                figure_results.append(
                    FigureArtifactReconciliation(
                        filename=filename,
                        path=str(actual_path),
                        matches=False,
                        expected_sha256=expected_hash,
                        actual_sha256=None,
                        mismatch_kind="file_missing",
                    )
                )
                continue
            try:
                actual_hash = hashlib.sha256(actual_path.read_bytes()).hexdigest()
            except OSError as error:
                raise AnalysisExportError(
                    f"Could not read analysis figure {actual_path}: {error}"
                ) from error
            matches = actual_hash == expected_hash
            figure_results.append(
                FigureArtifactReconciliation(
                    filename=filename,
                    path=str(actual_path),
                    matches=matches,
                    expected_sha256=expected_hash,
                    actual_sha256=actual_hash,
                    mismatch_kind=None if matches else "content_mismatch",
                )
            )

        expected_manifest_path = expected_directory / "manifest.json"
        actual_manifest_path = output_directory / "manifest.json"
        expected_manifest_text = expected_manifest_path.read_text(encoding="utf-8")
        expected_manifest_hash = hashlib.sha256(
            expected_manifest_text.encode("utf-8")
        ).hexdigest()
        if not actual_manifest_path.is_file():
            return CampaignAnalysisFiguresReconciliation(
                campaign_id=report.campaign_id,
                figures=tuple(figure_results),
                manifest_path=str(actual_manifest_path),
                manifest_matches=False,
                manifest_mismatch_kind="file_missing",
                expected_manifest_sha256=expected_manifest_hash,
                actual_manifest_sha256=None,
            )
        try:
            actual_manifest_text = actual_manifest_path.read_text(encoding="utf-8")
            actual_manifest = json.loads(actual_manifest_text)
        except (OSError, UnicodeError, json.JSONDecodeError) as error:
            if isinstance(error, OSError):
                raise AnalysisExportError(
                    f"Could not read analysis figures manifest "
                    f"{actual_manifest_path}: {error}"
                ) from error
            return CampaignAnalysisFiguresReconciliation(
                campaign_id=report.campaign_id,
                figures=tuple(figure_results),
                manifest_path=str(actual_manifest_path),
                manifest_matches=False,
                manifest_mismatch_kind="invalid_json",
                expected_manifest_sha256=expected_manifest_hash,
                actual_manifest_sha256=None,
            )
        actual_manifest_hash = hashlib.sha256(
            actual_manifest_text.encode("utf-8")
        ).hexdigest()
        manifest_matches = actual_manifest == json.loads(expected_manifest_text)
        return CampaignAnalysisFiguresReconciliation(
            campaign_id=report.campaign_id,
            figures=tuple(figure_results),
            manifest_path=str(actual_manifest_path),
            manifest_matches=manifest_matches,
            manifest_mismatch_kind=(None if manifest_matches else "content_mismatch"),
            expected_manifest_sha256=expected_manifest_hash,
            actual_manifest_sha256=actual_manifest_hash,
        )


def run_campaign_analysis(
    connection: sqlite3.Connection,
    campaign_id: str,
    output_directory: str | Path,
    alpha: float = 0.05,
) -> CampaignAnalysisPipelineResult:
    """Export, analyze, render, and reconcile one campaign as a single workflow."""

    if not math.isfinite(alpha) or alpha <= 0 or alpha >= 1:
        raise AnalysisError("alpha must be finite and strictly between 0 and 1")
    root = Path(output_directory)
    runs_path = root / "runs.csv"
    traces_path = root / "traces.csv"
    report_path = root / "analysis.json"
    tables_directory = root / "tables"
    figures_directory = root / "figures"
    export_summary = export_campaign_csv(
        connection, campaign_id, runs_path, traces_path
    )
    report = build_campaign_analysis_report(
        connection, campaign_id, runs_path, traces_path, alpha
    )
    write_campaign_analysis_report(report, report_path)
    write_campaign_analysis_tables(report, tables_directory)
    write_campaign_analysis_figures(report, figures_directory)

    report_check = reconcile_campaign_analysis_report(
        connection,
        campaign_id,
        runs_path,
        traces_path,
        report_path,
        alpha,
    )
    table_check = reconcile_campaign_analysis_tables(report, tables_directory)
    figure_check = reconcile_campaign_analysis_figures(report, figures_directory)
    if not report_check.matches or not table_check.matches or not figure_check.matches:
        raise AnalysisExportError(
            f"Campaign {campaign_id!r} analysis pipeline failed reconciliation: "
            f"report={report_check.mismatch_kind}, "
            f"tables_match={table_check.matches}, "
            f"figures_match={figure_check.matches}"
        )
    return CampaignAnalysisPipelineResult(
        campaign_id=campaign_id,
        output_directory=str(root),
        run_row_count=export_summary.run_rows,
        trace_row_count=export_summary.trace_rows,
        report_path=str(report_path),
        tables_directory=str(tables_directory),
        figures_directory=str(figures_directory),
    )


def write_campaign_analysis_report(
    report: CampaignAnalysisReport,
    path: str | Path,
) -> Path:
    """Write a deterministic JSON report via an atomic replacement."""

    output_path = Path(path)
    temporary_path: Path | None = None
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="\n",
            dir=output_path.parent,
            prefix=f".{output_path.name}.",
            suffix=".tmp",
            delete=False,
        ) as file:
            temporary_path = Path(file.name)
            file.write(_report_json(report))
            file.flush()
            os.fsync(file.fileno())
        os.replace(temporary_path, output_path)
    except OSError as error:
        raise AnalysisExportError(
            f"Could not write campaign analysis report {output_path}: {error}"
        ) from error
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
    return output_path


def reconcile_campaign_analysis_report(
    connection: sqlite3.Connection,
    campaign_id: str,
    runs_path: str | Path,
    traces_path: str | Path,
    report_path: str | Path,
    alpha: float = 0.05,
) -> AnalysisReportReconciliation:
    """Compare a stored report with a fresh reconciled analysis of SQLite."""

    import hashlib

    expected_report = build_campaign_analysis_report(
        connection, campaign_id, runs_path, traces_path, alpha
    )
    expected_text = _report_json(expected_report)
    expected_hash = hashlib.sha256(expected_text.encode("utf-8")).hexdigest()
    path = Path(report_path)
    if not path.is_file():
        return AnalysisReportReconciliation(
            path=str(path),
            matches=False,
            mismatch_kind="file_missing",
            expected_sha256=expected_hash,
            actual_sha256=None,
        )

    try:
        actual_text = path.read_text(encoding="utf-8")
        actual_payload = json.loads(actual_text)
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        if isinstance(error, OSError):
            raise AnalysisExportError(
                f"Could not read campaign analysis report {path}: {error}"
            ) from error
        return AnalysisReportReconciliation(
            path=str(path),
            matches=False,
            mismatch_kind="invalid_json",
            expected_sha256=expected_hash,
            actual_sha256=None,
        )

    actual_hash = hashlib.sha256(actual_text.encode("utf-8")).hexdigest()
    matches = actual_payload == json.loads(expected_text)
    return AnalysisReportReconciliation(
        path=str(path),
        matches=matches,
        mismatch_kind=None if matches else "content_mismatch",
        expected_sha256=expected_hash,
        actual_sha256=actual_hash,
    )
