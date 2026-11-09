"""Descriptive and paired summaries for canonical campaign run rows."""

from __future__ import annotations

import hashlib
import json
import math
import statistics
from collections import Counter, defaultdict
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from numbers import Number
from typing import Any, SupportsFloat, cast

from afcs.persistence import canonical_json


class AnalysisError(ValueError):
    """Raised when run rows cannot support a well-defined analysis."""


@dataclass(frozen=True, slots=True)
class InstanceIdentity:
    """Local reference plus a versioned semantic fingerprint, never a plot label."""

    instance_id: int
    problem_family: str
    instance: str
    dimension: int | None
    direction: str
    optimum: float | None
    parameters_json: str
    data_sha256: str | None
    fingerprint_version: str
    semantic_sha256: str


ProblemGroupKey = tuple[str, str, str, int | None, str, InstanceIdentity]
ConvergenceGroupKey = tuple[str, str, str, int | None, str, InstanceIdentity]


@dataclass(frozen=True, slots=True)
class ObjectiveSummary:
    campaign_id: str
    instance_identity: InstanceIdentity
    problem_family: str
    instance: str
    dimension: int | None
    direction: str
    configuration_id: str
    algorithm: str
    optimizer_version: str | None
    run_count: int
    completed_count: int
    status_counts: tuple[tuple[str, int], ...]
    objective_provenance_counts: tuple[tuple[str, int], ...]
    mean: float | None
    sample_std: float | None
    median: float | None
    q25: float | None
    q75: float | None
    minimum: float | None
    maximum: float | None


@dataclass(frozen=True, slots=True)
class PairedObjectiveSummary:
    campaign_id: str
    instance_identity: InstanceIdentity
    problem_family: str
    instance: str
    dimension: int | None
    direction: str
    baseline_configuration_id: str
    candidate_configuration_id: str
    baseline_completed_count: int
    candidate_completed_count: int
    paired_count: int
    baseline_unpaired_count: int
    candidate_unpaired_count: int
    baseline_noncompleted_count: int
    candidate_noncompleted_count: int
    mean_baseline: float | None
    mean_candidate: float | None
    mean_improvement: float | None
    median_improvement: float | None
    sample_std_improvement: float | None
    minimum_improvement: float | None
    maximum_improvement: float | None


@dataclass(frozen=True, slots=True)
class AggregateObjectiveRank:
    campaign_id: str
    configuration_id: str
    algorithm: str
    optimizer_version: str | None
    instances_ranked: int
    total_instances: int
    ranked_instances: tuple[InstanceIdentity, ...]
    available_instances: tuple[InstanceIdentity, ...]
    mean_rank: float | None
    median_rank: float | None
    unique_best_count: int
    tied_best_count: int
    worst_count: int


@dataclass(frozen=True, slots=True)
class PairedObjectiveTest:
    comparison: PairedObjectiveSummary
    test: str
    correction: str
    family_id: str
    family_size: int
    alpha: float
    statistic: float | None
    raw_p_value: float | None
    adjusted_p_value: float | None
    reject_null: bool | None
    rank_biserial_effect: float | None
    hodges_lehmann_effect: float | None
    zero_difference_count: int
    nonzero_difference_count: int
    p_value_method: str
    scipy_version: str | None


@dataclass(frozen=True, slots=True)
class ConvergenceSummary:
    campaign_id: str
    instance_identity: InstanceIdentity
    problem_family: str
    instance: str
    dimension: int | None
    direction: str
    configuration_id: str
    algorithm: str
    optimizer_version: str | None
    evaluations: int
    checkpoint_count: int
    median_objective: float
    q25_objective: float
    q75_objective: float
    observed_value_count: int
    reconstructed_value_count: int
    expected_value_count: int
    provenance_counts: tuple[tuple[str, int], ...]


@dataclass(frozen=True, slots=True)
class ConvergenceCoverage:
    campaign_id: str
    instance_identity: InstanceIdentity
    problem_family: str
    instance: str
    dimension: int | None
    configuration_id: str
    completed_run_count: int
    completed_runs_with_trace: int
    completed_runs_without_trace: int
    noncompleted_runs_with_trace: int
    completed_trace_points_without_objective: int


@dataclass(frozen=True, slots=True)
class ConvergenceCurveSummary:
    run_count: int
    iterations: tuple[int, ...]
    mean_objective: tuple[float, ...]
    population_std_objective: tuple[float, ...]


@dataclass(frozen=True, slots=True)
class IterationValueSummary:
    group_values: tuple[Any, ...]
    iteration: Any
    value_count: int
    mean: float | None
    sample_std: float | None


@dataclass(frozen=True, slots=True)
class FriedmanResult:
    campaign_id: str
    problem_family: str
    configurations: tuple[str, ...]
    included_instances: tuple[InstanceIdentity, ...]
    excluded_instances: tuple[InstanceIdentity, ...]
    block_count: int
    incomplete_block_count: int
    statistic: float | None
    p_value: float | None
    kendall_w: float | None
    ties_present: bool
    average_ranks: tuple[tuple[str, float | None], ...]
    alpha: float
    reject_null: bool | None
    test: str
    p_value_method: str
    p_value_approximation_recommended: bool
    scipy_version: str | None


@dataclass(frozen=True, slots=True)
class FriedmanPostHocResult:
    campaign_id: str
    problem_family: str
    baseline_configuration_id: str
    candidate_configuration_id: str
    omnibus_p_value: float | None
    omnibus_reject_null: bool | None
    omnibus_p_value_approximation_recommended: bool
    paired_instance_count: int
    status: str
    family_id: str
    family_size: int
    alpha: float
    mean_rank_difference: float | None
    studentized_range_statistic: float | None
    p_value: float | None
    reject_null: bool | None
    p_value_method: str
    scipy_version: str | None


def _required_text(row: Mapping[str, Any], field: str) -> str:
    value = row.get(field)
    if not isinstance(value, str) or not value:
        raise AnalysisError(f"Run row requires non-empty {field!r}")
    return value


def _positive_integer(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, (str, int)):
        raise AnalysisError(f"Run row {field} must be a positive integer")
    try:
        normalized = int(value)
    except ValueError as error:
        raise AnalysisError(f"Run row {field} must be a positive integer") from error
    if normalized < 1:
        raise AnalysisError(f"Run row {field} must be positive")
    return normalized


def _group_key(row: Mapping[str, Any]) -> ProblemGroupKey:
    campaign_id = _required_text(row, "campaign_id")
    problem_family = _required_text(row, "problem_family")
    instance = _required_text(row, "instance")
    direction = _required_text(row, "direction")
    if direction not in {"minimize", "maximize"}:
        raise AnalysisError(f"Unsupported objective direction: {direction!r}")

    dimension_value = row.get("dimension")
    if dimension_value in (None, ""):
        dimension = None
    else:
        dimension = _positive_integer(dimension_value, "dimension")
    instance_id = _positive_integer(row.get("instance_id"), "instance_id")
    parameters_text = _required_text(row, "problem_parameters_json")
    try:
        parameters = json.loads(parameters_text)
        if not isinstance(parameters, dict):
            raise ValueError("parameters must be an object")
        parameters_json = canonical_json(parameters)
    except (TypeError, ValueError) as error:
        raise AnalysisError(
            "Problem parameters must be a finite JSON object"
        ) from error
    optimum_value = row.get("optimum")
    try:
        optimum = None if optimum_value in (None, "") else float(optimum_value)
    except (TypeError, ValueError) as error:
        raise AnalysisError("Instance optimum must be finite or empty") from error
    if isinstance(optimum_value, bool) or (
        optimum is not None and not math.isfinite(optimum)
    ):
        raise AnalysisError("Instance optimum must be finite or empty")
    data_value = row.get("data_sha256")
    data_sha256 = None if data_value in (None, "") else data_value
    if data_sha256 is not None and (
        not isinstance(data_sha256, str)
        or len(data_sha256) != 64
        or any(char not in "0123456789abcdef" for char in data_sha256)
    ):
        raise AnalysisError("Instance data_sha256 must be a lowercase SHA-256 or empty")
    version = "problem_instance_v1"
    payload = canonical_json(
        {
            "version": version,
            "problem_family": problem_family,
            "instance": instance,
            "dimension": dimension,
            "direction": direction,
            "optimum": optimum,
            "parameters": parameters,
            "data_sha256": data_sha256,
        }
    )
    identity = InstanceIdentity(
        instance_id,
        problem_family,
        instance,
        dimension,
        direction,
        optimum,
        parameters_json,
        data_sha256,
        version,
        hashlib.sha256(payload.encode("utf-8")).hexdigest(),
    )
    return campaign_id, problem_family, instance, dimension, direction, identity


def _validated_rows(run_rows: Iterable[Mapping[str, Any]]) -> list[Mapping[str, Any]]:
    rows = list(run_rows)
    identities: dict[tuple[str, int], InstanceIdentity] = {}
    for row in rows:
        key = _group_key(row)
        reference = (key[0], key[5].instance_id)
        previous = identities.setdefault(reference, key[5])
        if previous != key[5]:
            raise AnalysisError(f"inconsistent metadata for instance_id {reference!r}")
    return rows


def _objective(row: Mapping[str, Any]) -> float:
    value = row.get("objective_best")
    if isinstance(value, bool) or value in (None, ""):
        raise AnalysisError("Completed run is missing objective_best")
    try:
        objective = float(value)
    except (TypeError, ValueError) as error:
        raise AnalysisError("objective_best must be numeric") from error
    if not math.isfinite(objective):
        raise AnalysisError("objective_best must be finite")
    return objective


def _provenance(row: Mapping[str, Any]) -> str:
    value = row.get("provenance__objective_best")
    return value if isinstance(value, str) and value else "unavailable"


def _quantile(sorted_values: list[float], probability: float) -> float:
    """Linearly interpolate using Hyndman-Fan type 7 quantiles."""

    if len(sorted_values) == 1:
        return sorted_values[0]
    position = (len(sorted_values) - 1) * probability
    lower = math.floor(position)
    fraction = position - lower
    if lower + 1 == len(sorted_values):
        return sorted_values[lower]
    return sorted_values[lower] + fraction * (
        sorted_values[lower + 1] - sorted_values[lower]
    )


def _describe(
    values: list[float],
) -> tuple[
    float | None,
    float | None,
    float | None,
    float | None,
    float | None,
    float | None,
    float | None,
]:
    if not values:
        return (None, None, None, None, None, None, None)
    ordered = sorted(values)
    return (
        statistics.fmean(values),
        statistics.stdev(values) if len(values) > 1 else None,
        statistics.median(ordered),
        _quantile(ordered, 0.25),
        _quantile(ordered, 0.75),
        ordered[0],
        ordered[-1],
    )


def _average_ranks(scores: Mapping[str, float]) -> dict[str, float]:
    ordered_scores = sorted(scores.values())
    ranks: dict[str, float] = {}
    for configuration_id, score in scores.items():
        first = ordered_scores.index(score) + 1
        last = len(ordered_scores) - ordered_scores[::-1].index(score)
        ranks[configuration_id] = (first + last) / 2
    return ranks


def summarize_objectives(
    run_rows: Iterable[Mapping[str, Any]],
) -> tuple[ObjectiveSummary, ...]:
    """Summarize objective values per campaign, problem instance, and configuration.

    ``instance_id`` and ``problem_parameters_json`` must be explicit; labels
    never reconstruct identity. Only ``completed`` runs contribute values.
    Counts for every observed run status are retained so exclusions are explicit. Standard
    deviation is the sample standard deviation; quartiles use type 7.
    """

    groups: dict[
        tuple[ProblemGroupKey, str, str, str | None],
        list[Mapping[str, Any]],
    ] = defaultdict(list)
    for row in _validated_rows(run_rows):
        key = _group_key(row)
        configuration_id = _required_text(row, "configuration_id")
        algorithm = _required_text(row, "algorithm")
        version_value = row.get("optimizer_version")
        version = (
            version_value if isinstance(version_value, str) and version_value else None
        )
        groups[(key, configuration_id, algorithm, version)].append(row)

    summaries: list[ObjectiveSummary] = []
    for (key, configuration_id, algorithm, version), rows in groups.items():
        status_counts = Counter(_required_text(row, "run_status") for row in rows)
        values = [
            _objective(row) for row in rows if row.get("run_status") == "completed"
        ]
        provenance_counts = Counter(
            _provenance(row) for row in rows if row.get("run_status") == "completed"
        )
        mean, sample_std, median, q25, q75, minimum, maximum = _describe(values)
        summaries.append(
            ObjectiveSummary(
                campaign_id=key[0],
                instance_identity=key[5],
                problem_family=key[1],
                instance=key[2],
                dimension=key[3],
                direction=key[4],
                configuration_id=configuration_id,
                algorithm=algorithm,
                optimizer_version=version,
                run_count=len(rows),
                completed_count=len(values),
                status_counts=tuple(sorted(status_counts.items())),
                objective_provenance_counts=tuple(sorted(provenance_counts.items())),
                mean=mean,
                sample_std=sample_std,
                median=median,
                q25=q25,
                q75=q75,
                minimum=minimum,
                maximum=maximum,
            )
        )
    return tuple(
        sorted(
            summaries,
            key=lambda item: (
                item.campaign_id,
                item.problem_family,
                item.instance,
                -1 if item.dimension is None else item.dimension,
                item.instance_identity.instance_id,
                item.configuration_id,
            ),
        )
    )


def compare_paired_objectives(
    run_rows: Iterable[Mapping[str, Any]],
    baseline_configuration_id: str,
    candidate_configuration_id: str,
) -> tuple[PairedObjectiveSummary, ...]:
    """Compare two configurations using completed runs with matching seed pairs.

    Pair identity is ``(replica_index, random_seed)`` within a campaign and
    problem instance. Positive improvement means the candidate is better:
    baseline minus candidate for minimization, candidate minus baseline for
    maximization. No hypothesis test or p-value is computed.
    """

    if not baseline_configuration_id or not candidate_configuration_id:
        raise AnalysisError("Configuration identifiers must be non-empty")
    if baseline_configuration_id == candidate_configuration_id:
        raise AnalysisError("Baseline and candidate configurations must differ")

    selected_configs = {baseline_configuration_id, candidate_configuration_id}
    selected: dict[
        ProblemGroupKey,
        dict[str, list[Mapping[str, Any]]],
    ] = defaultdict(
        lambda: {baseline_configuration_id: [], candidate_configuration_id: []}
    )
    for row in _validated_rows(run_rows):
        configuration_id = row.get("configuration_id")
        if configuration_id not in selected_configs:
            continue
        key = _group_key(row)
        selected[key][configuration_id].append(row)

    summaries: list[PairedObjectiveSummary] = []
    for key, configurations in selected.items():
        baseline_rows = configurations[baseline_configuration_id]
        candidate_rows = configurations[candidate_configuration_id]
        baseline_completed = _completed_by_pair(baseline_rows)
        candidate_completed = _completed_by_pair(candidate_rows)
        paired_keys = baseline_completed.keys() & candidate_completed.keys()
        baseline_only = baseline_completed.keys() - candidate_completed.keys()
        candidate_only = candidate_completed.keys() - baseline_completed.keys()
        differences = [
            (
                baseline_completed[pair] - candidate_completed[pair]
                if key[4] == "minimize"
                else candidate_completed[pair] - baseline_completed[pair]
            )
            for pair in sorted(paired_keys)
        ]
        mean_baseline = (
            statistics.fmean(baseline_completed[pair] for pair in sorted(paired_keys))
            if paired_keys
            else None
        )
        mean_candidate = (
            statistics.fmean(candidate_completed[pair] for pair in sorted(paired_keys))
            if paired_keys
            else None
        )
        ordered_differences = sorted(differences)
        summaries.append(
            PairedObjectiveSummary(
                campaign_id=key[0],
                instance_identity=key[5],
                problem_family=key[1],
                instance=key[2],
                dimension=key[3],
                direction=key[4],
                baseline_configuration_id=baseline_configuration_id,
                candidate_configuration_id=candidate_configuration_id,
                baseline_completed_count=len(baseline_completed),
                candidate_completed_count=len(candidate_completed),
                paired_count=len(paired_keys),
                baseline_unpaired_count=len(baseline_only),
                candidate_unpaired_count=len(candidate_only),
                baseline_noncompleted_count=len(baseline_rows)
                - len(baseline_completed),
                candidate_noncompleted_count=len(candidate_rows)
                - len(candidate_completed),
                mean_baseline=mean_baseline,
                mean_candidate=mean_candidate,
                mean_improvement=statistics.fmean(differences) if differences else None,
                median_improvement=statistics.median(differences)
                if differences
                else None,
                sample_std_improvement=statistics.stdev(differences)
                if len(differences) > 1
                else None,
                minimum_improvement=ordered_differences[0]
                if ordered_differences
                else None,
                maximum_improvement=ordered_differences[-1]
                if ordered_differences
                else None,
            )
        )
    return tuple(
        sorted(
            summaries,
            key=lambda item: (
                item.campaign_id,
                item.problem_family,
                item.instance,
                -1 if item.dimension is None else item.dimension,
                item.instance_identity.instance_id,
                item.baseline_configuration_id,
            ),
        )
    )


def aggregate_objective_ranks(
    run_rows: Iterable[Mapping[str, Any]],
) -> tuple[AggregateObjectiveRank, ...]:
    """Aggregate configuration performance across instances using average ranks.

    Within each campaign and problem instance, configurations are ranked by
    their median completed objective, respecting optimization direction. Exact
    ties receive average ranks. Mean ranks weight each available instance
    equally; objective values from different scales are never pooled.
    """

    rows = list(run_rows)
    summaries = summarize_objectives(rows)
    instance_groups: dict[ProblemGroupKey, list[ObjectiveSummary]] = defaultdict(list)
    for summary in summaries:
        key = (
            summary.campaign_id,
            summary.problem_family,
            summary.instance,
            summary.dimension,
            summary.direction,
            summary.instance_identity,
        )
        instance_groups[key].append(summary)

    total_instances: Counter[str] = Counter(key[0] for key in instance_groups)
    rank_values: dict[tuple[str, str], list[float]] = defaultdict(list)
    ranked_instances: dict[tuple[str, str], list[InstanceIdentity]] = defaultdict(list)
    available_instances: dict[str, list[InstanceIdentity]] = defaultdict(list)
    for key in instance_groups:
        available_instances[key[0]].append(key[5])
    placements: Counter[tuple[str, str, str]] = Counter()
    metadata: dict[tuple[str, str], tuple[str, str | None]] = {}

    for (campaign_id, _, _, _, direction, identity), group in instance_groups.items():
        eligible = [summary for summary in group if summary.median is not None]
        if not eligible:
            continue
        scores: dict[str, float] = {}
        for summary in eligible:
            median = summary.median
            if median is None:
                continue
            scores[summary.configuration_id] = (
                median if direction == "minimize" else -median
            )
        ranks = _average_ranks(scores)
        ordered_scores = sorted(scores.values())
        for configuration_id in scores:
            metadata_key = (campaign_id, configuration_id)
            value = next(
                summary
                for summary in eligible
                if summary.configuration_id == configuration_id
            )
            previous = metadata.get(metadata_key)
            current = (value.algorithm, value.optimizer_version)
            if previous is not None and previous != current:
                raise AnalysisError(
                    f"Configuration {configuration_id!r} has inconsistent metadata"
                )
            metadata[metadata_key] = current
            rank_values[metadata_key].append(ranks[configuration_id])
            ranked_instances[metadata_key].append(identity)

        best_score = ordered_scores[0]
        worst_score = ordered_scores[-1]
        best_configurations = [
            configuration_id
            for configuration_id, score in scores.items()
            if score == best_score
        ]
        for configuration_id, score in scores.items():
            placements[(campaign_id, configuration_id, "unique_best")] += int(
                len(best_configurations) == 1 and score == best_score
            )
            placements[(campaign_id, configuration_id, "tied_best")] += int(
                len(best_configurations) > 1 and score == best_score
            )
            placements[(campaign_id, configuration_id, "worst")] += int(
                score == worst_score
            )

    results: list[AggregateObjectiveRank] = []
    for (campaign_id, configuration_id), ranks in rank_values.items():
        algorithm, version = metadata[(campaign_id, configuration_id)]
        results.append(
            AggregateObjectiveRank(
                campaign_id=campaign_id,
                configuration_id=configuration_id,
                algorithm=algorithm,
                optimizer_version=version,
                instances_ranked=len(ranks),
                total_instances=total_instances[campaign_id],
                ranked_instances=tuple(
                    ranked_instances[(campaign_id, configuration_id)]
                ),
                available_instances=tuple(available_instances[campaign_id]),
                mean_rank=statistics.fmean(ranks),
                median_rank=statistics.median(ranks),
                unique_best_count=placements[
                    (campaign_id, configuration_id, "unique_best")
                ],
                tied_best_count=placements[
                    (campaign_id, configuration_id, "tied_best")
                ],
                worst_count=placements[(campaign_id, configuration_id, "worst")],
            )
        )
    return tuple(
        sorted(
            results,
            key=lambda item: (
                item.campaign_id,
                item.mean_rank,
                item.configuration_id,
            ),
        )
    )


def summarize_convergence(
    run_rows: Iterable[Mapping[str, Any]],
    trace_rows: Iterable[Mapping[str, Any]],
) -> tuple[tuple[ConvergenceSummary, ...], tuple[ConvergenceCoverage, ...]]:
    """Summarize observed best-so-far traces at exact evaluation counts.

    Only completed runs contribute to convergence curves. No interpolation is
    performed; the quartiles at each evaluation count describe the completed
    runs that actually have a checkpoint at that count. If a run has multiple
    checkpoints at one evaluation count, only its latest checkpoint is used.
    """

    runs_by_id: dict[str, Mapping[str, Any]] = {}
    coverage_state: dict[
        ConvergenceGroupKey,
        dict[str, Any],
    ] = {}
    for row in _validated_rows(run_rows):
        run_id = _required_text(row, "run_id")
        if run_id in runs_by_id:
            raise AnalysisError(f"Duplicate run_id in convergence input: {run_id!r}")
        runs_by_id[run_id] = row
        campaign_id, family, instance, dimension, direction, identity = _group_key(row)
        configuration_id = _required_text(row, "configuration_id")
        key = (campaign_id, family, instance, dimension, configuration_id, identity)
        state = coverage_state.setdefault(
            key,
            {
                "algorithm": _required_text(row, "algorithm"),
                "optimizer_version": row.get("optimizer_version"),
                "completed_run_count": 0,
                "completed_runs_with_trace": 0,
                "completed_runs_without_trace": 0,
                "noncompleted_runs_with_trace": 0,
                "completed_trace_points_without_objective": 0,
                "direction": direction,
                "trace_run_ids": set(),
            },
        )
        if (
            state["algorithm"] != row.get("algorithm")
            or state["optimizer_version"] != row.get("optimizer_version")
            or state["direction"] != direction
        ):
            raise AnalysisError(
                f"Configuration {configuration_id!r} has inconsistent metadata"
            )
        if row.get("run_status") == "completed":
            state["completed_run_count"] += 1

    latest_points: dict[
        tuple[str, ConvergenceGroupKey, int],
        tuple[int, float, str],
    ] = {}
    for trace in trace_rows:
        run_id = _required_text(trace, "run_id")
        run = runs_by_id.get(run_id)
        if run is None:
            raise AnalysisError(f"Trace references unknown run_id {run_id!r}")
        run_group = _group_key(run)
        trace_dimension_value = trace.get("dimension")
        try:
            trace_dimension = (
                None
                if trace_dimension_value in (None, "")
                else int(trace_dimension_value)
            )
        except (TypeError, ValueError) as error:
            raise AnalysisError(
                "Trace row dimension must be an integer or empty"
            ) from error
        trace_identity = (
            trace.get("campaign_id"),
            trace.get("problem_family"),
            trace.get("instance"),
            trace_dimension,
            _positive_integer(trace.get("instance_id"), "instance_id"),
        )
        run_identity = (*run_group[:4], run_group[5].instance_id)
        configuration_id = _required_text(trace, "configuration_id")
        if trace_identity != run_identity or configuration_id != run.get(
            "configuration_id"
        ):
            raise AnalysisError(f"Trace identity does not match run {run_id!r}")
        key = (
            run_group[0],
            run_group[1],
            run_group[2],
            run_group[3],
            configuration_id,
            run_group[5],
        )
        state = coverage_state[key]
        state["trace_run_ids"].add(run_id)
        checkpoint_index_value = trace.get("checkpoint_index")
        evaluations_value = trace.get("evaluations")
        try:
            if checkpoint_index_value is None or evaluations_value is None:
                raise TypeError("trace indices cannot be None")
            checkpoint_index = int(checkpoint_index_value)
            evaluations = int(evaluations_value)
        except (TypeError, ValueError) as error:
            raise AnalysisError(
                "Trace checkpoint_index and evaluations must be integers"
            ) from error
        if checkpoint_index < 0 or evaluations < 0:
            raise AnalysisError(
                "Trace checkpoint_index and evaluations must be non-negative"
            )
        if run.get("run_status") != "completed":
            continue
        value = trace.get("metric__objective_best")
        if value in (None, ""):
            state["completed_trace_points_without_objective"] += 1
            continue
        try:
            objective = float(value)
        except (TypeError, ValueError) as error:
            raise AnalysisError(
                "Trace objective_best must be numeric when present"
            ) from error
        if not math.isfinite(objective):
            raise AnalysisError("Trace objective_best must be finite")
        provenance_value = trace.get("provenance__objective_best")
        provenance = provenance_value if isinstance(provenance_value, str) else ""
        point_key = (run_id, key, evaluations)
        current = latest_points.get(point_key)
        if current is None or checkpoint_index > current[0]:
            latest_points[point_key] = (
                checkpoint_index,
                objective,
                provenance,
            )

    for key, state in coverage_state.items():
        traced_completed = sum(
            1
            for run_id in state["trace_run_ids"]
            if runs_by_id[run_id].get("run_status") == "completed"
        )
        traced_noncompleted = len(state["trace_run_ids"]) - traced_completed
        state["completed_runs_with_trace"] = traced_completed
        state["completed_runs_without_trace"] = (
            state["completed_run_count"] - traced_completed
        )
        state["noncompleted_runs_with_trace"] = traced_noncompleted

    grouped_points: dict[
        tuple[ConvergenceGroupKey, int],
        list[tuple[float, str]],
    ] = defaultdict(list)
    for (_, group_key, evaluations), (
        _,
        objective,
        provenance,
    ) in latest_points.items():
        grouped_points[(group_key, evaluations)].append((objective, provenance))

    summaries: list[ConvergenceSummary] = []
    for (key, evaluations), points in grouped_points.items():
        campaign_id, family, instance, dimension, configuration_id, identity = key
        state = coverage_state[key]
        objectives = [objective for objective, _ in points]
        ordered = sorted(objectives)
        summaries.append(
            ConvergenceSummary(
                campaign_id=campaign_id,
                instance_identity=identity,
                problem_family=family,
                instance=instance,
                dimension=dimension,
                direction=state["direction"],
                configuration_id=configuration_id,
                algorithm=state["algorithm"],
                optimizer_version=state["optimizer_version"],
                evaluations=evaluations,
                checkpoint_count=len(points),
                median_objective=statistics.median(ordered),
                q25_objective=_quantile(ordered, 0.25),
                q75_objective=_quantile(ordered, 0.75),
                observed_value_count=sum(
                    provenance == "observed" for _, provenance in points
                ),
                reconstructed_value_count=sum(
                    provenance == "reconstructed" for _, provenance in points
                ),
                expected_value_count=sum(
                    provenance == "expected" for _, provenance in points
                ),
                provenance_counts=tuple(
                    sorted(
                        Counter(
                            provenance if provenance else "unavailable"
                            for _, provenance in points
                        ).items()
                    )
                ),
            )
        )
    coverage = tuple(
        ConvergenceCoverage(
            campaign_id=campaign_id,
            instance_identity=identity,
            problem_family=family,
            instance=instance,
            dimension=dimension,
            configuration_id=configuration_id,
            completed_run_count=state["completed_run_count"],
            completed_runs_with_trace=state["completed_runs_with_trace"],
            completed_runs_without_trace=state["completed_runs_without_trace"],
            noncompleted_runs_with_trace=state["noncompleted_runs_with_trace"],
            completed_trace_points_without_objective=state[
                "completed_trace_points_without_objective"
            ],
        )
        for (
            campaign_id,
            family,
            instance,
            dimension,
            configuration_id,
            identity,
        ), state in sorted(
            coverage_state.items(),
            key=lambda item: (
                item[0][0],
                item[0][1],
                item[0][2],
                -1 if item[0][3] is None else item[0][3],
                item[0][5].instance_id,
                item[0][4],
            ),
        )
    )
    return (
        tuple(
            sorted(
                summaries,
                key=lambda item: (
                    item.campaign_id,
                    item.problem_family,
                    item.instance,
                    -1 if item.dimension is None else item.dimension,
                    item.instance_identity.instance_id,
                    item.configuration_id,
                    item.evaluations,
                ),
            )
        ),
        coverage,
    )


def summarize_convergence_curve(
    run_traces: Iterable[Iterable[float]],
    expected_run_count: int,
) -> ConvergenceCurveSummary:
    """Summarize equal-length best-fitness traces using mean and population SD.

    ``iterations`` contains zero-based sample positions, not observed iteration
    or evaluation indices. Callers must establish alignment. The expected run
    count prevents silently summarizing fewer traces than declared.
    """

    if (
        isinstance(expected_run_count, bool)
        or not isinstance(expected_run_count, int)
        or expected_run_count < 1
    ):
        raise AnalysisError("expected_run_count must be a positive integer")

    traces: list[tuple[float, ...]] = []
    for run_index, trace in enumerate(run_traces, start=1):
        if isinstance(trace, (str, bytes, bytearray)):
            raise AnalysisError(f"Trace {run_index} must be a sequence of values")
        try:
            values = tuple(float(value) for value in trace)
        except (OverflowError, TypeError, ValueError) as error:
            raise AnalysisError(
                f"Trace {run_index} contains a non-numeric objective"
            ) from error
        if not values:
            raise AnalysisError(f"Trace {run_index} has no checkpoints")
        if any(not math.isfinite(value) for value in values):
            raise AnalysisError(f"Trace {run_index} contains a non-finite objective")
        if traces and len(values) != len(traces[0]):
            raise AnalysisError(
                f"Trace {run_index} has {len(values)} checkpoints; "
                f"expected {len(traces[0])}"
            )
        traces.append(values)

    if len(traces) != expected_run_count:
        raise AnalysisError(
            f"Expected {expected_run_count} traces; received {len(traces)}"
        )

    checkpoint_count = len(traces[0])
    return ConvergenceCurveSummary(
        run_count=len(traces),
        iterations=tuple(range(checkpoint_count)),
        mean_objective=tuple(
            statistics.fmean(trace[index] for trace in traces)
            for index in range(checkpoint_count)
        ),
        population_std_objective=tuple(
            statistics.pstdev(trace[index] for trace in traces)
            for index in range(checkpoint_count)
        ),
    )


def aggregate_iteration_values(
    rows: Iterable[Mapping[str, Any]],
    group_fields: tuple[str, ...],
    iteration_field: str,
    value_field: str,
) -> tuple[IterationValueSummary, ...]:
    """Aggregate observed values by group and iteration using sample SD.

    Missing group or iteration keys are excluded, matching pandas ``groupby``.
    Missing values are ignored; groups with no numeric values remain present
    with ``None`` summaries, and single-value groups have no sample SD.
    """

    if not group_fields or len(set(group_fields)) != len(group_fields):
        raise AnalysisError("group_fields must contain unique field names")
    field_names = (*group_fields, iteration_field, value_field)
    if any(not isinstance(field, str) or not field for field in field_names):
        raise AnalysisError("Analysis field names must be non-empty strings")
    if len(set(field_names)) != len(field_names):
        raise AnalysisError("Group, iteration, and value fields must be distinct")

    groups: dict[tuple[Any, ...], list[float]] = {}
    for row_index, row in enumerate(rows, start=1):
        missing_fields = [field for field in field_names if field not in row]
        if missing_fields:
            raise AnalysisError(
                f"Iteration row {row_index} is missing fields: {missing_fields}"
            )
        key_values = tuple(row[field] for field in (*group_fields, iteration_field))
        if any(
            value is None
            or value == ""
            or isinstance(value, Number)
            and math.isnan(float(cast(SupportsFloat, value)))
            for value in key_values
        ):
            continue

        group_values = key_values[:-1]
        iteration = key_values[-1]
        key = (*group_values, iteration)
        values = groups.setdefault(key, [])
        raw_value = row[value_field]
        if raw_value is None or raw_value == "":
            continue
        try:
            value = float(raw_value)
        except (OverflowError, TypeError, ValueError) as error:
            raise AnalysisError(
                f"Iteration row {row_index} has non-numeric {value_field!r}"
            ) from error
        if math.isnan(value):
            continue
        if not math.isfinite(value):
            raise AnalysisError(
                f"Iteration row {row_index} has non-finite {value_field!r}"
            )
        values.append(value)

    try:
        ordered_keys = sorted(groups)
    except TypeError as error:
        raise AnalysisError(
            "Group and iteration values must be mutually sortable"
        ) from error

    return tuple(
        IterationValueSummary(
            group_values=key[:-1],
            iteration=key[-1],
            value_count=len(values),
            mean=statistics.fmean(values) if values else None,
            sample_std=statistics.stdev(values) if len(values) > 1 else None,
        )
        for key in ordered_keys
        for values in (groups[key],)
    )


def friedman_objective_test(
    run_rows: Iterable[Mapping[str, Any]],
    alpha: float = 0.05,
) -> tuple[FriedmanResult, ...]:
    """Run a Friedman omnibus test per campaign and problem family.

    A problem instance is a block and each configuration is a treatment. The
    per-instance statistic is the median objective across completed replicas.
    Only complete blocks containing a finite median for every configuration
    in the campaign/family are tested; incomplete blocks are reported. At
    least three configurations and two complete instances are required.
    """

    if not math.isfinite(alpha) or alpha <= 0 or alpha >= 1:
        raise AnalysisError("alpha must be finite and strictly between 0 and 1")
    summaries = summarize_objectives(run_rows)
    family_blocks: dict[
        tuple[str, str],
        dict[
            InstanceIdentity,
            dict[str, ObjectiveSummary],
        ],
    ] = defaultdict(lambda: defaultdict(dict))
    family_configurations: dict[tuple[str, str], set[str]] = defaultdict(set)

    for summary in summaries:
        family_key = (summary.campaign_id, summary.problem_family)
        block_key = summary.instance_identity
        existing = family_blocks[family_key][block_key].get(summary.configuration_id)
        if existing is not None:
            raise AnalysisError(
                f"Configuration {summary.configuration_id!r} has duplicate "
                f"records for instance {summary.instance!r}"
            )
        family_blocks[family_key][block_key][summary.configuration_id] = summary
        family_configurations[family_key].add(summary.configuration_id)

    try:
        import scipy
        from scipy.stats import friedmanchisquare
    except ImportError as error:
        raise AnalysisError(
            "Friedman tests require SciPy; install the 'analysis' extra"
        ) from error

    results: list[FriedmanResult] = []
    for family_key in sorted(family_blocks):
        campaign_id, problem_family = family_key
        configurations = tuple(sorted(family_configurations[family_key]))
        if len(configurations) < 3:
            raise AnalysisError(
                "Friedman omnibus tests require at least three configurations "
                f"for campaign {campaign_id!r}, family {problem_family!r}"
            )

        blocks = family_blocks[family_key]
        included: list[InstanceIdentity] = []
        excluded: list[InstanceIdentity] = []
        for block_key in sorted(
            blocks,
            key=lambda item: (
                item.instance,
                -1 if item.dimension is None else item.dimension,
                item.direction,
                item.instance_id,
            ),
        ):
            by_configuration = blocks[block_key]
            complete = all(
                configuration_id in by_configuration
                and by_configuration[configuration_id].median is not None
                for configuration_id in configurations
            )
            (included if complete else excluded).append(block_key)

        rank_values: dict[str, list[float]] = {
            configuration_id: [] for configuration_id in configurations
        }
        treatments: dict[str, list[float]] = {
            configuration_id: [] for configuration_id in configurations
        }
        ties_present = False
        for block_key in included:
            direction = block_key.direction
            scores: dict[str, float] = {}
            for configuration_id in configurations:
                median = blocks[block_key][configuration_id].median
                if median is None:
                    raise AnalysisError("Complete Friedman block has a missing median")
                scores[configuration_id] = (
                    median if direction == "minimize" else -median
                )
            if len(set(scores.values())) < len(scores):
                ties_present = True
            for configuration_id in configurations:
                treatments[configuration_id].append(scores[configuration_id])
            ranks = _average_ranks(scores)
            for configuration_id, rank in ranks.items():
                rank_values[configuration_id].append(rank)

        statistic: float | None = None
        p_value: float | None = None
        kendall_w: float | None = None
        reject_null: bool | None = None
        if len(included) >= 2:
            all_blocks_tied = all(
                len(
                    {
                        treatments[configuration_id][block_index]
                        for configuration_id in configurations
                    }
                )
                == 1
                for block_index in range(len(included))
            )
            if all_blocks_tied:
                statistic = 0.0
                p_value = 1.0
            else:
                result = friedmanchisquare(
                    *(
                        treatments[configuration_id]
                        for configuration_id in configurations
                    )
                )
                statistic = float(result.statistic)
                p_value = float(result.pvalue)
            kendall_w = statistic / (len(included) * (len(configurations) - 1))
            reject_null = p_value <= alpha

        average_ranks = tuple(
            (
                configuration_id,
                statistics.fmean(rank_values[configuration_id])
                if rank_values[configuration_id]
                else None,
            )
            for configuration_id in configurations
        )
        results.append(
            FriedmanResult(
                campaign_id=campaign_id,
                problem_family=problem_family,
                configurations=configurations,
                included_instances=tuple(included),
                excluded_instances=tuple(excluded),
                block_count=len(included),
                incomplete_block_count=len(excluded),
                statistic=statistic,
                p_value=p_value,
                kendall_w=kendall_w,
                ties_present=ties_present,
                average_ranks=average_ranks,
                alpha=alpha,
                reject_null=reject_null,
                test="friedman_chi_square",
                p_value_method="scipy_friedmanchisquare",
                p_value_approximation_recommended=(
                    len(included) > 10 and len(configurations) > 6
                ),
                scipy_version=scipy.__version__,
            )
        )
    return tuple(results)


def friedman_posthoc_objective_tests(
    run_rows: Iterable[Mapping[str, Any]],
    alpha: float = 0.05,
) -> tuple[FriedmanPostHocResult, ...]:
    """Run Nemenyi all-pairs post hoc comparisons after significant Friedman.

    The Nemenyi studentized-range procedure compares average within-instance
    ranks on the exact complete blocks used by the omnibus test. Its p-values
    already account for all pairs. Post hoc inference is suppressed when the
    Friedman chi-square approximation is outside SciPy's recommended range.
    """

    rows = list(run_rows)
    omnibus_results = friedman_objective_test(rows, alpha)
    summaries = summarize_objectives(rows)
    summary_by_key: dict[tuple[str, InstanceIdentity, str], ObjectiveSummary] = {}
    for summary in summaries:
        key = (
            summary.campaign_id,
            summary.instance_identity,
            summary.configuration_id,
        )
        if key in summary_by_key:
            raise AnalysisError(
                f"Configuration {summary.configuration_id!r} has duplicate "
                f"records for instance {summary.instance!r}"
            )
        summary_by_key[key] = summary

    try:
        import scipy
        from scipy.stats import studentized_range
    except ImportError as error:
        raise AnalysisError(
            "Friedman post-hoc tests require SciPy; install the 'analysis' extra"
        ) from error

    pending: list[dict[str, Any]] = []
    for omnibus in omnibus_results:
        pairs = [
            (omnibus.configurations[left], omnibus.configurations[right])
            for left in range(len(omnibus.configurations))
            for right in range(left + 1, len(omnibus.configurations))
        ]
        if omnibus.p_value is None:
            gate_status = "insufficient_omnibus_blocks"
        elif not omnibus.reject_null:
            gate_status = "omnibus_not_significant"
        elif not omnibus.p_value_approximation_recommended:
            gate_status = "omnibus_p_value_approximation_limited"
        elif omnibus.ties_present:
            gate_status = "ties_not_supported_by_nemenyi"
        else:
            gate_status = "tested"
        for baseline_id, candidate_id in pairs:
            rank_differences: list[float] = []
            if gate_status == "tested":
                for identity in omnibus.included_instances:
                    scores: dict[str, float] = {}
                    for configuration_id in omnibus.configurations:
                        median = summary_by_key[
                            (
                                omnibus.campaign_id,
                                identity,
                                configuration_id,
                            )
                        ].median
                        if median is None:
                            raise AnalysisError(
                                "Friedman complete block unexpectedly lacks a median"
                            )
                        scores[configuration_id] = (
                            median if identity.direction == "minimize" else -median
                        )
                    ranks = _average_ranks(scores)
                    rank_differences.append(ranks[baseline_id] - ranks[candidate_id])

            if gate_status != "tested":
                status = gate_status
                mean_rank_difference = None
                studentized_range_statistic = None
                p_value = None
            elif len(rank_differences) < 2:
                status = "insufficient_pairwise_blocks"
                mean_rank_difference = None
                studentized_range_statistic = None
                p_value = None
            else:
                mean_rank_difference = statistics.fmean(rank_differences)
                config_count = len(omnibus.configurations)
                scale = math.sqrt(
                    config_count * (config_count + 1) / (6 * omnibus.block_count)
                )
                studentized_range_statistic = (
                    abs(mean_rank_difference) * math.sqrt(2) / scale
                )
                p_value = float(
                    studentized_range.sf(
                        studentized_range_statistic,
                        config_count,
                        math.inf,
                    )
                )
                status = "tested"

            pending.append(
                {
                    "omnibus": omnibus,
                    "baseline_id": baseline_id,
                    "candidate_id": candidate_id,
                    "paired_count": (
                        len(rank_differences)
                        if gate_status == "tested"
                        else omnibus.block_count
                    ),
                    "status": status,
                    "mean_rank_difference": mean_rank_difference,
                    "studentized_range_statistic": studentized_range_statistic,
                    "p_value": p_value,
                }
            )

    results: list[FriedmanPostHocResult] = []
    for result in pending:
        omnibus = result["omnibus"]
        family_size = (
            len(omnibus.configurations) * (len(omnibus.configurations) - 1) // 2
        )
        family_id = (
            f"campaign={omnibus.campaign_id!r}:"
            f"problem_family={omnibus.problem_family!r}:"
            "nemenyi_all_pairs"
        )
        results.append(
            FriedmanPostHocResult(
                campaign_id=omnibus.campaign_id,
                problem_family=omnibus.problem_family,
                baseline_configuration_id=result["baseline_id"],
                candidate_configuration_id=result["candidate_id"],
                omnibus_p_value=omnibus.p_value,
                omnibus_reject_null=omnibus.reject_null,
                omnibus_p_value_approximation_recommended=(
                    omnibus.p_value_approximation_recommended
                ),
                paired_instance_count=result["paired_count"],
                status=result["status"],
                family_id=family_id,
                family_size=family_size,
                alpha=alpha,
                mean_rank_difference=result["mean_rank_difference"],
                studentized_range_statistic=result["studentized_range_statistic"],
                p_value=result["p_value"],
                reject_null=(
                    result["p_value"] <= alpha
                    if result["p_value"] is not None
                    else None
                ),
                p_value_method="nemenyi_studentized_range_infinite_df",
                scipy_version=scipy.__version__,
            )
        )
    return tuple(results)


def holm_adjust(p_values: Iterable[float]) -> tuple[float, ...]:
    """Return Holm-adjusted p-values in the same order as the input family."""

    values = tuple(float(value) for value in p_values)
    if any(not math.isfinite(value) or value < 0 or value > 1 for value in values):
        raise AnalysisError("p-values must be finite values in [0, 1]")
    ordered = sorted(enumerate(values), key=lambda item: item[1])
    adjusted = [0.0] * len(values)
    running_maximum = 0.0
    family_size = len(values)
    for rank, (original_index, p_value) in enumerate(ordered):
        candidate = min(1.0, (family_size - rank) * p_value)
        running_maximum = max(running_maximum, candidate)
        adjusted[original_index] = running_maximum
    return tuple(adjusted)


def infer_paired_objectives(
    run_rows: Iterable[Mapping[str, Any]],
    baseline_configuration_id: str,
    candidate_configuration_id: str,
    alpha: float = 0.05,
) -> tuple[PairedObjectiveTest, ...]:
    """Run two-sided paired Wilcoxon tests and Holm-adjust by campaign.

    A family comprises all testable problem-instance comparisons for this
    baseline/candidate pair within one campaign. Instances with no matched
    completed pairs are reported with no p-value and are excluded from that
    campaign's family size.
    """

    if not math.isfinite(alpha) or alpha <= 0 or alpha >= 1:
        raise AnalysisError("alpha must be finite and strictly between 0 and 1")
    rows = list(run_rows)
    comparisons = compare_paired_objectives(
        rows, baseline_configuration_id, candidate_configuration_id
    )
    try:
        import scipy
        from scipy.stats import wilcoxon
    except ImportError as error:
        raise AnalysisError(
            "Paired Wilcoxon tests require SciPy; install the 'analysis' extra"
        ) from error

    provisional: list[dict[str, Any]] = []
    for comparison in comparisons:
        key = (
            comparison.campaign_id,
            comparison.problem_family,
            comparison.instance,
            comparison.dimension,
            comparison.direction,
            comparison.instance_identity,
        )
        grouped_rows = {
            baseline_configuration_id: [],
            candidate_configuration_id: [],
        }
        for row in rows:
            if row.get("configuration_id") not in grouped_rows:
                continue
            if _group_key(row) == key:
                grouped_rows[row["configuration_id"]].append(row)
        baseline = _completed_by_pair(grouped_rows[baseline_configuration_id])
        candidate = _completed_by_pair(grouped_rows[candidate_configuration_id])
        common_pairs = baseline.keys() & candidate.keys()
        improvements = [
            (
                baseline[pair] - candidate[pair]
                if comparison.direction == "minimize"
                else candidate[pair] - baseline[pair]
            )
            for pair in sorted(common_pairs)
        ]
        if not improvements:
            provisional.append(
                {
                    "comparison": comparison,
                    "statistic": None,
                    "p_value": None,
                    "effect": None,
                    "hodges_lehmann": None,
                    "zeros": 0,
                    "nonzeros": 0,
                }
            )
            continue

        zeros = sum(value == 0 for value in improvements)
        nonzero_improvements = [value for value in improvements if value != 0]
        if nonzero_improvements:
            result = wilcoxon(
                nonzero_improvements,
                alternative="two-sided",
                method="auto",
                zero_method="wilcox",
            )
            statistic_value, p_value_value = result
            if not isinstance(statistic_value, SupportsFloat) or not isinstance(
                p_value_value, SupportsFloat
            ):
                raise AnalysisError("SciPy Wilcoxon returned nonnumeric scalar results")
            statistic = float(statistic_value)
            p_value = float(p_value_value)
            effect = _matched_pairs_rank_biserial(nonzero_improvements)
        else:
            statistic = 0.0
            p_value = 1.0
            effect = None
        hodges_lehmann = _hodges_lehmann_shift(improvements)
        provisional.append(
            {
                "comparison": comparison,
                "statistic": statistic,
                "p_value": p_value,
                "effect": effect,
                "hodges_lehmann": hodges_lehmann,
                "zeros": zeros,
                "nonzeros": len(nonzero_improvements),
            }
        )

    by_campaign: dict[str, list[int]] = defaultdict(list)
    for index, result in enumerate(provisional):
        if result["p_value"] is not None:
            by_campaign[result["comparison"].campaign_id].append(index)

    adjusted_p_values: dict[int, float] = {}
    family_sizes: dict[str, int] = {}
    for campaign_id, indices in by_campaign.items():
        adjusted = holm_adjust(provisional[index]["p_value"] for index in indices)
        family_sizes[campaign_id] = len(indices)
        adjusted_p_values.update(zip(indices, adjusted))

    return tuple(
        PairedObjectiveTest(
            comparison=result["comparison"],
            test="wilcoxon_signed_rank_two_sided",
            correction="holm",
            family_id=(
                f"campaign={result['comparison'].campaign_id!r}:"
                f"{baseline_configuration_id!r}:"
                f"{candidate_configuration_id!r}:problem_instances"
            ),
            family_size=family_sizes.get(result["comparison"].campaign_id, 0),
            alpha=alpha,
            statistic=result["statistic"],
            raw_p_value=result["p_value"],
            adjusted_p_value=adjusted_p_values.get(index),
            reject_null=(
                adjusted_p_values[index] <= alpha
                if index in adjusted_p_values
                else None
            ),
            rank_biserial_effect=result["effect"],
            hodges_lehmann_effect=result["hodges_lehmann"],
            zero_difference_count=result["zeros"],
            nonzero_difference_count=result["nonzeros"],
            p_value_method="scipy_wilcoxon_auto",
            scipy_version=scipy.__version__,
        )
        for index, result in enumerate(provisional)
    )


def _hodges_lehmann_shift(differences: list[float]) -> float | None:
    """Return the paired Hodges-Lehmann shift estimate from Walsh averages."""

    if not differences:
        return None
    walsh_averages = [
        (left + right) / 2
        for index, left in enumerate(differences)
        for right in differences[index:]
    ]
    return statistics.median(walsh_averages)


def _matched_pairs_rank_biserial(improvements: list[float]) -> float | None:
    """Calculate rank-biserial effect, with positive values favoring candidate."""

    ordered = sorted(abs(value) for value in improvements if value != 0)
    if not ordered:
        return None
    positive_rank_sum = 0.0
    negative_rank_sum = 0.0
    start = 0
    while start < len(ordered):
        end = start + 1
        while end < len(ordered) and ordered[end] == ordered[start]:
            end += 1
        average_rank = ((start + 1) + end) / 2
        for value in improvements:
            if value != 0 and abs(value) == ordered[start]:
                if value > 0:
                    positive_rank_sum += average_rank
                else:
                    negative_rank_sum += average_rank
        start = end
    rank_sum = positive_rank_sum + negative_rank_sum
    return (positive_rank_sum - negative_rank_sum) / rank_sum if rank_sum else None


def _completed_by_pair(
    rows: list[Mapping[str, Any]],
) -> dict[tuple[int, int], float]:
    completed: dict[tuple[int, int], float] = {}
    for row in rows:
        if row.get("run_status") != "completed":
            continue
        replica_index = row.get("replica_index")
        random_seed = row.get("random_seed")
        try:
            if replica_index is None or random_seed is None:
                raise TypeError("replica identity cannot be None")
            pair = (int(replica_index), int(random_seed))
        except (TypeError, ValueError) as error:
            raise AnalysisError(
                "Paired comparisons require integer replica_index and random_seed"
            ) from error
        if pair in completed:
            raise AnalysisError(
                f"Duplicate completed run for replica/seed pair {pair!r}"
            )
        completed[pair] = _objective(row)
    return completed
