import unittest

from afcs.controllers import NoAdaptation, ParameterPolicy, ParameterUpdate
from afcs.optimizers import OptimizerMetadata, SearchState
from afcs.optimizers.pso import LegacyLinearInertia


class TestOptimizerContracts(unittest.TestCase):
    def setUp(self):
        self.state = SearchState(
            iteration=2,
            evaluations=20,
            evaluation_budget=100,
            best_objective=1.5,
            observations={"diversity": 0.4},
        )

    def test_search_state_is_read_only_and_reports_nfe_progress(self):
        self.assertEqual(self.state.progress, 0.2)
        with self.assertRaises(TypeError):
            self.state.observations["diversity"] = 0.8

    def test_no_adaptation_is_an_explicit_policy(self):
        policy = NoAdaptation()
        self.assertIsInstance(policy, ParameterPolicy)
        update = policy.propose(self.state, {"w": 0.7})
        self.assertEqual(dict(update.values), {})
        self.assertEqual(update.policy_id, "no_adaptation")

    def test_parameter_updates_reject_non_finite_values(self):
        with self.assertRaisesRegex(ValueError, "finite"):
            ParameterUpdate("policy", "1", {"w": float("nan")})

    def test_optimizer_metadata_requires_adaptable_parameters_to_be_declared(self):
        with self.assertRaisesRegex(ValueError, "configurable"):
            OptimizerMetadata(
                optimizer_id="PSO",
                version="1",
                configurable_parameters=("c1", "c2"),
                adaptable_parameters=("w",),
            )

    def test_legacy_ldiw_reproduces_historical_schedule(self):
        policy = LegacyLinearInertia(max_iterations=10)
        self.assertEqual(policy.value_at(0), 0.9)
        self.assertAlmostEqual(policy.value_at(2), 0.74)
        self.assertAlmostEqual(policy.value_at(10), 0.1)
        update = policy.propose(self.state, {"w": 0.9})
        self.assertAlmostEqual(update.values["w"], 0.74)
        self.assertEqual(update.policy_id, "legacy_ldiw")


if __name__ == "__main__":
    unittest.main()

