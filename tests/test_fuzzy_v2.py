from __future__ import annotations

import unittest

import numpy as np

from afcs.fuzzy import MamdaniController, fuzzify, rule_matrix, uniform_partition
from afcs.optimizers import SearchState
from afcs.optimizers.pso import FuzzyInertiaPolicy


class TestVersionedFuzzyPrimitives(unittest.TestCase):
    def test_triangular_partition_geometry_for_all_study_granularities(self) -> None:
        for granularity in (3, 5, 7, 9):
            for overlap in (0.0, 0.5, 1.0):
                with self.subTest(granularity=granularity, overlap=overlap):
                    partition = uniform_partition(
                        granularity=granularity,
                        family="triangular_v1",
                        overlap=overlap,
                    )
                    delta = 1.0 / (granularity - 1)
                    self.assertEqual(len(partition), granularity)
                    for index, membership in enumerate(partition):
                        self.assertAlmostEqual(membership.center, index * delta)
                        self.assertAlmostEqual(
                            membership.width, delta * (1.0 + overlap) / 2.0
                        )
                        self.assertEqual(membership.left_shoulder, index == 0)
                        self.assertEqual(
                            membership.right_shoulder, index == granularity - 1
                        )
                    self.assertEqual(partition[0].degree(0.0), 1.0)
                    self.assertEqual(partition[-1].degree(1.0), 1.0)

    def test_triangular_coverage_distinguishes_zero_overlap_boundary_policy(
        self,
    ) -> None:
        for granularity in (3, 5, 7, 9):
            for overlap in (0.0, 0.5, 1.0):
                partition = uniform_partition(
                    granularity=granularity,
                    family="triangular_v1",
                    overlap=overlap,
                )
                values = list(np.linspace(0.0, 1.0, 101))
                values.extend(
                    (left.center + right.center) / 2.0
                    for left, right in zip(partition, partition[1:])
                )
                for value in values:
                    with self.subTest(
                        granularity=granularity, overlap=overlap, value=value
                    ):
                        raw = tuple(item.degree(value) for item in partition)
                        degrees, boundary = fuzzify(
                            value,
                            partition,
                            zero_overlap_boundary_policy="nearest_center_tie_upper",
                        )
                        self.assertTrue(any(degree > 0.0 for degree in degrees))
                        if overlap == 1.0:
                            self.assertAlmostEqual(sum(raw), 1.0)
                        if overlap > 0.0:
                            self.assertTrue(any(degree > 0.0 for degree in raw))
                            self.assertFalse(boundary)
                        if boundary:
                            self.assertEqual(overlap, 0.0)
                            self.assertEqual(sum(degrees), 1.0)
                            self.assertLessEqual(max(raw), 1e-12)

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
        zero = uniform_partition(granularity=3, family="gaussian_v1", overlap=0.0)
        full = uniform_partition(granularity=3, family="gaussian_v1", overlap=1.0)
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


class TestVersionedFuzzyRuleProperties(unittest.TestCase):
    def test_captured_three_and_five_label_additive_consequents(self) -> None:
        expected = {
            3: ((1, 0, 0), (2, 1, 0), (2, 2, 1)),
            5: (
                (2, 1, 1, 0, 0),
                (3, 2, 1, 1, 0),
                (3, 3, 2, 1, 1),
                (4, 3, 3, 2, 1),
                (4, 4, 3, 3, 2),
            ),
        }
        for granularity, matrix in expected.items():
            with self.subTest(granularity=granularity):
                self.assertEqual(rule_matrix("R5", granularity), matrix)
                self.assertEqual(
                    rule_matrix("R6", granularity), tuple(reversed(matrix))
                )
                self.assertEqual(
                    rule_matrix("R7", granularity),
                    tuple(tuple(reversed(row)) for row in matrix),
                )
                self.assertEqual(
                    rule_matrix("R8", granularity),
                    tuple(
                        tuple(granularity - 1 - index for index in row)
                        for row in matrix
                    ),
                )

    def test_unknown_rule_base_is_rejected_by_canonical_controller(self) -> None:
        for granularity in (3, 5, 7, 9):
            with self.subTest(granularity=granularity):
                with self.assertRaisesRegex(ValueError, "rule_base"):
                    MamdaniController(
                        granularity=granularity,
                        rule_base="UNKNOWN",
                        membership_family="triangular_v1",
                        diversity_overlap=1.0,
                        progress_overlap=1.0,
                        output_overlap=1.0,
                    )

    def test_rule_matrices_are_complete_and_preserve_single_axis_semantics(self):
        for granularity in (3, 5, 7, 9):
            for index in range(1, 9):
                with self.subTest(granularity=granularity, rule=index):
                    matrix = rule_matrix(f"R{index}", granularity)
                    self.assertEqual(len(matrix), granularity)
                    for diversity, row in enumerate(matrix):
                        self.assertEqual(len(row), granularity)
                        for progress, output in enumerate(row):
                            self.assertIsInstance(output, int)
                            self.assertGreaterEqual(output, 0)
                            self.assertLess(output, granularity)
                            if index <= 4:
                                expected = (
                                    granularity - 1 - progress,
                                    progress,
                                    diversity,
                                    granularity - 1 - diversity,
                                )[index - 1]
                                self.assertEqual(output, expected)

    def test_mirror_rules_reflect_each_consequent(self):
        for granularity in (3, 5, 7, 9):
            for first, second in (
                ("R1", "R2"),
                ("R3", "R4"),
                ("R5", "R8"),
                ("R6", "R7"),
            ):
                with self.subTest(granularity=granularity, pair=(first, second)):
                    first_matrix = np.asarray(rule_matrix(first, granularity))
                    second_matrix = np.asarray(rule_matrix(second, granularity))
                    np.testing.assert_array_equal(
                        first_matrix + second_matrix,
                        np.full((granularity, granularity), granularity - 1),
                    )

    def test_all_rule_surfaces_are_bounded_deterministic_and_mirrored(self):
        for granularity in (3, 5, 7, 9):
            for overlap in (0.0, 0.5, 1.0):
                for first, second in (
                    ("R1", "R2"),
                    ("R3", "R4"),
                    ("R5", "R8"),
                    ("R6", "R7"),
                ):
                    common = {
                        "granularity": granularity,
                        "membership_family": "triangular_v1",
                        "diversity_overlap": overlap,
                        "progress_overlap": overlap,
                        "output_overlap": overlap,
                    }
                    first_controller = MamdaniController(rule_base=first, **common)
                    second_controller = MamdaniController(rule_base=second, **common)
                    for diversity in (0.0, 0.25, 0.5, 0.75, 1.0):
                        for progress in (0.0, 0.25, 0.5, 0.75, 1.0):
                            with self.subTest(
                                granularity=granularity,
                                overlap=overlap,
                                pair=(first, second),
                                diversity=diversity,
                                progress=progress,
                            ):
                                result = first_controller.infer(diversity, progress)
                                repeated = first_controller.infer(diversity, progress)
                                mirrored = second_controller.infer(diversity, progress)
                                self.assertEqual(result, repeated)
                                for observed in (result, mirrored):
                                    self.assertTrue(
                                        np.isfinite(observed.normalized_output)
                                    )
                                    self.assertGreaterEqual(
                                        observed.normalized_output, 0.0
                                    )
                                    self.assertLessEqual(
                                        observed.normalized_output, 1.0
                                    )
                                self.assertAlmostEqual(
                                    result.normalized_output
                                    + mirrored.normalized_output,
                                    1.0,
                                    places=12,
                                )


class TestFuzzyInertiaPolicy(unittest.TestCase):
    def test_real_diversity_retains_historical_maximum_and_maps_inference(self) -> None:
        policy = FuzzyInertiaPolicy(
            max_iterations=5,
            granularity=3,
            rule_base="R5",
            overlap=1.0,
        )
        controller = MamdaniController(
            granularity=3,
            rule_base="R5",
            membership_family="triangular_v1",
            diversity_overlap=1.0,
            progress_overlap=1.0,
            output_overlap=1.0,
        )
        population = np.array([[1.0, 2.0], [-1.0, 0.0]])
        for iteration, (scale, maximum, ratio) in enumerate(
            (
                (0.0, 0.0, 0.0),
                (1.0, 1.0, 1.0),
                (0.25, 1.0, 0.25),
                (4.0, 4.0, 1.0),
                (0.0, 4.0, 0.0),
            ),
            start=1,
        ):
            with self.subTest(iteration=iteration):
                update = policy.propose(
                    SearchState(
                        iteration=iteration,
                        evaluations=2 * iteration,
                        evaluation_budget=12,
                        best_objective=0.0,
                        observations={"positions": population * scale},
                    ),
                    {},
                )
                self.assertEqual(policy.last_diagnostics["diversity_maximum"], maximum)
                self.assertEqual(policy.last_diagnostics["diversity_ratio"], ratio)
                self.assertEqual(
                    policy.last_diagnostics["progress_ratio"], iteration / 5
                )
                expected = controller.infer(ratio, iteration / 5).normalized_output
                self.assertEqual(update.values["w"], 0.1 + expected * 0.8)

    def test_initial_swarm_drives_first_update_without_iteration_zero_inertia(
        self,
    ) -> None:
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
