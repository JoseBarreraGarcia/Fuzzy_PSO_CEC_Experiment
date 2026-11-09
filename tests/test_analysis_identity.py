import csv
import json
import sqlite3
import tempfile
import unittest
from dataclasses import asdict
from pathlib import Path
from unittest.mock import patch

from afcs.analysis import (
    AnalysisError,
    AnalysisExportError,
    aggregate_objective_ranks,
    build_campaign_analysis_report,
    compare_paired_objectives,
    export_campaign_csv,
    friedman_objective_test,
    friedman_posthoc_objective_tests,
    infer_paired_objectives,
    load_reconciled_campaign_data,
    run_campaign_analysis,
    summarize_convergence,
    summarize_objectives,
)
from afcs.metrics import load_metric_registry
from afcs.persistence import ExperimentRepository, apply_migrations


class TestAnalysisInstanceIdentity(unittest.TestCase):
    def setUp(self):
        self.connection = sqlite3.connect(":memory:")
        self.connection.row_factory = sqlite3.Row
        self.addCleanup(self.connection.close)
        self.connection.execute("PRAGMA foreign_keys=ON")
        apply_migrations(self.connection)
        self.repository = ExperimentRepository(self.connection, load_metric_registry())
        self.repository.create_campaign(
            "variants", "Variants", {}, "test", "convergence"
        )
        self.instances = [
            self.repository.add_problem_instance(
                "test", "same-name", 2, 0.0, parameters={"variant": variant}
            )
            for variant in ("one", "two")
        ]
        for config in ("a", "b", "c"):
            self.repository.add_algorithm_configuration(
                config,
                "variants",
                "GA",
                "test",
                {},
                "evaluations",
                budget_evaluations=8,
            )
        runs = []
        for instance, values in zip(
            self.instances, ((0.0, 1.0, 2.0), (100.0, 102.0, 101.0))
        ):
            for config, value in zip(("a", "b", "c"), values):
                run = self.repository.plan_run(
                    "variants", config, instance, 0, random_seed=42
                )
                runs.append((run, value))
        self.repository.start_campaign("variants")
        for run, value in runs:
            self.repository.start_run(run)
            self.repository.record_trace(run, 0, 0, 8, {"objective_best": value})
            self.repository.complete_run(
                run, value, [0.0, 0.0], 8, 0.01, metrics={"objective_best": value}
            )
        self.repository.finish_campaign("variants")
        self.repository.seal_campaign("variants")
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.runs = self.root / "runs.csv"
        self.traces = self.root / "traces.csv"
        export_campaign_csv(self.connection, "variants", self.runs, self.traces)
        self.rows, self.points, _ = load_reconciled_campaign_data(
            self.connection, "variants", self.runs, self.traces
        )

    def test_objective_summaries_do_not_pool_variants(self):
        summaries = summarize_objectives(self.rows)
        self.assertEqual(len(summaries), 6)
        baseline = [summary for summary in summaries if summary.configuration_id == "a"]
        self.assertEqual([item.mean for item in baseline], [0.0, 100.0])
        self.assertEqual(
            [item.instance_identity.instance_id for item in baseline], self.instances
        )
        self.assertEqual(
            {item.instance_identity.parameters_json for item in baseline},
            {'{"variant":"one"}', '{"variant":"two"}'},
        )
        self.assertEqual(
            len({item.instance_identity.semantic_sha256 for item in baseline}), 2
        )

    def test_pairing_and_wilcoxon_families_are_separate_per_instance(self):
        comparisons = compare_paired_objectives(self.rows, "a", "b")
        self.assertEqual([item.mean_improvement for item in comparisons], [-1.0, -2.0])
        self.assertEqual([item.paired_count for item in comparisons], [1, 1])
        tests = infer_paired_objectives(self.rows, "a", "b")
        self.assertEqual(len(tests), 2)
        self.assertTrue(all(item.family_size == 2 for item in tests))
        self.assertEqual(
            {item.comparison.instance_identity.instance_id for item in tests},
            set(self.instances),
        )

    def test_rank_and_friedman_blocks_keep_variants(self):
        ranks = {
            item.configuration_id: item for item in aggregate_objective_ranks(self.rows)
        }
        self.assertEqual(ranks["b"].total_instances, 2)
        self.assertEqual(
            {item.instance_id for item in ranks["b"].ranked_instances},
            set(self.instances),
        )
        self.assertEqual(ranks["b"].available_instances, ranks["b"].ranked_instances)
        self.assertEqual(ranks["b"].mean_rank, 2.5)
        self.assertEqual(ranks["c"].mean_rank, 2.5)
        (result,) = friedman_objective_test(self.rows)
        self.assertEqual(result.block_count, 2)
        self.assertEqual(
            [item.instance_id for item in result.included_instances], self.instances
        )
        self.assertEqual(dict(result.average_ranks), {"a": 1.0, "b": 2.5, "c": 2.5})

    def test_convergence_and_coverage_keep_variants(self):
        summaries, coverage = summarize_convergence(self.rows, self.points)
        self.assertEqual(len(summaries), 6)
        self.assertEqual(len(coverage), 6)
        self.assertEqual(
            [
                item.median_objective
                for item in summaries
                if item.configuration_id == "a"
            ],
            [0.0, 100.0],
        )
        self.assertTrue(all(item.completed_run_count == 1 for item in coverage))

    def test_failed_variant_retains_its_own_missingness_and_rank_coverage(self):
        rows = [dict(row) for row in self.rows]
        for row in rows:
            if (
                row["instance_id"] == str(self.instances[1])
                and row["configuration_id"] == "c"
            ):
                row.update(run_status="failed", objective_best="")
        summary = next(
            item
            for item in summarize_objectives(rows)
            if item.instance_identity.instance_id == self.instances[1]
            and item.configuration_id == "c"
        )
        self.assertEqual(
            (summary.run_count, summary.completed_count, summary.mean), (1, 0, None)
        )
        rank = next(
            item
            for item in aggregate_objective_ranks(rows)
            if item.configuration_id == "c"
        )
        self.assertEqual((rank.instances_ranked, rank.total_instances), (1, 2))
        self.assertEqual(
            [item.instance_id for item in rank.ranked_instances], [self.instances[0]]
        )
        _, coverage = summarize_convergence(rows, self.points)
        failed = next(
            item
            for item in coverage
            if item.instance_identity.instance_id == self.instances[1]
            and item.configuration_id == "c"
        )
        self.assertEqual(
            (failed.completed_run_count, failed.noncompleted_runs_with_trace), (0, 1)
        )

    def test_trace_cannot_reference_the_other_variant(self):
        points = [dict(point) for point in self.points]
        points[0]["instance_id"] = str(self.instances[1])
        with self.assertRaisesRegex(AnalysisError, "identity"):
            summarize_convergence(self.rows, points)

    def test_missing_instance_id_is_not_reconstructed_from_a_label(self):
        rows = [dict(row) for row in self.rows]
        rows[0].pop("instance_id")
        with self.assertRaisesRegex(AnalysisError, "instance_id"):
            summarize_objectives(rows)

    def test_invalid_identity_metadata_is_not_coerced_or_defaulted(self):
        for field, value in (
            ("instance_id", True),
            ("instance_id", 1.5),
            ("instance_id", "0"),
            ("dimension", "2.5"),
            ("dimension", False),
            ("problem_parameters_json", ""),
            ("problem_parameters_json", "[]"),
            ("problem_parameters_json", '{"bad":NaN}'),
            ("data_sha256", 0),
            ("data_sha256", "invalid"),
            ("optimum", "inf"),
            ("optimum", True),
        ):
            with self.subTest(field=field, value=value):
                with self.assertRaises(AnalysisError):
                    summarize_objectives([dict(self.rows[0], **{field: value})])

    def test_conflicting_metadata_for_the_same_local_id_is_rejected(self):
        rows = [dict(row) for row in self.rows]
        rows[1]["problem_parameters_json"] = '{"variant":"contradiction"}'
        with self.assertRaisesRegex(AnalysisError, "inconsistent.*instance"):
            summarize_objectives(rows)

    def test_semantic_fingerprint_is_independent_of_local_ids_and_json_order(self):
        first = dict(self.rows[0], problem_parameters_json='{"b":[1,2],"a":true}')
        second = dict(
            first,
            instance_id="900",
            campaign_id="other",
            problem_parameters_json='{ "a": true, "b": [1, 2] }',
        )
        (left,) = summarize_objectives([first])
        (right,) = summarize_objectives([second])
        self.assertNotEqual(
            left.instance_identity.instance_id, right.instance_identity.instance_id
        )
        self.assertEqual(
            left.instance_identity.semantic_sha256,
            right.instance_identity.semantic_sha256,
        )
        (changed,) = summarize_objectives([dict(first, data_sha256="b" * 64)])
        self.assertNotEqual(
            left.instance_identity.semantic_sha256,
            changed.instance_identity.semantic_sha256,
        )

    def test_local_references_are_not_merged_just_because_semantics_match(self):
        first = dict(self.rows[0])
        second = dict(first, instance_id="900", run_id="900")
        summaries = summarize_objectives([first, second])
        self.assertEqual(len(summaries), 2)
        self.assertEqual(
            summaries[0].instance_identity.semantic_sha256,
            summaries[1].instance_identity.semantic_sha256,
        )

    def test_campaign_boundaries_and_order_are_preserved(self):
        rows = [dict(row) for row in self.rows]
        rows.extend(dict(row, campaign_id="other") for row in self.rows)
        summaries = summarize_objectives(rows)
        self.assertEqual(len(summaries), 12)
        self.assertEqual(summaries, summarize_objectives(reversed(rows)))
        self.assertEqual(
            aggregate_objective_ranks(rows), aggregate_objective_ranks(reversed(rows))
        )

    def test_incomplete_variant_is_reported_as_its_own_friedman_block(self):
        rows = [
            row
            for row in self.rows
            if not (
                row["instance_id"] == str(self.instances[1])
                and row["configuration_id"] == "c"
            )
        ]
        (result,) = friedman_objective_test(rows)
        self.assertEqual(result.block_count, 1)
        self.assertEqual(result.incomplete_block_count, 1)
        self.assertEqual(result.excluded_instances[0].instance_id, self.instances[1])
        self.assertIsNone(result.p_value)

    def test_testable_nemenyi_uses_exact_variant_blocks(self):
        rows = [
            dict(
                self.rows[0],
                instance_id=str(index + 1),
                problem_parameters_json=json.dumps({"variant": index}),
                configuration_id=f"config-{config}",
                configuration_key=f"key-{config}",
                objective_best=str((config + 1) * 10.0**index),
            )
            for index in range(11)
            for config in range(7)
        ]
        (result,) = friedman_objective_test(rows)
        self.assertEqual(result.block_count, 11)
        tests = friedman_posthoc_objective_tests(rows)
        self.assertEqual(len(tests), 21)
        self.assertTrue(
            all(
                test.status == "tested" and test.paired_instance_count == 11
                for test in tests
            )
        )
        pair = next(
            test
            for test in tests
            if (
                test.baseline_configuration_id == "config-0"
                and test.candidate_configuration_id == "config-6"
            )
        )
        self.assertEqual(pair.mean_rank_difference, -6.0)

    def test_r29_contradiction_cannot_reach_the_canonical_analysis_bundle(self):
        self.connection.execute(
            "UPDATE trace_metric_values SET value_real=999 "
            "WHERE metric_id='objective_best' AND run_id=1"
        )
        self.connection.commit()
        target = self.root / "contradictory"
        with self.assertRaises(AnalysisExportError):
            run_campaign_analysis(self.connection, "variants", target)
        self.assertFalse((target / "analysis.json").exists())

    def test_complete_pipeline_preserves_identity_in_json_tables_and_plot_panels(self):
        from matplotlib.figure import Figure

        original_savefig = Figure.savefig
        titles = []

        def capture(figure, path, *args, **kwargs):
            if Path(path).name == "convergence_curves.png":
                titles.append([axis.get_title() for axis in figure.axes])
            return original_savefig(figure, path, *args, **kwargs)

        with patch.object(Figure, "savefig", capture):
            result = run_campaign_analysis(
                self.connection, "variants", self.root / "analysis"
            )
        report = json.loads(Path(result.report_path).read_text(encoding="utf-8"))
        self.assertEqual(report["schema_version"], 4)
        self.assertEqual(len(report["objective_summaries"]), 6)
        self.assertEqual(len(report["convergence_coverage"]), 6)
        self.assertEqual(report["friedman_results"][0]["block_count"], 2)
        for name in (
            "objective_summaries",
            "convergence_summaries",
            "convergence_coverage",
        ):
            with (Path(result.tables_directory) / f"{name}.csv").open(
                encoding="utf-8", newline=""
            ) as file:
                table = list(csv.DictReader(file))
            self.assertEqual(len(table), 6)
            identities = [json.loads(row["instance_identity_json"]) for row in table]
            self.assertEqual(
                {item["instance_id"] for item in identities}, set(self.instances)
            )
        with (Path(result.tables_directory) / "aggregate_ranks.csv").open(
            encoding="utf-8", newline=""
        ) as file:
            ranks = list(csv.DictReader(file))
        self.assertTrue(
            all(
                {
                    item["instance_id"]
                    for item in json.loads(row["ranked_instances_json"])
                }
                == set(self.instances)
                for row in ranks
            )
        )
        with (Path(result.tables_directory) / "friedman_results.csv").open(
            encoding="utf-8", newline=""
        ) as file:
            (friedman,) = csv.DictReader(file)
        self.assertEqual(
            {
                item["instance_id"]
                for item in json.loads(friedman["included_instances_json"])
            },
            set(self.instances),
        )
        self.assertTrue(titles)
        self.assertTrue(all(len(panels) == 2 for panels in titles))
        self.assertTrue(all("instance_id=" in title for title in titles[0]))
        self.assertNotEqual(titles[0][0], titles[0][1])
        second = build_campaign_analysis_report(
            self.connection,
            "variants",
            Path(result.output_directory) / "runs.csv",
            Path(result.output_directory) / "traces.csv",
        )
        self.assertEqual(
            report["objective_summaries"][0]["instance_identity"],
            asdict(second.objective_summaries[0].instance_identity),
        )
