import csv
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from afcs.analysis import (
    AnalysisExportError,
    build_campaign_analysis_report,
    export_campaign_csv,
    load_reconciled_run_rows,
    reconcile_campaign_analysis_figures,
    reconcile_campaign_analysis_report,
    reconcile_campaign_analysis_tables,
    reconcile_campaign_csv,
    run_campaign_analysis,
    write_campaign_analysis_figures,
    write_campaign_analysis_report,
    write_campaign_analysis_tables,
)
from afcs.metrics import load_metric_registry
from afcs.persistence import (
    configure_campaign_metrics,
    initialize_v2_database,
)


class TestCampaignCsvExport(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.connection = initialize_v2_database(self.root / "campaign.db")
        self._create_campaign()

    def tearDown(self):
        self.connection.close()
        self.temp_dir.cleanup()

    def _create_campaign(self):
        config_json = json.dumps({"fixture": True}, separators=(",", ":"))
        config_hash = hashlib.sha256(config_json.encode("utf-8")).hexdigest()
        self.connection.execute(
            """
            INSERT INTO campaigns (
                campaign_id, name, config_json, config_sha256, code_commit,
                metric_registry_version, schema_version, created_at,
                base_seed, seed_protocol, rng_engine
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "export-fixture",
                "Export fixture",
                config_json,
                config_hash,
                "abc123",
                3,
                5,
                "2026-11-08T00:00:00Z",
                100,
                "paired_by_replica_v1",
                "numpy_seedsequence_pcg64_v1",
            ),
        )
        registry = load_metric_registry()
        configure_campaign_metrics(
            self.connection, "export-fixture", registry, "convergence"
        )
        self.connection.execute(
            """
            INSERT INTO problem_instances (
                problem_family, name, dimension, optimum, direction, parameters_json
            ) VALUES ('BEN', 'F1', 2, 0.0, 'minimize', '{}')
            """
        )
        instance_id = self.connection.execute(
            "SELECT instance_id FROM problem_instances WHERE name = 'F1'"
        ).fetchone()[0]
        self.connection.execute(
            """
            INSERT INTO algorithm_configurations (
                configuration_id, campaign_id, algorithm, optimizer_version,
                parameters_json, parameters_sha256, budget_type,
                budget_evaluations, budget_iterations, population_size, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "ga-fixture",
                "export-fixture",
                "GA",
                "2.0.0a0-real-coded",
                '{"mutation_probability":"1/d"}',
                "1" * 64,
                "evaluations",
                6,
                2,
                2,
                "2026-11-08T00:00:00Z",
            ),
        )
        self.connection.executemany(
            """
            INSERT INTO runs (
                campaign_id, configuration_id, instance_id,
                replica_index, random_seed, status, started_at, finished_at,
                objective_best, solution_json, evaluations, runtime_total_seconds,
                feasible, constraint_violation, error_type, error_message
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    "export-fixture",
                    "ga-fixture",
                    instance_id,
                    0,
                    100,
                    "completed",
                    "2026-11-08T00:01:00Z",
                    "2026-11-08T00:01:01Z",
                    0.25,
                    "[0.5,0.5]",
                    6,
                    0.5,
                    1,
                    0.0,
                    None,
                    None,
                ),
                (
                    "export-fixture",
                    "ga-fixture",
                    instance_id,
                    1,
                    101,
                    "failed",
                    "2026-11-08T00:02:00Z",
                    "2026-11-08T00:02:01Z",
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    "RuntimeError",
                    "fixture failure",
                ),
            ],
        )
        self.connection.execute(
            """
            INSERT INTO run_metric_values (
                run_id, metric_id, metric_version, provenance, value_real
            )
            SELECT r.run_id, 'objective_best', 1, 'observed', 0.25
            FROM runs AS r WHERE r.campaign_id = 'export-fixture'
              AND r.replica_index = 0
            """
        )
        self.connection.execute(
            """
            INSERT INTO run_metric_values (
                run_id, metric_id, metric_version, provenance, value_real
            )
            SELECT r.run_id, 'runtime_total_seconds', 2, 'reconstructed', 0.5
            FROM runs AS r WHERE r.campaign_id = 'export-fixture'
              AND r.replica_index = 0
            """
        )
        self.connection.executemany(
            """
            INSERT INTO trace_points (
                run_id, checkpoint_index, iteration_index, evaluations, elapsed_seconds
            ) VALUES (?, ?, ?, ?, ?)
            """,
            [
                (1, 0, 0, 2, 0.1),
                (1, 1, 1, 6, 0.5),
            ],
        )
        self.connection.executemany(
            """
            INSERT INTO trace_metric_values (
                run_id, checkpoint_index, metric_id, metric_version,
                provenance, value_real
            ) VALUES (1, ?, 'objective_best', 1, ?, ?)
            """,
            [(0, "observed", 1.0), (1, "observed", 0.25)],
        )
        self.connection.commit()

    def test_exports_run_and_trace_tables_with_provenance(self):
        runs_path = self.root / "output" / "runs.csv"
        traces_path = self.root / "output" / "traces.csv"
        counts_before = self.connection.execute("SELECT COUNT(*) FROM runs").fetchone()[
            0
        ]

        summary = export_campaign_csv(
            self.connection, "export-fixture", runs_path, traces_path
        )

        with runs_path.open(newline="", encoding="utf-8") as file:
            run_rows = list(csv.DictReader(file))
        with traces_path.open(newline="", encoding="utf-8") as file:
            trace_rows = list(csv.DictReader(file))

        self.assertEqual((summary.run_rows, summary.trace_rows), (2, 2))
        self.assertEqual(len(run_rows), 2)
        self.assertEqual(
            [row["run_status"] for row in run_rows], ["completed", "failed"]
        )
        self.assertEqual(run_rows[0]["algorithm"], "GA")
        self.assertEqual(run_rows[0]["optimizer_version"], "2.0.0a0-real-coded")
        self.assertEqual(run_rows[0]["metric__objective_best"], "0.25")
        self.assertEqual(run_rows[0]["provenance__objective_best"], "observed")
        self.assertEqual(
            run_rows[0]["provenance__runtime_total_seconds"], "reconstructed"
        )
        self.assertEqual(run_rows[0]["feasible"], "true")
        self.assertEqual(run_rows[1]["metric__objective_best"], "")
        self.assertEqual(len(trace_rows), 2)
        self.assertEqual(trace_rows[-1]["evaluations"], "6")
        self.assertEqual(trace_rows[-1]["metric__objective_best"], "0.25")
        self.assertEqual(trace_rows[-1]["provenance__objective_best"], "observed")
        self.assertEqual(
            self.connection.execute("SELECT COUNT(*) FROM runs").fetchone()[0],
            counts_before,
        )

    def test_unknown_campaign_and_same_output_path_are_rejected(self):
        runs_path = self.root / "runs.csv"
        traces_path = self.root / "traces.csv"
        with self.assertRaisesRegex(AnalysisExportError, "Unknown campaign"):
            export_campaign_csv(self.connection, "missing", runs_path, traces_path)
        with self.assertRaisesRegex(AnalysisExportError, "different paths"):
            export_campaign_csv(self.connection, "export-fixture", runs_path, runs_path)
        self.assertFalse(runs_path.exists())

    def test_reconciled_exports_load_only_canonical_sqlite_run_rows(self):
        runs_path = self.root / "output" / "runs.csv"
        traces_path = self.root / "output" / "traces.csv"
        export_campaign_csv(self.connection, "export-fixture", runs_path, traces_path)

        reconciliation = reconcile_campaign_csv(
            self.connection, "export-fixture", runs_path, traces_path
        )
        run_rows = load_reconciled_run_rows(
            self.connection, "export-fixture", runs_path, traces_path
        )

        self.assertTrue(reconciliation.reconciled)
        self.assertEqual(reconciliation.runs.expected_row_count, 2)
        self.assertEqual(reconciliation.runs.actual_row_count, 2)
        self.assertEqual(reconciliation.traces.expected_row_count, 2)
        self.assertEqual(len(run_rows), 2)
        self.assertEqual(run_rows[0]["run_id"], "1")
        self.assertEqual(run_rows[0]["objective_best"], "0.25")

    def test_reconciliation_reports_changed_cells_and_missing_trace_rows(self):
        runs_path = self.root / "output" / "runs.csv"
        traces_path = self.root / "output" / "traces.csv"
        export_campaign_csv(self.connection, "export-fixture", runs_path, traces_path)

        with runs_path.open(newline="", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            rows = list(reader)
            columns = reader.fieldnames
        rows[0]["algorithm"] = "PSO"
        with runs_path.open("w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=columns)
            writer.writeheader()
            writer.writerows(rows)

        with traces_path.open(newline="", encoding="utf-8") as file:
            trace_rows = list(csv.reader(file))
        with traces_path.open("w", newline="", encoding="utf-8") as file:
            csv.writer(file).writerows(trace_rows[:2])

        reconciliation = reconcile_campaign_csv(
            self.connection, "export-fixture", runs_path, traces_path
        )

        self.assertFalse(reconciliation.reconciled)
        self.assertIn(
            "cell_value",
            {item.kind for item in reconciliation.runs.mismatches},
        )
        self.assertIn(
            "row_count",
            {item.kind for item in reconciliation.traces.mismatches},
        )
        self.assertIn(
            "row_missing",
            {item.kind for item in reconciliation.traces.mismatches},
        )
        with self.assertRaisesRegex(AnalysisExportError, "do not reconcile"):
            load_reconciled_run_rows(
                self.connection, "export-fixture", runs_path, traces_path
            )

    def test_reconciliation_detects_header_mismatch(self):
        runs_path = self.root / "output" / "runs.csv"
        traces_path = self.root / "output" / "traces.csv"
        export_campaign_csv(self.connection, "export-fixture", runs_path, traces_path)
        with runs_path.open(newline="", encoding="utf-8") as file:
            rows = list(csv.reader(file))
        column_index = rows[0].index("algorithm")
        rows[0][column_index] = "algorithm_name"
        with runs_path.open("w", newline="", encoding="utf-8") as file:
            csv.writer(file).writerows(rows)

        reconciliation = reconcile_campaign_csv(
            self.connection, "export-fixture", runs_path, traces_path
        )

        self.assertFalse(reconciliation.reconciled)
        self.assertEqual(reconciliation.runs.mismatches[0].kind, "header")
        self.assertTrue(reconciliation.traces.matches)

    def test_reconciliation_detects_missing_and_stale_exports(self):
        runs_path = self.root / "output" / "runs.csv"
        traces_path = self.root / "output" / "traces.csv"
        export_campaign_csv(self.connection, "export-fixture", runs_path, traces_path)
        traces_path.unlink()

        missing = reconcile_campaign_csv(
            self.connection, "export-fixture", runs_path, traces_path
        )
        self.assertFalse(missing.reconciled)
        self.assertEqual(missing.traces.mismatches[0].kind, "file_missing")

        export_campaign_csv(self.connection, "export-fixture", runs_path, traces_path)
        self.connection.execute(
            "UPDATE runs SET objective_best = 0.125 WHERE replica_index = 0"
        )
        self.connection.execute(
            """
            UPDATE run_metric_values SET value_real = 0.125
            WHERE metric_id = 'objective_best'
              AND run_id = (
                  SELECT run_id FROM runs
                  WHERE campaign_id = 'export-fixture'
                    AND replica_index = 0
              )
            """
        )
        self.connection.execute(
            "UPDATE trace_metric_values SET value_real=0.125 "
            "WHERE metric_id='objective_best' AND checkpoint_index=1"
        )
        self.connection.commit()

        stale = reconcile_campaign_csv(
            self.connection, "export-fixture", runs_path, traces_path
        )
        self.assertFalse(stale.reconciled)
        self.assertIn(
            "cell_value",
            {item.kind for item in stale.runs.mismatches},
        )
        with self.assertRaisesRegex(AnalysisExportError, "do not reconcile"):
            load_reconciled_run_rows(
                self.connection, "export-fixture", runs_path, traces_path
            )

    def test_analysis_report_uses_reconciled_source_and_reconciles_deterministically(
        self,
    ):
        runs_path = self.root / "output" / "runs.csv"
        traces_path = self.root / "output" / "traces.csv"
        report_path = self.root / "output" / "analysis.json"
        export_campaign_csv(self.connection, "export-fixture", runs_path, traces_path)

        report = build_campaign_analysis_report(
            self.connection, "export-fixture", runs_path, traces_path
        )
        write_campaign_analysis_report(report, report_path)
        first_content = report_path.read_text(encoding="utf-8")
        reconciliation = reconcile_campaign_analysis_report(
            self.connection,
            "export-fixture",
            runs_path,
            traces_path,
            report_path,
        )

        self.assertEqual(report.run_row_count, 2)
        self.assertEqual(report.trace_row_count, 2)
        self.assertEqual(report.schema_version, 4)
        self.assertEqual(report.run_status_counts, (("completed", 1), ("failed", 1)))
        self.assertEqual(len(report.objective_summaries), 1)
        self.assertEqual(
            [item.evaluations for item in report.convergence_summaries],
            [2, 6],
        )
        self.assertEqual(report.convergence_coverage[0].completed_runs_with_trace, 1)
        self.assertEqual(report.convergence_coverage[0].completed_runs_without_trace, 0)
        self.assertEqual(len(report.aggregate_ranks), 1)
        self.assertEqual(report.friedman_results, ())
        self.assertEqual(
            report.skipped_friedman_families[0].status,
            "fewer_than_three_configurations",
        )
        self.assertTrue(reconciliation.matches)
        write_campaign_analysis_report(report, report_path)
        self.assertEqual(report_path.read_text(encoding="utf-8"), first_content)

    def test_analysis_report_requires_reconciled_exports_and_detects_stale_report(self):
        runs_path = self.root / "output" / "runs.csv"
        traces_path = self.root / "output" / "traces.csv"
        report_path = self.root / "output" / "analysis.json"
        export_campaign_csv(self.connection, "export-fixture", runs_path, traces_path)
        report = build_campaign_analysis_report(
            self.connection, "export-fixture", runs_path, traces_path
        )
        write_campaign_analysis_report(report, report_path)

        with runs_path.open(newline="", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            rows = list(reader)
            columns = reader.fieldnames
        rows[0]["algorithm"] = "PSO"
        with runs_path.open("w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=columns)
            writer.writeheader()
            writer.writerows(rows)
        with self.assertRaisesRegex(AnalysisExportError, "do not reconcile"):
            build_campaign_analysis_report(
                self.connection, "export-fixture", runs_path, traces_path
            )

        export_campaign_csv(self.connection, "export-fixture", runs_path, traces_path)
        self.connection.execute(
            "UPDATE runs SET objective_best = 0.125 WHERE replica_index = 0"
        )
        self.connection.execute(
            """
            UPDATE run_metric_values SET value_real = 0.125
            WHERE metric_id = 'objective_best'
              AND run_id = (
                  SELECT run_id FROM runs
                  WHERE campaign_id = 'export-fixture'
                    AND replica_index = 0
              )
            """
        )
        self.connection.execute(
            "UPDATE trace_metric_values SET value_real=0.125 "
            "WHERE metric_id='objective_best' AND checkpoint_index=1"
        )
        self.connection.commit()
        export_campaign_csv(self.connection, "export-fixture", runs_path, traces_path)
        stale = reconcile_campaign_analysis_report(
            self.connection,
            "export-fixture",
            runs_path,
            traces_path,
            report_path,
        )
        self.assertFalse(stale.matches)
        self.assertEqual(stale.mismatch_kind, "content_mismatch")
        self.assertNotEqual(stale.expected_sha256, stale.actual_sha256)

    def test_analysis_report_rejects_missing_completed_objective_provenance(self):
        self.connection.execute(
            """
            DELETE FROM run_metric_values
            WHERE metric_id = 'objective_best'
              AND run_id = (
                  SELECT run_id FROM runs
                  WHERE campaign_id = 'export-fixture'
                    AND status = 'completed'
              )
            """
        )
        self.connection.commit()
        runs_path = self.root / "output" / "runs.csv"
        traces_path = self.root / "output" / "traces.csv"
        with self.assertRaisesRegex(AnalysisExportError, "missing_required_metric"):
            export_campaign_csv(
                self.connection, "export-fixture", runs_path, traces_path
            )
        self.assertFalse(runs_path.exists())
        with self.assertRaisesRegex(AnalysisExportError, "missing_required_metric"):
            build_campaign_analysis_report(
                self.connection, "export-fixture", runs_path, traces_path
            )

    def test_analysis_report_preserves_friedman_insufficiency_without_fake_p_values(
        self,
    ):
        instance_id = self.connection.execute(
            "SELECT instance_id FROM problem_instances WHERE name = 'F1'"
        ).fetchone()[0]
        for index, configuration_id in enumerate(("config-b", "config-c"), start=2):
            self.connection.execute(
                """
                INSERT INTO algorithm_configurations (
                    configuration_id, campaign_id, algorithm, optimizer_version,
                    parameters_json, parameters_sha256, budget_type,
                    budget_evaluations, budget_iterations, population_size, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    configuration_id,
                    "export-fixture",
                    f"GA-{index}",
                    "2.0.0a0-real-coded",
                    "{}",
                    str(index) * 64,
                    "evaluations",
                    6,
                    2,
                    2,
                    "2026-11-08T00:00:00Z",
                ),
            )
            self.connection.execute(
                """
                INSERT INTO runs (
                    campaign_id, configuration_id, instance_id,
                    replica_index, random_seed, status, started_at, finished_at,
                    objective_best, solution_json, evaluations, runtime_total_seconds,
                    feasible, constraint_violation, error_type, error_message
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    "export-fixture",
                    configuration_id,
                    instance_id,
                    0,
                    100,
                    "completed",
                    "2026-11-08T00:03:00Z",
                    "2026-11-08T00:03:01Z",
                    0.1 * index,
                    "[0.5,0.5]",
                    6,
                    0.5,
                    1,
                    0.0,
                    None,
                    None,
                ),
            )
            self.connection.execute(
                """
                INSERT INTO run_metric_values (
                    run_id, metric_id, metric_version, provenance, value_real
                )
                SELECT run_id, 'objective_best', 1, 'observed', objective_best
                FROM runs
                WHERE campaign_id = 'export-fixture'
                  AND configuration_id = ?
                """,
                (configuration_id,),
            )
        self.connection.commit()

        runs_path = self.root / "output" / "runs.csv"
        traces_path = self.root / "output" / "traces.csv"
        export_campaign_csv(self.connection, "export-fixture", runs_path, traces_path)
        report = build_campaign_analysis_report(
            self.connection, "export-fixture", runs_path, traces_path
        )

        self.assertEqual(len(report.friedman_results), 1)
        self.assertEqual(report.friedman_results[0].block_count, 1)
        self.assertIsNone(report.friedman_results[0].p_value)
        self.assertEqual(len(report.friedman_posthoc_results), 3)
        self.assertEqual(
            {result.status for result in report.friedman_posthoc_results},
            {"insufficient_omnibus_blocks"},
        )
        self.assertTrue(
            all(result.p_value is None for result in report.friedman_posthoc_results)
        )
        figures_dir = self.root / "output" / "friedman_figures"
        write_campaign_analysis_figures(report, figures_dir)
        self.assertTrue(
            reconcile_campaign_analysis_figures(report, figures_dir).matches
        )

    def test_analysis_tables_are_deterministic_and_reconciled_to_report(self):
        runs_path = self.root / "output" / "runs.csv"
        traces_path = self.root / "output" / "traces.csv"
        report_path = self.root / "output" / "analysis.json"
        tables_dir = self.root / "output" / "tables"
        export_campaign_csv(self.connection, "export-fixture", runs_path, traces_path)
        report = build_campaign_analysis_report(
            self.connection, "export-fixture", runs_path, traces_path
        )
        write_campaign_analysis_report(report, report_path)

        export_summary = write_campaign_analysis_tables(report, tables_dir)
        first_tables = {
            filename: (tables_dir / filename).read_bytes()
            for filename in export_summary.files
        }
        reconciliation = reconcile_campaign_analysis_tables(report, tables_dir)

        self.assertTrue(reconciliation.matches)
        self.assertEqual(len(reconciliation.tables), 8)
        table_manifest = json.loads(
            (tables_dir / "manifest.json").read_text(encoding="utf-8")
        )
        self.assertEqual(table_manifest["schema_version"], 4)
        with (tables_dir / "convergence_summaries.csv").open(
            newline="", encoding="utf-8"
        ) as file:
            convergence = list(csv.DictReader(file))
        self.assertEqual(len(convergence), 2)
        self.assertEqual(
            json.loads(convergence[0]["provenance_counts_json"]),
            [["observed", 1]],
        )
        self.assertEqual(dict(export_summary.row_counts)["objective_summaries.csv"], 1)
        self.assertEqual(dict(export_summary.row_counts)["run_status_counts.csv"], 2)
        with (tables_dir / "objective_summaries.csv").open(
            newline="", encoding="utf-8"
        ) as file:
            summaries = list(csv.DictReader(file))
        self.assertEqual(summaries[0]["campaign_id"], "export-fixture")
        self.assertEqual(summaries[0]["median"], "0.25")
        self.assertEqual(
            json.loads(summaries[0]["objective_provenance_counts_json"]),
            [["observed", 1]],
        )
        self.assertEqual(
            json.loads(summaries[0]["status_counts_json"]),
            [["completed", 1], ["failed", 1]],
        )

        write_campaign_analysis_tables(report, tables_dir)
        self.assertEqual(
            first_tables,
            {
                filename: (tables_dir / filename).read_bytes()
                for filename in export_summary.files
            },
        )

    def test_analysis_table_reconciliation_detects_table_and_manifest_changes(self):
        runs_path = self.root / "output" / "runs.csv"
        traces_path = self.root / "output" / "traces.csv"
        tables_dir = self.root / "output" / "tables"
        export_campaign_csv(self.connection, "export-fixture", runs_path, traces_path)
        report = build_campaign_analysis_report(
            self.connection, "export-fixture", runs_path, traces_path
        )
        write_campaign_analysis_tables(report, tables_dir)
        (tables_dir / "objective_summaries.csv").write_text(
            "tampered\nvalue\n", encoding="utf-8"
        )
        (tables_dir / "aggregate_ranks.csv").unlink()

        changed = reconcile_campaign_analysis_tables(report, tables_dir)
        self.assertFalse(changed.matches)
        changed_by_name = {item.dataset: item for item in changed.tables}
        self.assertFalse(changed_by_name["objective_summaries"].matches)
        self.assertFalse(changed_by_name["aggregate_ranks"].matches)
        self.assertEqual(
            changed_by_name["aggregate_ranks"].mismatches[0].kind, "file_missing"
        )

        write_campaign_analysis_tables(report, tables_dir)
        manifest_path = tables_dir / "manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["campaign_id"] = "stale-campaign"
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        stale_manifest = reconcile_campaign_analysis_tables(report, tables_dir)
        self.assertFalse(stale_manifest.matches)
        self.assertFalse(stale_manifest.manifest_matches)
        self.assertEqual(stale_manifest.manifest_mismatch_kind, "content_mismatch")

    def test_analysis_figures_are_deterministic_and_reconciled(self):
        runs_path = self.root / "output" / "runs.csv"
        traces_path = self.root / "output" / "traces.csv"
        figures_dir = self.root / "output" / "figures"
        export_campaign_csv(self.connection, "export-fixture", runs_path, traces_path)
        report = build_campaign_analysis_report(
            self.connection, "export-fixture", runs_path, traces_path
        )

        export_summary = write_campaign_analysis_figures(report, figures_dir)
        first_figures = {
            filename: (figures_dir / filename).read_bytes()
            for filename in export_summary.files
        }
        reconciliation = reconcile_campaign_analysis_figures(report, figures_dir)

        self.assertTrue(reconciliation.matches)
        self.assertEqual(len(reconciliation.figures), 3)
        figure_manifest = json.loads(
            (figures_dir / "manifest.json").read_text(encoding="utf-8")
        )
        self.assertEqual(figure_manifest["schema_version"], 4)
        self.assertTrue(
            all(
                image.startswith(b"\x89PNG\r\n\x1a\n")
                for image in first_figures.values()
            )
        )
        write_campaign_analysis_figures(report, figures_dir)
        self.assertEqual(
            first_figures,
            {
                filename: (figures_dir / filename).read_bytes()
                for filename in export_summary.files
            },
        )
        self.assertTrue(
            reconcile_campaign_analysis_figures(report, figures_dir).matches
        )

    def test_analysis_pipeline_exports_report_tables_figures_and_reconciles(self):
        output_dir = self.root / "pipeline"
        result = run_campaign_analysis(self.connection, "export-fixture", output_dir)

        self.assertEqual(result.campaign_id, "export-fixture")
        self.assertEqual(result.run_row_count, 2)
        self.assertEqual(result.trace_row_count, 2)
        self.assertTrue(Path(result.report_path).is_file())
        self.assertTrue((Path(result.tables_directory) / "manifest.json").is_file())
        self.assertTrue((Path(result.figures_directory) / "manifest.json").is_file())
        self.assertTrue(
            reconcile_campaign_csv(
                self.connection,
                "export-fixture",
                output_dir / "runs.csv",
                output_dir / "traces.csv",
            ).reconciled
        )

    def test_analysis_figure_reconciliation_detects_tampered_and_missing_files(self):
        runs_path = self.root / "output" / "runs.csv"
        traces_path = self.root / "output" / "traces.csv"
        figures_dir = self.root / "output" / "figures"
        export_campaign_csv(self.connection, "export-fixture", runs_path, traces_path)
        report = build_campaign_analysis_report(
            self.connection, "export-fixture", runs_path, traces_path
        )
        write_campaign_analysis_figures(report, figures_dir)
        (figures_dir / "aggregate_mean_ranks.png").write_bytes(b"tampered")

        changed = reconcile_campaign_analysis_figures(report, figures_dir)
        changed_by_name = {figure.filename: figure for figure in changed.figures}
        self.assertFalse(changed.matches)
        self.assertEqual(
            changed_by_name["aggregate_mean_ranks.png"].mismatch_kind,
            "content_mismatch",
        )

        (figures_dir / "friedman_mean_ranks.png").unlink()
        missing = reconcile_campaign_analysis_figures(report, figures_dir)
        missing_by_name = {figure.filename: figure for figure in missing.figures}
        self.assertEqual(
            missing_by_name["friedman_mean_ranks.png"].mismatch_kind,
            "file_missing",
        )

    def test_analysis_report_reconciliation_reports_missing_and_invalid_json(self):
        runs_path = self.root / "output" / "runs.csv"
        traces_path = self.root / "output" / "traces.csv"
        report_path = self.root / "output" / "analysis.json"
        export_campaign_csv(self.connection, "export-fixture", runs_path, traces_path)

        missing = reconcile_campaign_analysis_report(
            self.connection,
            "export-fixture",
            runs_path,
            traces_path,
            report_path,
        )
        self.assertEqual(missing.mismatch_kind, "file_missing")

        report_path.write_text("{invalid", encoding="utf-8")
        invalid = reconcile_campaign_analysis_report(
            self.connection,
            "export-fixture",
            runs_path,
            traces_path,
            report_path,
        )
        self.assertEqual(invalid.mismatch_kind, "invalid_json")


if __name__ == "__main__":
    unittest.main()
