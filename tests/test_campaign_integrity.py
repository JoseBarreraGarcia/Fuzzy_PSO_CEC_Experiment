from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from afcs.experiments import SequentialCampaignOrchestrator, parse_campaign_config
from afcs.metrics import load_metric_registry
from afcs.persistence import (
    ExperimentRepository,
    audit_campaign_integrity,
    initialize_v2_database,
)

EXAMPLE_PATH = Path("config/campaigns/cec2017_pso_v2.example.json")


class TestCampaignIntegrityAudit(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.connection = initialize_v2_database(
            Path(self.temp_dir.name) / "integrity.db"
        )
        repository = ExperimentRepository(self.connection, load_metric_registry())
        raw = json.loads(EXAMPLE_PATH.read_text(encoding="utf-8"))
        raw["campaign"].update(
            {"id": "integrity", "replicas": 1, "metrics": "optimizer"}
        )
        raw["problems"] = [{"family": "CEC2017", "functions": [1], "dimensions": [10]}]
        raw["treatments"] = [raw["treatments"][0]]
        raw["treatments"][0]["parameters"].update(
            {"population_size": 4, "max_iterations": 2}
        )
        loaded = parse_campaign_config(raw, code_commit="test-commit")
        SequentialCampaignOrchestrator(repository).plan_and_execute(loaded)

    def tearDown(self) -> None:
        self.connection.close()
        self.temp_dir.cleanup()

    def test_completed_campaign_passes_integrity_audit(self) -> None:
        report = audit_campaign_integrity(self.connection, "integrity")

        self.assertTrue(report.is_valid)
        self.assertEqual(report.run_count, 1)
        self.assertEqual(report.attempt_count, 1)
        self.assertEqual(report.trace_point_count, 3)
        self.assertEqual(report.warnings, ())

    def test_budget_tampering_is_reported_without_modification(self) -> None:
        run_id = self.connection.execute(
            "SELECT run_id FROM runs WHERE campaign_id = 'integrity'"
        ).fetchone()[0]
        self.connection.execute(
            "UPDATE runs SET evaluations = evaluations - 1 WHERE run_id = ?",
            (run_id,),
        )
        self.connection.commit()

        report = audit_campaign_integrity(self.connection, "integrity")

        self.assertFalse(report.is_valid)
        codes = {issue.code for issue in report.issues}
        self.assertIn("evaluation_budget_mismatch", codes)
        self.assertIn("final_trace_nfe_mismatch", codes)
        stored = self.connection.execute(
            "SELECT evaluations FROM runs WHERE run_id = ?", (run_id,)
        ).fetchone()[0]
        self.assertEqual(stored, 11)

    def test_attempt_status_tampering_is_reported(self) -> None:
        self.connection.execute(
            "UPDATE run_attempts SET status = 'failed' WHERE run_id = 1"
        )
        self.connection.commit()

        report = audit_campaign_integrity(self.connection, "integrity")

        self.assertIn(
            "terminal_attempt_mismatch", {issue.code for issue in report.issues}
        )

    def test_cancelled_run_is_warning_but_missing_waiver_is_integrity_error(
        self,
    ) -> None:
        self.connection.execute(
            """
            UPDATE runs SET status = 'cancelled', cancellation_reason = 'scope change'
            WHERE campaign_id = 'integrity'
            """
        )
        self.connection.execute(
            "UPDATE run_attempts SET status = 'cancelled' WHERE run_id = 1"
        )
        self.connection.execute(
            """
            UPDATE campaigns SET status = 'sealed', sealed_at = '2026-10-26T00:00:00Z'
            WHERE campaign_id = 'integrity'
            """
        )
        self.connection.commit()

        report = audit_campaign_integrity(self.connection, "integrity")

        self.assertIn("cancelled_run", {warning.code for warning in report.warnings})
        self.assertIn(
            "sealed_incomplete_without_waiver",
            {issue.code for issue in report.issues},
        )


if __name__ == "__main__":
    unittest.main()
