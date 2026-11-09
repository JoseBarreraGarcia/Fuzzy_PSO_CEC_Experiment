from __future__ import annotations

import json
import unittest
from copy import deepcopy
from pathlib import Path

from afcs.experiments import (
    ConfigurationError,
    load_campaign_config,
    parse_campaign_config,
)

EXAMPLE_PATH = Path("config/campaigns/cec2017_pso_v2.example.json")
GA_EXAMPLE_PATH = Path("config/campaigns/real_coded_ga_v2.example.json")


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
            (
                lambda raw: raw["problems"][0].update({"dimensions": [20]}),
                "unsupported values [20]",
            ),
            (
                lambda raw: raw["treatments"][0].update({"optimizer": "DE"}),
                "supported options are ['GA', 'PSO']",
            ),
            (
                lambda raw: raw["treatments"][0]["parameter_policy"].update(
                    {"id": "fuzzy"}
                ),
                "supported options are ['fixed_inertia', 'legacy_ldiw', 'linear_endpoints_v1', 'fuzzy_inertia_mamdani']",
            ),
            (
                lambda raw: raw["campaign"].update({"metrics": "unknown"}),
                "Unknown metric profile",
            ),
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

    def test_parallel_worker_count_is_accepted_and_resolved(self) -> None:
        raw = _example()
        raw["execution"]["parallel_workers"] = 2
        loaded = parse_campaign_config(raw, code_commit="abc123")
        self.assertEqual(loaded.execution.parallel_workers, 2)
        self.assertEqual(loaded.resolved_config["execution"]["parallel_workers"], 2)

    def test_real_coded_ga_is_resolved_without_binary_representation(self) -> None:
        raw = _example()
        raw["problems"] = [{"family": "CLASSICAL", "functions": [1], "dimensions": [2]}]
        raw["treatments"] = [
            {
                "id": "ga-real-defaults",
                "optimizer": "GA",
                "parameters": {"population_size": 8, "max_iterations": 5},
            }
        ]

        loaded = parse_campaign_config(raw, code_commit="abc123")
        resolved = loaded.resolved_config["treatments"][0]

        self.assertEqual(loaded.treatments[0].run_metadata.optimizer.optimizer_id, "GA")
        self.assertEqual(
            loaded.treatments[0].run_metadata.optimizer.version,
            "2.0.0a0-real-coded",
        )
        self.assertEqual(resolved["parameters"]["crossover_probability"], 0.9)
        self.assertEqual(resolved["parameters"]["mutation_probability"], "1/d")
        self.assertEqual(resolved["parameter_policy"]["id"], "no_adaptation")

    def test_real_coded_ga_example_is_loadable_and_budgeted(self) -> None:
        loaded = load_campaign_config(GA_EXAMPLE_PATH, code_commit="abc123")

        self.assertEqual(loaded.summary.total_runs, 5)
        self.assertEqual(loaded.summary.total_evaluations, 20 * 201 * 5)
        self.assertEqual(loaded.treatments[0].run_metadata.optimizer.optimizer_id, "GA")

    def test_classical_family_validates_fixed_dimensions(self) -> None:
        raw = _example()
        raw["problems"] = [
            {"family": "CLASSICAL", "functions": [1, 14], "dimensions": [2]}
        ]
        loaded = parse_campaign_config(raw, code_commit="abc123")
        self.assertEqual(loaded.summary.problem_instances, 2)
        self.assertEqual(loaded.resolved_config["problems"][0]["family"], "CLASSICAL")

        raw["problems"] = [
            {"family": "CLASSICAL", "functions": [14], "dimensions": [3]}
        ]
        with self.assertRaisesRegex(ConfigurationError, "requires dimension 2"):
            parse_campaign_config(raw, code_commit="abc123")

    def test_opfunu_family_resolves_suite_year_and_function(self) -> None:
        raw = _example()
        raw["problems"] = [
            {
                "family": "OPFUNU_CEC",
                "suite_year": 2014,
                "functions": [1],
                "dimensions": [10],
            }
        ]
        loaded = parse_campaign_config(raw, code_commit="abc123")
        problem = loaded.resolved_config["problems"][0]
        self.assertEqual(problem["family"], "OPFUNU_CEC")
        self.assertEqual(problem["suite_year"], 2014)
        self.assertEqual(problem["functions"], (1,))

        del raw["problems"][0]["suite_year"]
        with self.assertRaisesRegex(ConfigurationError, "suite_year"):
            parse_campaign_config(raw, code_commit="abc123")

    def test_fuzzy_policy_is_resolved_with_explicit_methodology(self) -> None:
        raw = _example()
        raw["treatments"] = [deepcopy(raw["treatments"][0])]
        raw["treatments"][0]["id"] = "fcs-o0-n3-r1"
        raw["treatments"][0]["parameter_policy"] = {
            "id": "fuzzy_inertia_mamdani",
            "parameters": {
                "minimum": 0.1,
                "maximum": 0.9,
                "granularity": 3,
                "rule_base": "R1",
                "membership_family": "triangular_v1",
                "overlap": {"mode": "shared", "value": 0.0},
                "zero_overlap_boundary_policy": "nearest_center_tie_upper",
            },
        }
        resolved = parse_campaign_config(raw, code_commit="abc123").resolved_config
        parameters = resolved["treatments"][0]["parameter_policy"]["parameters"]
        self.assertEqual(parameters["diversity_metric"], "hussain_diversity_v1")
        self.assertEqual(parameters["progress"], "iteration_over_max_iterations_v1")
        self.assertEqual(parameters["overlap"], {"mode": "shared", "value": 0.0})

    def test_independent_overlap_requires_all_variables(self) -> None:
        raw = _example()
        raw["treatments"] = [deepcopy(raw["treatments"][0])]
        raw["treatments"][0]["parameter_policy"] = {
            "id": "fuzzy_inertia_mamdani",
            "parameters": {
                "minimum": 0.1,
                "maximum": 0.9,
                "granularity": 3,
                "rule_base": "R1",
                "membership_family": "triangular_v1",
                "overlap": {"mode": "independent", "diversity": 0.0},
                "zero_overlap_boundary_policy": "nearest_center_tie_upper",
            },
        }
        with self.assertRaisesRegex(ConfigurationError, "missing=.*output"):
            parse_campaign_config(raw, code_commit="abc123")


if __name__ == "__main__":
    unittest.main()
