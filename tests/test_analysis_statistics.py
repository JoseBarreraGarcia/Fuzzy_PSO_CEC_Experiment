import csv
from pathlib import Path
import sys
import unittest

SRC = Path(__file__).resolve().parents[1] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from afcs.analysis import (
    AnalysisError,
    aggregate_iteration_values,
    aggregate_objective_ranks,
    compare_paired_objectives,
    friedman_objective_test,
    friedman_posthoc_objective_tests,
    holm_adjust,
    infer_paired_objectives,
    summarize_convergence,
    summarize_convergence_curve,
    summarize_objectives,
)


FIXTURES = Path(__file__).with_name("fixtures")


def load_run_fixture():
    with (FIXTURES / "analysis_runs.csv").open(
        newline="", encoding="utf-8"
    ) as file:
        return list(csv.DictReader(file))


def make_friedman_fixture():
    rows = []
    directions = ("minimize", "minimize", "maximize", "minimize")
    for instance_index, direction in enumerate(directions):
        scale = 10.0**instance_index
        values = (
            (scale, 2 * scale, 3 * scale)
            if direction == "minimize"
            else (3 * scale, 2 * scale, scale)
        )
        for config_index, configuration_id in enumerate(
            ("config-a", "config-b", "config-c")
        ):
            for replica_index in range(3):
                rows.append(
                    {
                        "campaign_id": "friedman-campaign",
                        "configuration_id": configuration_id,
                        "problem_family": "BEN",
                        "instance": f"F{instance_index + 1}",
                        "dimension": "10",
                        "direction": direction,
                        "algorithm": configuration_id.upper(),
                        "optimizer_version": "1",
                        "replica_index": str(replica_index),
                        "random_seed": str(3000 + replica_index),
                        "run_status": "completed",
                        "objective_best": str(
                            values[config_index] + replica_index * scale / 100
                        ),
                    }
                )
    for configuration_id in ("config-a", "config-b"):
        rows.append(
            {
                **rows[0],
                "configuration_id": configuration_id,
                "algorithm": configuration_id.upper(),
                "instance": "F5",
                "replica_index": "0",
                "random_seed": "3000",
                "objective_best": "1.0",
            }
        )
    return rows


def make_scale_heterogeneity_fixture():
    rows = []
    block_values = (
        (1.0, 100.0, 1000.0),
        (100.0, 1.0, 1000.0),
        (1_000_000.0, 1_000_001.0, 1_000_002.0),
        (100_000_000.0, 1.0, 1_000_000_000.0),
    )
    for instance_index, values in enumerate(block_values):
        for config_index, configuration_id in enumerate(
            ("config-a", "config-b", "config-c")
        ):
            rows.append(
                {
                    "campaign_id": "scale-campaign",
                    "configuration_id": configuration_id,
                    "problem_family": "BEN",
                    "instance": f"F{instance_index + 1}",
                    "dimension": "10",
                    "direction": "minimize",
                    "algorithm": configuration_id.upper(),
                    "optimizer_version": "1",
                    "replica_index": "0",
                    "random_seed": "4000",
                    "run_status": "completed",
                    "objective_best": str(values[config_index]),
                }
            )
    return rows


def make_reliable_friedman_fixture():
    rows = []
    configurations = tuple(f"config-{index}" for index in range(7))
    for instance_index in range(11):
        scale = 10.0**instance_index
        for config_index, configuration_id in enumerate(configurations):
            rows.append(
                {
                    "campaign_id": "reliable-friedman-campaign",
                    "configuration_id": configuration_id,
                    "problem_family": "BEN",
                    "instance": f"F{instance_index + 1}",
                    "dimension": "10",
                    "direction": "minimize",
                    "algorithm": configuration_id.upper(),
                    "optimizer_version": "1",
                    "replica_index": "0",
                    "random_seed": "5000",
                    "run_status": "completed",
                    "objective_best": str((config_index + 1) * scale),
                }
            )
    return rows


class TestAnalysisStatistics(unittest.TestCase):
    def test_legacy_iteration_aggregation_preserves_sample_statistics(self):
        summaries = aggregate_iteration_values(
            [
                {"MH": "PSO", "funcion": "F1", "iter": 0, "fitness": 2.0},
                {"MH": "PSO", "funcion": "F1", "iter": 0, "fitness": 4.0},
                {"MH": "PSO", "funcion": "F1", "iter": 0, "fitness": float("nan")},
                {"MH": "PSO", "funcion": "F1", "iter": 1, "fitness": 5.0},
                {"MH": "GA", "funcion": "F1", "iter": 0, "fitness": 8.0},
                {"MH": "PSO", "funcion": "F2", "iter": 0, "fitness": None},
                {"MH": None, "funcion": "F1", "iter": 0, "fitness": 99.0},
            ],
            group_fields=("MH", "funcion"),
            iteration_field="iter",
            value_field="fitness",
        )

        self.assertEqual(len(summaries), 4)
        pso_f1_iter0 = summaries[1]
        self.assertEqual(pso_f1_iter0.group_values, ("PSO", "F1"))
        self.assertEqual(pso_f1_iter0.iteration, 0)
        self.assertEqual(pso_f1_iter0.value_count, 2)
        self.assertEqual(pso_f1_iter0.mean, 3.0)
        self.assertAlmostEqual(pso_f1_iter0.sample_std, 2**0.5)
        self.assertIsNone(summaries[2].sample_std)
        self.assertEqual(summaries[3].value_count, 0)
        self.assertIsNone(summaries[3].mean)

    def test_iteration_aggregation_rejects_non_numeric_values(self):
        with self.assertRaisesRegex(AnalysisError, "non-numeric"):
            aggregate_iteration_values(
                [{"MH": "PSO", "funcion": "F1", "iter": 0, "fitness": "bad"}],
                group_fields=("MH", "funcion"),
                iteration_field="iter",
                value_field="fitness",
            )

    def test_legacy_convergence_adapter_preserves_dataframe_shape(self):
        import pandas as pd

        from analysis_modules_cec.convergence_curves_cec import aggregate_by_iter

        frame = pd.DataFrame(
            [
                {"MH": "PSO", "funcion": "F1", "iter": 0, "best_fitness": 2.0},
                {"MH": "PSO", "funcion": "F1", "iter": 0, "best_fitness": 4.0},
                {"MH": "PSO", "funcion": "F1", "iter": 1, "best_fitness": 5.0},
                {"MH": "GA", "funcion": "F1", "iter": 0, "best_fitness": 8.0},
            ]
        )

        result = aggregate_by_iter(frame)

        self.assertEqual(
            list(result.columns),
            ["MH", "funcion", "iter", "best_fitness_mean", "best_fitness_std"],
        )
        self.assertEqual(
            list(result[["MH", "funcion", "iter"]].itertuples(index=False, name=None)),
            [("GA", "F1", 0), ("PSO", "F1", 0), ("PSO", "F1", 1)],
        )
        pso_first_iteration = result.iloc[1]
        self.assertEqual(pso_first_iteration["best_fitness_mean"], 3.0)
        self.assertAlmostEqual(pso_first_iteration["best_fitness_std"], 2**0.5)

    def test_descriptive_summaries_group_by_instance_and_configuration(self):
        rows = load_run_fixture()
        rows.append(
            {
                **rows[0],
                "run_id": "failed-extra",
                "replica_index": "2",
                "random_seed": "1003",
                "run_status": "failed",
                "objective_best": "",
            }
        )

        summaries = summarize_objectives(rows)

        self.assertEqual(len(summaries), 4)
        pso_f1 = next(
            item
            for item in summaries
            if item.instance == "F1" and item.configuration_id == "pso"
        )
        self.assertEqual(pso_f1.run_count, 3)
        self.assertEqual(pso_f1.completed_count, 2)
        self.assertEqual(pso_f1.status_counts, (("completed", 2), ("failed", 1)))
        self.assertEqual(
            pso_f1.objective_provenance_counts, (("unavailable", 2),)
        )
        self.assertAlmostEqual(pso_f1.mean, 0.3)
        self.assertAlmostEqual(pso_f1.sample_std, 0.1414213562373095)
        self.assertAlmostEqual(pso_f1.median, 0.3)
        self.assertAlmostEqual(pso_f1.q25, 0.25)
        self.assertAlmostEqual(pso_f1.q75, 0.35)
        self.assertAlmostEqual(pso_f1.minimum, 0.2)
        self.assertAlmostEqual(pso_f1.maximum, 0.4)

    def test_paired_objectives_use_shared_seeds_and_orient_improvement(self):
        summaries = compare_paired_objectives(
            load_run_fixture(), "pso", "fcs"
        )

        self.assertEqual(len(summaries), 2)
        f1 = next(item for item in summaries if item.instance == "F1")
        self.assertEqual(f1.instance, "F1")
        self.assertEqual(f1.paired_count, 2)
        self.assertEqual(f1.baseline_unpaired_count, 0)
        self.assertEqual(f1.candidate_unpaired_count, 0)
        self.assertAlmostEqual(f1.mean_baseline, 0.3)
        self.assertAlmostEqual(f1.mean_candidate, 0.075)
        self.assertAlmostEqual(f1.mean_improvement, 0.225)
        self.assertAlmostEqual(f1.median_improvement, 0.225)
        self.assertAlmostEqual(f1.sample_std_improvement, 0.1060660171779821)
        self.assertAlmostEqual(f1.minimum_improvement, 0.15)
        self.assertAlmostEqual(f1.maximum_improvement, 0.3)

        f3 = next(item for item in summaries if item.instance == "F3")
        self.assertEqual(f3.instance, "F3")
        self.assertAlmostEqual(f3.mean_improvement, 0.25)

    def test_unmatched_seeds_are_reported_not_paired(self):
        rows = load_run_fixture()
        candidate = next(
            row
            for row in rows
            if row["configuration_id"] == "fcs"
            and row["replica_index"] == "1"
        )
        candidate["random_seed"] = "9999"

        summary = next(
            item
            for item in compare_paired_objectives(rows, "pso", "fcs")
            if item.instance == "F1"
        )

        self.assertEqual(summary.paired_count, 1)
        self.assertEqual(summary.baseline_unpaired_count, 1)
        self.assertEqual(summary.candidate_unpaired_count, 1)

    def test_maximization_improvement_is_candidate_minus_baseline(self):
        rows = [
            {
                **load_run_fixture()[0],
                "direction": "maximize",
                "configuration_id": "baseline",
                "objective_best": "5",
            },
            {
                **load_run_fixture()[0],
                "direction": "maximize",
                "configuration_id": "candidate",
                "objective_best": "7",
            },
        ]

        summary = compare_paired_objectives(rows, "baseline", "candidate")[0]
        self.assertEqual(summary.paired_count, 1)
        self.assertEqual(summary.mean_improvement, 2.0)

    def test_invalid_completed_objective_and_duplicate_pair_are_rejected(self):
        rows = load_run_fixture()
        rows[0]["objective_best"] = "nan"
        with self.assertRaisesRegex(AnalysisError, "finite"):
            summarize_objectives(rows)

        rows = load_run_fixture()
        rows.append(dict(rows[0]))
        with self.assertRaisesRegex(AnalysisError, "Duplicate completed run"):
            compare_paired_objectives(rows, "pso", "fcs")

    def test_aggregate_ranks_do_not_pool_different_objective_scales(self):
        ranks = aggregate_objective_ranks(load_run_fixture())

        self.assertEqual(len(ranks), 2)
        candidate, baseline = ranks
        self.assertEqual(candidate.configuration_id, "fcs")
        self.assertEqual(baseline.configuration_id, "pso")
        self.assertEqual(candidate.instances_ranked, 2)
        self.assertEqual(candidate.total_instances, 2)
        self.assertEqual(candidate.mean_rank, 1.0)
        self.assertEqual(candidate.unique_best_count, 2)
        self.assertEqual(baseline.mean_rank, 2.0)
        self.assertEqual(baseline.worst_count, 2)

    def test_aggregate_rank_ties_receive_average_rank(self):
        rows = load_run_fixture()
        for row in rows:
            row["configuration_id"] = "config-a" if row["configuration_id"] == "pso" else "config-b"
        tied = [
            {
                **rows[2],
                "configuration_id": "config-c",
                "algorithm": "GA",
                "replica_index": "0",
                "random_seed": "2001",
            },
            {
                **rows[3],
                "configuration_id": "config-c",
                "algorithm": "GA",
                "replica_index": "1",
                "random_seed": "2002",
            },
        ]

        ranks = aggregate_objective_ranks(rows + tied)
        rank_by_config = {item.configuration_id: item for item in ranks}
        self.assertEqual(rank_by_config["config-a"].mean_rank, 2.5)
        self.assertEqual(rank_by_config["config-b"].mean_rank, 1.25)
        self.assertEqual(rank_by_config["config-c"].mean_rank, 1.5)
        self.assertEqual(rank_by_config["config-b"].tied_best_count, 1)
        self.assertEqual(rank_by_config["config-c"].tied_best_count, 1)

    def test_aggregate_ranks_respect_maximization_direction(self):
        rows = load_run_fixture()
        for row in rows:
            row["direction"] = "maximize"

        ranks = aggregate_objective_ranks(rows)

        self.assertEqual(ranks[0].configuration_id, "pso")
        self.assertEqual(ranks[0].mean_rank, 1.0)
        self.assertEqual(ranks[1].configuration_id, "fcs")
        self.assertEqual(ranks[1].mean_rank, 2.0)

    def test_holm_adjustment_preserves_input_order_and_known_values(self):
        self.assertEqual(holm_adjust([0.04, 0.01, 0.03]), (0.06, 0.03, 0.06))
        with self.assertRaisesRegex(AnalysisError, "p-values"):
            holm_adjust([0.2, float("nan")])

    def test_paired_wilcoxon_and_holm_are_reported_by_campaign_family(self):
        results = infer_paired_objectives(load_run_fixture(), "pso", "fcs")

        self.assertEqual(len(results), 2)
        self.assertEqual({item.family_size for item in results}, {2})
        self.assertEqual({item.correction for item in results}, {"holm"})
        for result in results:
            self.assertEqual(result.test, "wilcoxon_signed_rank_two_sided")
            self.assertEqual(result.comparison.paired_count, 2)
            self.assertEqual(result.nonzero_difference_count, 2)
            self.assertEqual(result.zero_difference_count, 0)
            self.assertAlmostEqual(result.rank_biserial_effect, 1.0)
            self.assertAlmostEqual(
                result.hodges_lehmann_effect,
                0.225 if result.comparison.instance == "F1" else 0.25,
            )
            self.assertAlmostEqual(result.raw_p_value, 0.5)
            self.assertAlmostEqual(result.adjusted_p_value, 1.0)
            self.assertFalse(result.reject_null)

    def test_paired_test_reports_zero_only_differences_without_effect(self):
        rows = load_run_fixture()
        candidate_rows = [
            {
                **row,
                "configuration_id": "same",
                "algorithm": "GA",
            }
            for row in rows
            if row["configuration_id"] == "pso"
        ]
        results = infer_paired_objectives(rows + candidate_rows, "pso", "same")

        self.assertEqual(len(results), 2)
        for result in results:
            self.assertEqual(result.raw_p_value, 1.0)
            self.assertEqual(result.adjusted_p_value, 1.0)
            self.assertIsNone(result.rank_biserial_effect)
            self.assertEqual(result.hodges_lehmann_effect, 0.0)
            self.assertEqual(result.zero_difference_count, 2)
            self.assertEqual(result.nonzero_difference_count, 0)

    def test_hodges_lehmann_shift_includes_zero_paired_differences(self):
        rows = load_run_fixture()
        candidate_rows = [
            {
                **row,
                "configuration_id": "candidate",
                "algorithm": "GA",
                "objective_best": (
                    row["objective_best"]
                    if row["instance"] == "F1" and row["replica_index"] == "0"
                    else str(float(row["objective_best"]) - 0.2)
                ),
            }
            for row in rows
            if row["configuration_id"] == "pso"
        ]

        results = infer_paired_objectives(
            rows + candidate_rows, "pso", "candidate"
        )

        f1 = next(item for item in results if item.comparison.instance == "F1")
        self.assertEqual(f1.zero_difference_count, 1)
        self.assertEqual(f1.nonzero_difference_count, 1)
        self.assertAlmostEqual(f1.hodges_lehmann_effect, 0.1)

    def test_convergence_uses_latest_checkpoint_at_exact_evaluation_count(self):
        run_rows = [
            {
                "run_id": "run-1",
                "campaign_id": "campaign",
                "problem_family": "BEN",
                "instance": "F1",
                "dimension": "10",
                "direction": "minimize",
                "configuration_id": "pso",
                "algorithm": "PSO",
                "optimizer_version": "2",
                "run_status": "completed",
            },
            {
                "run_id": "run-2",
                "campaign_id": "campaign",
                "problem_family": "BEN",
                "instance": "F1",
                "dimension": "10",
                "direction": "minimize",
                "configuration_id": "pso",
                "algorithm": "PSO",
                "optimizer_version": "2",
                "run_status": "completed",
            },
            {
                "run_id": "run-3",
                "campaign_id": "campaign",
                "problem_family": "BEN",
                "instance": "F1",
                "dimension": "10",
                "direction": "minimize",
                "configuration_id": "pso",
                "algorithm": "PSO",
                "optimizer_version": "2",
                "run_status": "failed",
            },
        ]
        trace_rows = [
            {
                "run_id": "run-1",
                "campaign_id": "campaign",
                "problem_family": "BEN",
                "instance": "F1",
                "dimension": "10",
                "configuration_id": "pso",
                "checkpoint_index": "0",
                "evaluations": "5",
                "metric__objective_best": "10",
                "provenance__objective_best": "observed",
            },
            {
                "run_id": "run-1",
                "campaign_id": "campaign",
                "problem_family": "BEN",
                "instance": "F1",
                "dimension": "10",
                "configuration_id": "pso",
                "checkpoint_index": "1",
                "evaluations": "5",
                "metric__objective_best": "8",
                "provenance__objective_best": "reconstructed",
            },
            {
                "run_id": "run-1",
                "campaign_id": "campaign",
                "problem_family": "BEN",
                "instance": "F1",
                "dimension": "10",
                "configuration_id": "pso",
                "checkpoint_index": "2",
                "evaluations": "10",
                "metric__objective_best": "",
                "provenance__objective_best": "",
            },
            {
                "run_id": "run-2",
                "campaign_id": "campaign",
                "problem_family": "BEN",
                "instance": "F1",
                "dimension": "10",
                "configuration_id": "pso",
                "checkpoint_index": "0",
                "evaluations": "5",
                "metric__objective_best": "12",
                "provenance__objective_best": "expected",
            },
            {
                "run_id": "run-3",
                "campaign_id": "campaign",
                "problem_family": "BEN",
                "instance": "F1",
                "dimension": "10",
                "configuration_id": "pso",
                "checkpoint_index": "0",
                "evaluations": "5",
                "metric__objective_best": "1",
                "provenance__objective_best": "observed",
            },
        ]

        summaries, coverage = summarize_convergence(run_rows, trace_rows)

        self.assertEqual(len(summaries), 1)
        summary = summaries[0]
        self.assertEqual(summary.evaluations, 5)
        self.assertEqual(summary.checkpoint_count, 2)
        self.assertEqual(summary.median_objective, 10)
        self.assertEqual(summary.q25_objective, 9)
        self.assertEqual(summary.q75_objective, 11)
        self.assertEqual(summary.observed_value_count, 0)
        self.assertEqual(summary.reconstructed_value_count, 1)
        self.assertEqual(summary.expected_value_count, 1)
        self.assertEqual(
            summary.provenance_counts,
            (("expected", 1), ("reconstructed", 1)),
        )
        self.assertEqual(len(coverage), 1)
        self.assertEqual(coverage[0].completed_run_count, 2)
        self.assertEqual(coverage[0].completed_runs_with_trace, 2)
        self.assertEqual(coverage[0].completed_runs_without_trace, 0)
        self.assertEqual(coverage[0].noncompleted_runs_with_trace, 1)
        self.assertEqual(coverage[0].completed_trace_points_without_objective, 1)

    def test_convergence_reports_completed_runs_without_trace(self):
        run_rows = [
            {
                "run_id": "run-1",
                "campaign_id": "campaign",
                "problem_family": "BEN",
                "instance": "F1",
                "dimension": "10",
                "direction": "minimize",
                "configuration_id": "pso",
                "algorithm": "PSO",
                "optimizer_version": "2",
                "run_status": "completed",
            }
        ]

        summaries, coverage = summarize_convergence(run_rows, [])

        self.assertEqual(summaries, ())
        self.assertEqual(coverage[0].completed_run_count, 1)
        self.assertEqual(coverage[0].completed_runs_with_trace, 0)
        self.assertEqual(coverage[0].completed_runs_without_trace, 1)

    def test_convergence_curve_uses_mean_and_population_std_for_expected_runs(self):
        traces = [
            (float(run_index), float(run_index * 2))
            for run_index in range(31)
        ]

        summary = summarize_convergence_curve(traces, expected_run_count=31)

        self.assertEqual(summary.run_count, 31)
        self.assertEqual(summary.iterations, (0, 1))
        self.assertEqual(summary.mean_objective, (15.0, 30.0))
        self.assertAlmostEqual(summary.population_std_objective[0], 80.0**0.5)
        self.assertAlmostEqual(summary.population_std_objective[1], 320.0**0.5)

    def test_convergence_curve_rejects_missing_runs_and_ragged_traces(self):
        with self.assertRaisesRegex(AnalysisError, "Expected 31 traces; received 30"):
            summarize_convergence_curve([(1.0,)] * 30, expected_run_count=31)

        with self.assertRaisesRegex(AnalysisError, "Trace 2 has 2 checkpoints"):
            summarize_convergence_curve(
                [(1.0,), (1.0, 2.0)],
                expected_run_count=2,
            )

    def test_convergence_curve_rejects_empty_or_nonfinite_traces(self):
        with self.assertRaisesRegex(AnalysisError, "no checkpoints"):
            summarize_convergence_curve([()], expected_run_count=1)

        with self.assertRaisesRegex(AnalysisError, "non-finite objective"):
            summarize_convergence_curve(
                [(float("nan"),)],
                expected_run_count=1,
            )

    def test_convergence_curve_requires_positive_integer_run_count(self):
        for expected_run_count in (0, -1, True, 1.5):
            with self.subTest(expected_run_count=expected_run_count):
                with self.assertRaisesRegex(
                    AnalysisError,
                    "expected_run_count must be a positive integer",
                ):
                    summarize_convergence_curve(
                        [(1.0,)],
                        expected_run_count=expected_run_count,
                    )

    def test_friedman_omnibus_uses_complete_instance_blocks_and_reports_effect(self):
        result = friedman_objective_test(make_friedman_fixture())[0]

        self.assertEqual(result.configurations, ("config-a", "config-b", "config-c"))
        self.assertEqual(result.block_count, 4)
        self.assertEqual(result.incomplete_block_count, 1)
        self.assertEqual(len(result.included_instances), 4)
        self.assertEqual(result.excluded_instances, (("F5", 10, "minimize"),))
        self.assertFalse(result.p_value_approximation_recommended)
        self.assertAlmostEqual(result.statistic, 8.0)
        self.assertAlmostEqual(result.kendall_w, 1.0)
        self.assertLess(result.p_value, 0.05)
        self.assertTrue(result.reject_null)
        self.assertEqual(
            result.average_ranks,
            (("config-a", 1.0), ("config-b", 2.0), ("config-c", 3.0)),
        )

    def test_friedman_incomplete_blocks_are_excluded_and_two_configurations_rejected(self):
        rows = load_run_fixture()
        with self.assertRaisesRegex(AnalysisError, "at least three configurations"):
            friedman_objective_test(rows)

    def test_friedman_handles_ties_and_requires_two_complete_blocks(self):
        rows = make_friedman_fixture()
        f2_rows = [
            row for row in rows
            if row["instance"] == "F2" and row["configuration_id"] == "config-c"
        ]
        rows = [
            row for row in rows
            if not (row["instance"] == "F2" and row["configuration_id"] == "config-c")
        ]
        for row in f2_rows:
            row["objective_best"] = "20.1"
        rows.extend(f2_rows)

        result = friedman_objective_test(rows)[0]
        self.assertEqual(result.block_count, 4)
        self.assertTrue(result.ties_present)
        self.assertEqual(result.average_ranks[1], ("config-b", 2.125))
        self.assertEqual(result.average_ranks[2], ("config-c", 2.875))

        only_one_complete_block = [
            row for row in rows
            if row["instance"] == "F1"
            or (
                row["instance"] == "F5"
                and row["configuration_id"] in {"config-a", "config-b"}
            )
        ]
        insufficient = friedman_objective_test(only_one_complete_block)[0]
        self.assertEqual(insufficient.block_count, 1)
        self.assertIsNone(insufficient.statistic)
        self.assertIsNone(insufficient.p_value)

    def test_friedman_posthoc_uses_nemenyi_and_its_all_pairs_adjustment(self):
        rows = make_reliable_friedman_fixture()
        omnibus = friedman_objective_test(rows)[0]
        results = friedman_posthoc_objective_tests(rows)

        self.assertTrue(omnibus.p_value_approximation_recommended)
        self.assertTrue(omnibus.reject_null)
        self.assertEqual(len(results), 21)
        self.assertEqual({item.status for item in results}, {"tested"})
        self.assertEqual({item.family_size for item in results}, {21})
        self.assertEqual({item.paired_instance_count for item in results}, {11})
        self.assertEqual({item.omnibus_reject_null for item in results}, {True})
        self.assertEqual(
            {item.family_id for item in results},
            {
                "campaign='reliable-friedman-campaign':problem_family='BEN':"
                "nemenyi_all_pairs"
            },
        )
        top_pair = next(
            item
            for item in results
            if item.baseline_configuration_id == "config-0"
            and item.candidate_configuration_id == "config-6"
        )
        self.assertEqual(top_pair.mean_rank_difference, -6.0)
        self.assertGreater(top_pair.studentized_range_statistic, 9.0)
        self.assertLess(top_pair.p_value, 0.001)
        self.assertEqual(top_pair.p_value_method, "nemenyi_studentized_range_infinite_df")
        self.assertTrue(top_pair.reject_null)
        adjacent_pair = next(
            item
            for item in results
            if item.baseline_configuration_id == "config-0"
            and item.candidate_configuration_id == "config-1"
        )
        self.assertEqual(adjacent_pair.mean_rank_difference, -1.0)
        self.assertGreater(adjacent_pair.p_value, 0.05)

    def test_friedman_posthoc_is_suppressed_when_blocks_contain_ties(self):
        rows = make_reliable_friedman_fixture()
        for row in rows:
            if row["instance"] == "F1" and row["configuration_id"] == "config-1":
                row["objective_best"] = "1.0"

        omnibus = friedman_objective_test(rows)[0]
        results = friedman_posthoc_objective_tests(rows)

        self.assertTrue(omnibus.p_value_approximation_recommended)
        self.assertTrue(omnibus.ties_present)
        self.assertTrue(omnibus.reject_null)
        self.assertEqual(
            {result.status for result in results},
            {"ties_not_supported_by_nemenyi"},
        )
        self.assertTrue(all(result.p_value is None for result in results))

    def test_friedman_posthoc_is_not_run_when_omnibus_is_not_significant(self):
        rows = make_reliable_friedman_fixture()
        for row in rows:
            row["objective_best"] = "1.0"

        results = friedman_posthoc_objective_tests(rows)

        self.assertEqual(len(results), 21)
        for result in results:
            self.assertEqual(result.status, "omnibus_not_significant")
            self.assertEqual(result.paired_instance_count, 11)
            self.assertEqual(result.omnibus_p_value, 1.0)
            self.assertFalse(result.omnibus_reject_null)
            self.assertEqual(result.family_size, 21)
            self.assertIsNone(result.p_value)
            self.assertIsNone(result.reject_null)

    def test_friedman_posthoc_marks_insufficient_omnibus_blocks(self):
        rows = [
            row
            for row in make_friedman_fixture()
            if row["instance"] in {"F1", "F5"}
        ]

        results = friedman_posthoc_objective_tests(rows)

        self.assertEqual(len(results), 3)
        for result in results:
            self.assertEqual(result.status, "insufficient_omnibus_blocks")
            self.assertEqual(result.paired_instance_count, 1)
            self.assertEqual(result.family_size, 3)
            self.assertIsNone(result.p_value)

    def test_friedman_posthoc_uses_within_instance_ranks_not_raw_scales(self):
        results = friedman_posthoc_objective_tests(
            make_scale_heterogeneity_fixture()
        )

        self.assertEqual(len(results), 3)
        ab = next(
            result
            for result in results
            if result.baseline_configuration_id == "config-a"
            and result.candidate_configuration_id == "config-b"
        )
        self.assertFalse(ab.omnibus_p_value_approximation_recommended)
        self.assertEqual(ab.status, "omnibus_p_value_approximation_limited")
        self.assertEqual(ab.paired_instance_count, 4)
        self.assertIsNone(ab.p_value)


if __name__ == "__main__":
    unittest.main()
