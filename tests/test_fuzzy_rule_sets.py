import itertools
import unittest

import numpy as np

from FUZZY.fuzzy_controller_w_3L import FuzzyInertiaController_3L
from FUZZY.fuzzy_controller_w_5L import FuzzyInertiaController_5L


RULE_SETS = tuple(f"R{index}" for index in range(1, 9))


class TestFuzzyRuleSets(unittest.TestCase):
    def _assert_rule_matrix(self, controller_class, diversity_labels, progress_labels):
        expected_keys = set(itertools.product(diversity_labels, progress_labels))
        valid_outputs = set(diversity_labels)

        for rule_set in RULE_SETS:
            with self.subTest(controller=controller_class.__name__, rule_set=rule_set):
                controller = controller_class("O1", rule_set=rule_set)
                self.assertEqual(set(controller.rules), expected_keys)
                self.assertTrue(set(controller.rules.values()) <= valid_outputs)

                for diversity, progress in itertools.product(
                    (0.0, 0.25, 0.5, 0.75, 1.0), repeat=2
                ):
                    weight = controller.compute_w(diversity, progress)
                    self.assertTrue(np.isfinite(weight))
                    self.assertGreaterEqual(weight, controller.wMin)
                    self.assertLessEqual(weight, controller.wMax)

    def test_all_3l_rule_sets_are_complete_and_operational(self):
        self._assert_rule_matrix(
            FuzzyInertiaController_3L,
            ("low", "medium", "high"),
            ("early", "mid", "late"),
        )

    def test_all_5l_rule_sets_are_complete_and_operational(self):
        self._assert_rule_matrix(
            FuzzyInertiaController_5L,
            ("very_low", "low", "medium", "high", "very_high"),
            ("very_early", "early", "mid", "late", "very_late"),
        )

    def test_unknown_rule_set_is_rejected(self):
        for controller_class in (
            FuzzyInertiaController_3L,
            FuzzyInertiaController_5L,
        ):
            with self.subTest(controller=controller_class.__name__):
                with self.assertRaises(ValueError):
                    controller_class("O1", rule_set="UNKNOWN")


if __name__ == "__main__":
    unittest.main()
