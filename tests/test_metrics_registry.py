import copy
import csv
from pathlib import Path
import sys
import unittest

SRC = Path(__file__).resolve().parents[1] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from afcs.metrics import (
    MetricRegistryError,
    load_metric_registry,
    parse_metric_registry,
)


FIXTURES = Path(__file__).with_name("fixtures")


class TestMetricRegistry(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = load_metric_registry()

    def test_default_registry_is_valid(self):
        self.assertEqual(self.registry.schema_version, 1)
        self.assertGreaterEqual(len(self.registry.metrics), 20)
        self.assertEqual(len(self.registry.metrics), len(set(self.registry.metrics)))

    def test_required_metrics_are_present_in_every_profile(self):
        required = set(self.registry.required_metrics)
        for profile in self.registry.profiles:
            with self.subTest(profile=profile):
                self.assertTrue(required <= set(self.registry.resolve(profile)))

    def test_all_selects_every_registered_metric_in_registry_order(self):
        self.assertEqual(self.registry.resolve("all"), tuple(self.registry.metrics))

    def test_explicit_list_keeps_required_metrics(self):
        resolved = set(self.registry.resolve(["inertia_weight"]))
        self.assertIn("inertia_weight", resolved)
        self.assertTrue(set(self.registry.required_metrics) <= resolved)

    def test_selection_object_supports_include_and_exclude(self):
        resolved = set(
            self.registry.resolve(
                {
                    "profile": "optimizer",
                    "include": ["inertia_weight"],
                    "exclude": ["population_entropy"],
                }
            )
        )
        self.assertIn("inertia_weight", resolved)
        self.assertNotIn("population_entropy", resolved)

    def test_required_metric_cannot_be_excluded(self):
        with self.assertRaises(MetricRegistryError):
            self.registry.resolve({"exclude": ["objective_best"]})

    def test_unknown_metric_and_profile_are_rejected(self):
        with self.assertRaises(MetricRegistryError):
            self.registry.resolve(["does_not_exist"])
        with self.assertRaises(MetricRegistryError):
            self.registry.resolve("does_not_exist")

    def test_invalid_definition_is_rejected(self):
        raw = {
            "schema_version": 1,
            "required_metrics": ["broken"],
            "profiles": {"minimal": []},
            "metrics": {"broken": {"version": 1}},
        }
        with self.assertRaises(MetricRegistryError):
            parse_metric_registry(copy.deepcopy(raw))

    def test_run_fixture_contains_required_storage_columns(self):
        with (FIXTURES / "analysis_runs.csv").open(newline="", encoding="utf-8") as file:
            rows = list(csv.DictReader(file))
        self.assertEqual(len(rows), 8)
        self.assertTrue(set(self.registry.required_metrics) <= set(rows[0]))
        pairs = {(row["instance"], row["replica_index"]) for row in rows}
        self.assertEqual(len(pairs), 4)

    def test_trace_fixture_has_monotonic_budget_and_current_diversity_max(self):
        with (FIXTURES / "analysis_traces.csv").open(newline="", encoding="utf-8") as file:
            rows = list(csv.DictReader(file))
        evaluations = [int(row["evaluations"]) for row in rows]
        diversity_max = [float(row["diversity_dimension_max"]) for row in rows]
        self.assertEqual(evaluations, sorted(evaluations))
        self.assertGreater(len(set(diversity_max)), 1)


if __name__ == "__main__":
    unittest.main()
