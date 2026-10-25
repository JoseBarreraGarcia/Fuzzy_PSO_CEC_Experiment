from __future__ import annotations

import unittest

import numpy as np

from afcs.fuzzy import MamdaniController, fuzzify, uniform_partition
from afcs.optimizers import SearchState
from afcs.optimizers.pso import FuzzyInertiaPolicy


class TestVersionedFuzzyPrimitives(unittest.TestCase):
    def test_triangular_ruspini_partition_sums_to_one(self) -> None:
        partition = uniform_partition(
            granularity=5, family="triangular_v1", overlap=1.0
        )
        for value in np.linspace(0.0, 1.0, 101):
            degrees, boundary = fuzzify(
                value,
                partition,
                zero_overlap_boundary_policy="nearest_center_tie_upper",
            )
            self.assertAlmostEqual(sum(degrees), 1.0)
            self.assertFalse(boundary)

    def test_zero_overlap_midpoint_uses_upper_label(self) -> None:
        partition = uniform_partition(
            granularity=3, family="triangular_v1", overlap=0.0
        )
        degrees, boundary = fuzzify(
            0.25,
            partition,
            zero_overlap_boundary_policy="nearest_center_tie_upper",
        )
        self.assertEqual(degrees, (0.0, 1.0, 0.0))
        self.assertTrue(boundary)

    def test_gaussian_two_sigma_overlap_convention(self) -> None:
        zero = uniform_partition(
            granularity=3, family="gaussian_v1", overlap=0.0
        )
        full = uniform_partition(
            granularity=3, family="gaussian_v1", overlap=1.0
        )
        delta = 0.5
        self.assertAlmostEqual(zero[0].width, delta / 4.0)
        self.assertAlmostEqual(full[0].width, delta / 2.0)
        self.assertAlmostEqual(zero[0].degree(2.0 * zero[0].width), np.exp(-2.0))

    def test_mamdani_controller_is_finite_at_zero_overlap_boundaries(self) -> None:
        controller = MamdaniController(
            granularity=3,
            rule_base="R5",
            membership_family="triangular_v1",
            diversity_overlap=0.0,
            progress_overlap=0.0,
            output_overlap=0.0,
        )
        result = controller.infer(0.25, 0.75)
        self.assertGreaterEqual(result.normalized_output, 0.0)
        self.assertLessEqual(result.normalized_output, 1.0)
        self.assertEqual(result.boundary_events, 2)
        self.assertEqual(len(result.active_rules), 1)

    def test_dense_and_sparse_inference_are_numerically_equivalent(self) -> None:
        for family in ("triangular_v1", "gaussian_v1"):
            for overlap in (0.0, 0.5, 1.0):
                common = {
                    "granularity": 5,
                    "rule_base": "R6",
                    "membership_family": family,
                    "diversity_overlap": overlap,
                    "progress_overlap": overlap,
                    "output_overlap": overlap,
                }
                dense = MamdaniController(**common, evaluation_mode="dense_v1")
                sparse = MamdaniController(**common, evaluation_mode="sparse_v1")
                for diversity in np.linspace(0.0, 1.0, 11):
                    for progress in np.linspace(0.0, 1.0, 11):
                        dense_result = dense.infer(diversity, progress)
                        sparse_result = sparse.infer(diversity, progress)
                        self.assertAlmostEqual(
                            dense_result.normalized_output,
                            sparse_result.normalized_output,
                            places=14,
                        )
                        self.assertEqual(
                            dense_result.active_rules, sparse_result.active_rules
                        )
                        self.assertEqual(dense_result.evaluated_rule_count, 25)
                        self.assertEqual(dense_result.skipped_rule_count, 0)
                        self.assertLessEqual(
                            sparse_result.evaluated_rule_count,
                            dense_result.evaluated_rule_count,
                        )
                        self.assertEqual(
                            sparse_result.evaluated_rule_count
                            + sparse_result.skipped_rule_count,
                            25,
                        )


class TestFuzzyInertiaPolicy(unittest.TestCase):
    def test_initial_swarm_drives_first_update_without_iteration_zero_inertia(self) -> None:
        policy = FuzzyInertiaPolicy(
            max_iterations=4,
            minimum=0.1,
            maximum=0.9,
            granularity=3,
            rule_base="R1",
            membership_family="triangular_v1",
            overlap_mode="shared",
            overlap=1.0,
        )
        positions = np.array([[-1.0, 0.0], [1.0, 2.0], [0.0, -2.0]])
        update = policy.propose(
            SearchState(
                iteration=1,
                evaluations=3,
                evaluation_budget=15,
                best_objective=0.0,
                observations={"positions": positions},
            ),
            {},
        )
        self.assertGreaterEqual(update.values["w"], 0.1)
        self.assertLessEqual(update.values["w"], 0.9)
        self.assertEqual(policy.last_diagnostics["diversity_ratio"], 1.0)
        self.assertEqual(policy.last_diagnostics["progress_ratio"], 0.25)

    def test_degenerate_population_has_defined_zero_ratio(self) -> None:
        policy = FuzzyInertiaPolicy(
            max_iterations=2,
            granularity=3,
            rule_base="R1",
            overlap_mode="shared",
            overlap=1.0,
        )
        positions = np.ones((4, 2))
        policy.propose(
            SearchState(
                iteration=1,
                evaluations=4,
                evaluation_budget=12,
                best_objective=1.0,
                observations={"positions": positions},
            ),
            {},
        )
        self.assertEqual(policy.last_diagnostics["diversity_ratio"], 0.0)

    def test_inference_time_and_run_summary_use_injected_monotonic_clock(self) -> None:
        readings = iter((10.0, 10.125))
        policy = FuzzyInertiaPolicy(
            max_iterations=1,
            granularity=3,
            rule_base="R1",
            overlap_mode="shared",
            overlap=1.0,
            clock=lambda: next(readings),
        )
        policy.propose(
            SearchState(
                iteration=1,
                evaluations=3,
                evaluation_budget=6,
                best_objective=0.0,
                observations={"positions": np.array([[-1.0], [0.0], [1.0]])},
            ),
            {},
        )
        self.assertEqual(policy.last_diagnostics["inference_time_seconds"], 0.125)
        self.assertEqual(policy.summary_metrics["fuzzy_runtime_total_seconds"], 0.125)
        self.assertEqual(policy.summary_metrics["fuzzy_inference_call_count"], 1)
        self.assertEqual(policy.summary_metrics["fuzzy_evaluated_rule_count"], 9)
        self.assertEqual(policy.summary_metrics["fuzzy_skipped_rule_count"], 0)


if __name__ == "__main__":
    unittest.main()
