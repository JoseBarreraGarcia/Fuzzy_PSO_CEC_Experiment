from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import unittest

from afcs.experiments import ConfigurationError, load_campaign_config, parse_campaign_config


EXAMPLE_PATH = Path("config/campaigns/cec2017_pso_v2.example.json")


def _example() -> dict:
    return json.loads(EXAMPLE_PATH.read_text(encoding="utf-8"))


class TestCampaignConfiguration(unittest.TestCase):
    def test_example_expands_complete_campaign_matrix(self) -> None:
        loaded = load_campaign_config(EXAMPLE_PATH, code_commit="abc123")
        self.assertEqual(loaded.summary.problem_instances, 2)
        self.assertEqual(loaded.summary.algorithm_configurations, 2)
        self.assertEqual(loaded.summary.replicas, 31)
        self.assertEqual(loaded.summary.total_runs, 124)
        self.assertEqual(loaded.summary.total_evaluations, 1_242_480)
        self.assertEqual(loaded.summary.first_seed, 42)
        self.assertEqual(loaded.summary.last_seed, 72)
        self.assertEqual(len(loaded.treatments), 4)
        self.assertEqual(loaded.campaign.code_commit, "abc123")

    def test_optional_values_are_materialized_in_resolved_config(self) -> None:
        raw = _example()
        raw["treatments"] = [deepcopy(raw["treatments"][1])]
        raw["treatments"][0]["parameters"] = {
            "population_size": 10,
            "max_iterations": 20,
        }
        raw["treatments"][0]["parameter_policy"]["parameters"] = {}
        raw["execution"] = {}

        resolved = parse_campaign_config(raw, code_commit="abc123").resolved_config
        parameters = resolved["treatments"][0]["parameters"]
        self.assertEqual(parameters["cognitive"], 2.0)
        self.assertEqual(parameters["social"], 2.0)
        self.assertEqual(parameters["velocity_factor"], 0.1)
        self.assertEqual(
            resolved["treatments"][0]["parameter_policy"]["parameters"],
            {"max_iterations": 20, "maximum": 0.9, "minimum": 0.1},
        )
        self.assertEqual(resolved["execution"], {"parallel_workers": 1})

    def test_invalid_configuration_is_rejected(self) -> None:
        cases = (
            (lambda raw: raw.update({"typo": True}), "unknown=['typo']"),
            (lambda raw: raw["problems"][0]["functions"].append(2), "F2 is excluded"),
            (lambda raw: raw["problems"][0].update({"dimensions": [20]}), "unsupported values [20]"),
            (lambda raw: raw["treatments"][0].update({"optimizer": "GA"}), "supported options are ['PSO']"),
            (lambda raw: raw["treatments"][0]["parameter_policy"].update({"id": "fuzzy"}), "supported options are ['fixed_inertia', 'legacy_ldiw']"),
            (lambda raw: raw["campaign"].update({"metrics": "unknown"}), "Unknown metric profile"),
        )
        for mutation, message in cases:
            with self.subTest(message=message):
                raw = _example()
                mutation(raw)
                with self.assertRaises(ConfigurationError) as context:
                    parse_campaign_config(raw, code_commit="abc123")
                self.assertIn(message, str(context.exception))

    def test_duplicate_treatment_identifier_is_rejected(self) -> None:
        raw = _example()
        raw["treatments"][1]["id"] = raw["treatments"][0]["id"]
        with self.assertRaisesRegex(ConfigurationError, "Duplicate treatment id"):
            parse_campaign_config(raw, code_commit="abc123")

    def test_schema_version_rejects_boolean(self) -> None:
        raw = _example()
        raw["schema_version"] = True
        with self.assertRaisesRegex(
            ConfigurationError, "schema_version must be exactly 1"
        ):
            parse_campaign_config(raw, code_commit="abc123")

    def test_parallel_execution_is_not_advertised_before_validation(self) -> None:
        raw = _example()
        raw["execution"]["parallel_workers"] = 2
        with self.assertRaisesRegex(ConfigurationError, "only sequential execution"):
            parse_campaign_config(raw, code_commit="abc123")


if __name__ == "__main__":
    unittest.main()
