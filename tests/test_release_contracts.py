import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

import numpy as np

from afcs.analysis import run_campaign_analysis
from afcs.core import Evaluation, ReplicaRandomStreams, SearchSpace
from afcs.experiments import (
    CampaignOrchestrator,
    CampaignPlanner,
    ExperimentRunExecutor,
    OptimizerFactory,
    parse_campaign_config,
)
from afcs.metrics import hussain_diversity_v1, load_metric_registry
from afcs.optimizers import SearchState
from afcs.optimizers.ga import RealCodedGA, RealCodedGARunConfig
from afcs.optimizers.pso import (
    FixedInertia,
    FuzzyInertiaPolicy,
    LegacyCompatiblePSO,
    LegacyPSORunConfig,
)
from afcs.persistence import ExperimentRepository, apply_migrations
from afcs.problems import CallableProblem, ProblemMetadata


class TestReleaseContracts(unittest.TestCase):
    def problem(self, lower=(-5.0, -20.0), upper=(0.0, -10.0), evaluation=None):
        return CallableProblem(
            ProblemMetadata("sphere", "test", SearchSpace(tuple(lower), tuple(upper))),
            evaluation or (lambda x: float(np.sum(np.asarray(x) ** 2))),
        )

    def test_domain_width_velocity_moves_on_negative_domains_and_is_versioned(self):
        config = LegacyPSORunConfig(4, 2, velocity_rule="domain_width_v1")
        problem = self.problem()
        optimizer = LegacyCompatiblePSO(
            problem=problem,
            config=config,
            inertia_policy=FixedInertia(0.5),
            random_streams=ReplicaRandomStreams(42),
        )
        initial = (
            ReplicaRandomStreams(42)
            .generator("initialization")
            .uniform([-5.0, -20.0], [0.0, -10.0], size=(4, 2))
        )
        result = optimizer.run()
        self.assertFalse(np.array_equal(result.positions, initial))
        self.assertEqual(result.evaluations, 12)
        self.assertEqual(
            optimizer.run_metadata.optimizer.version, "2.0.0a1-domain-width"
        )
        self.assertEqual(
            optimizer.run_metadata.parameters["velocity_rule"], "domain_width_v1"
        )

    def test_velocity_limits_are_per_dimension_and_translation_invariant(self):
        from afcs.optimizers.pso.core import PSOConfig, advance_swarm

        limits = 0.1 * (np.array([0.0, -10.0]) - np.array([-5.0, -20.0]))
        for offset in (0.0, 100.0):
            step = advance_swarm(
                positions=np.array([[0.0, 0.0]]) + offset,
                velocities=np.zeros((1, 2)),
                personal_best=np.array([[0.0, 0.0]]) + offset,
                global_best=np.array([100.0, 100.0]) + offset,
                cognitive_random=np.ones((1, 2)),
                social_random=np.ones((1, 2)),
                inertia=0.5,
                maximum_velocity=limits,
                config=PSOConfig(),
            )
            np.testing.assert_array_equal(step.velocities, [[0.5, 1.0]])

    def test_endpoint_linear_schedule_preserves_declared_extremes(self):
        from afcs.optimizers.pso import EndpointLinearInertia

        for count in (1, 2, 100):
            policy = EndpointLinearInertia(count, maximum=0.9, minimum=0.1)
            self.assertEqual(policy.value_at(1), 0.9)
            self.assertEqual(policy.value_at(count), 0.9 if count == 1 else 0.1)
            self.assertEqual(policy.policy_id, "linear_endpoints_v1")

    def test_unrounded_diversity_retains_small_nonzero_feedback(self):
        from afcs.metrics import hussain_diversity_v2

        population = np.array([[0.0], [0.0004]])
        self.assertEqual(hussain_diversity_v1(population), 0.0)
        self.assertEqual(hussain_diversity_v2(population), 0.0002)
        policy = FuzzyInertiaPolicy(
            max_iterations=2,
            granularity=3,
            rule_base="R1",
            overlap=0.5,
            diversity_metric="hussain_diversity_v2",
        )
        self.assertEqual(policy.policy_version, "2")
        self.assertEqual(
            policy.configuration["diversity_metric"], "hussain_diversity_v2"
        )
        for iteration, positions, expected in (
            (1, population, 1.0),
            (2, population / 2, 0.5),
        ):
            policy.propose(
                SearchState(
                    iteration, 2, 6, 0.0, observations={"positions": positions}
                ),
                {"w": 0.5},
            )
            self.assertEqual(policy.last_diagnostics["diversity_ratio"], expected)

    def test_constrained_evaluations_are_explicitly_rejected_by_both_optimizers(self):
        for feasible, violation in ((False, 2.0), (True, 0.1)):
            problem = self.problem(
                upper=(5.0, 20.0),
                evaluation=lambda x: Evaluation(0.0, feasible, violation),
            )
            for optimizer in (
                LegacyCompatiblePSO(
                    problem=problem,
                    config=LegacyPSORunConfig(4, 1),
                    inertia_policy=FixedInertia(0.5),
                    rng=np.random.default_rng(42),
                ),
                RealCodedGA(
                    problem=problem,
                    config=RealCodedGARunConfig(4, 1),
                    rng=np.random.default_rng(42),
                ),
            ):
                with self.subTest(
                    feasible=feasible, optimizer=type(optimizer).__name__
                ):
                    with self.assertRaisesRegex(ValueError, "constraints"):
                        optimizer.run()

    def test_new_variants_roundtrip_through_configuration(self):
        raw = json.loads(
            Path("config")
            .joinpath("campaigns", "cec2017_pso_v2.example.json")
            .read_text(encoding="utf-8")
        )
        raw["problems"] = [{"family": "CLASSICAL", "functions": [1], "dimensions": [2]}]
        raw["treatments"] = raw["treatments"][:1]
        treatment = raw["treatments"][0]
        treatment["parameters"]["velocity_rule"] = "domain_width_v1"
        treatment["parameter_policy"] = {
            "id": "linear_endpoints_v1",
            "parameters": {"maximum": 0.9, "minimum": 0.1},
        }
        loaded = parse_campaign_config(raw, code_commit="test")
        second = parse_campaign_config(json.loads(json.dumps(raw)), code_commit="test")
        self.assertEqual(loaded.treatments, second.treatments)

    def test_new_campaign_variants_persist_execute_and_export_with_exact_identity(self):
        raw = json.loads(
            Path("config")
            .joinpath("campaigns", "cec2017_pso_v2.example.json")
            .read_text(encoding="utf-8")
        )
        raw["problems"] = [{"family": "CLASSICAL", "functions": [1], "dimensions": [2]}]
        raw["campaign"].update(replicas=1, metrics="fuzzy")
        raw["treatments"] = [raw["treatments"][0]]
        first = raw["treatments"][0]
        first["parameters"].update(
            population_size=4, max_iterations=2, velocity_rule="domain_width_v1"
        )
        linear = json.loads(json.dumps(first))
        linear.update(
            id="new-linear",
            parameter_policy={
                "id": "linear_endpoints_v1",
                "parameters": {"maximum": 0.9, "minimum": 0.1},
            },
        )
        fuzzy = json.loads(json.dumps(first))
        fuzzy.update(
            id="new-fuzzy",
            parameter_policy={
                "id": "fuzzy_inertia_mamdani",
                "parameters": {
                    "minimum": 0.1,
                    "maximum": 0.9,
                    "granularity": 3,
                    "rule_base": "R1",
                    "membership_family": "triangular_v1",
                    "overlap": {"mode": "shared", "value": 0.5},
                    "zero_overlap_boundary_policy": "nearest_center_tie_upper",
                    "diversity_metric": "hussain_diversity_v2",
                },
            },
        )
        raw["treatments"].extend([linear, fuzzy])
        loaded = parse_campaign_config(raw, code_commit="test")
        connection = sqlite3.connect(":memory:")
        self.addCleanup(connection.close)
        connection.row_factory = sqlite3.Row
        apply_migrations(connection)
        repository = ExperimentRepository(connection, load_metric_registry())
        plan = CampaignPlanner(repository).persist(loaded.campaign, loaded.treatments)
        for run in plan.run_ids:
            optimizer = OptimizerFactory().build(
                repository.get_planned_run(run),
                selected_metrics=repository.selected_metric_ids(
                    loaded.campaign.campaign_id
                ),
            )
            self.assertEqual(
                optimizer.run_metadata.parameters,
                loaded.treatments[plan.run_ids.index(run)].run_metadata.parameters,
            )
            self.assertEqual(
                optimizer.run_metadata.optimizer.version, "2.0.0a1-domain-width"
            )
        summary = CampaignOrchestrator(repository).execute_pending(
            loaded.campaign.campaign_id
        )
        self.assertEqual(summary.completed, 3)
        repository.seal_campaign(loaded.campaign.campaign_id)
        with tempfile.TemporaryDirectory() as directory:
            result = run_campaign_analysis(
                connection, loaded.campaign.campaign_id, directory
            )
            text = Path(result.report_path).read_text(encoding="utf-8")
            self.assertIn("2.0.0a1-domain-width", text)
            runs_text = (Path(directory) / "runs.csv").read_text(encoding="utf-8")
            self.assertIn("hussain_diversity_v2", runs_text)
            self.assertIn("linear_endpoints_v1", runs_text)

    def test_recommended_template_sequential_parallel_scientific_equivalence(self):
        from afcs.persistence import initialize_v2_database

        raw = json.loads(
            Path("config")
            .joinpath("campaigns", "classical_pso_recommended_v2.example.json")
            .read_text(encoding="utf-8")
        )
        with tempfile.TemporaryDirectory() as directory:
            results = []
            for workers in (1, 2):
                raw["execution"]["parallel_workers"] = workers
                loaded = parse_campaign_config(raw, code_commit="test")
                connection = initialize_v2_database(
                    Path(directory) / f"workers{workers}.db"
                )
                try:
                    repository = ExperimentRepository(
                        connection, load_metric_registry()
                    )
                    CampaignPlanner(repository).persist(
                        loaded.campaign, loaded.treatments
                    )
                    summary = CampaignOrchestrator(repository).execute_pending(
                        loaded.campaign.campaign_id
                    )
                    self.assertEqual(summary.completed, 3)
                    results.append(
                        [
                            tuple(row)
                            for row in connection.execute(
                                "SELECT ac.treatment_id,r.objective_best,r.solution_json,r.evaluations,"
                                "r.initial_population_sha256,r.initial_velocity_sha256,r.initial_state_hash_version "
                                "FROM runs r JOIN algorithm_configurations ac USING(configuration_id) "
                                "ORDER BY ac.treatment_id"
                            )
                        ]
                    )
                finally:
                    connection.close()
            self.assertEqual(results[0], results[1])

    def test_old_versions_and_degenerate_velocity_remain_explicit_not_relabelled(self):
        from afcs.optimizers.pso import LegacyLinearInertia

        problem = self.problem()
        optimizer = LegacyCompatiblePSO(
            problem=problem,
            config=LegacyPSORunConfig(4, 2),
            inertia_policy=FixedInertia(0.5),
            random_streams=ReplicaRandomStreams(42),
        )
        self.assertEqual(
            optimizer.run_metadata.optimizer.version, "2.0.0a0-legacy-compatible"
        )
        self.assertNotIn("velocity_rule", optimizer.run_metadata.parameters)
        initial = (
            ReplicaRandomStreams(42)
            .generator("initialization")
            .uniform([-5.0, -20.0], [0.0, -10.0], size=(4, 2))
        )
        np.testing.assert_array_equal(optimizer.run().positions, initial)
        policy = LegacyLinearInertia(100)
        self.assertEqual(policy.value_at(1), 0.892)
        self.assertAlmostEqual(policy.value_at(100), 0.1)
        fuzzy = FuzzyInertiaPolicy(
            max_iterations=2, granularity=3, rule_base="R1", overlap=0.5
        )
        self.assertEqual(fuzzy.policy_version, "1")
        self.assertEqual(
            fuzzy.configuration["diversity_metric"], "hussain_diversity_v1"
        )

    def test_version_definition_mismatch_is_rejected_by_factory(self):
        from afcs.experiments.factory import _build_inertia_policy

        policy = FuzzyInertiaPolicy(
            max_iterations=2,
            granularity=3,
            rule_base="R1",
            overlap=0.5,
            diversity_metric="hussain_diversity_v2",
        )
        for version in ("1", "3"):
            with self.assertRaisesRegex(ValueError, "version"):
                _build_inertia_policy(
                    {
                        "policy_id": policy.policy_id,
                        "policy_version": version,
                        "configuration": policy.configuration,
                    },
                    2,
                )

    def test_new_policy_inputs_and_schedule_indices_are_validated(self):
        from afcs.optimizers.pso import EndpointLinearInertia

        with self.assertRaises(ValueError):
            LegacyPSORunConfig(4, 2, velocity_rule="unknown")
        with self.assertRaises(ValueError):
            FuzzyInertiaPolicy(
                max_iterations=2,
                granularity=3,
                rule_base="R1",
                overlap=0.5,
                diversity_metric="unknown",
            )
        for value in (True, -1, 3):
            with self.assertRaises((TypeError, ValueError)):
                EndpointLinearInertia(2).value_at(value)

    def test_in_memory_rng_does_not_invent_campaign_provenance(self):
        optimizer = LegacyCompatiblePSO(
            problem=self.problem(upper=(5.0, 20.0)),
            config=LegacyPSORunConfig(4, 1),
            inertia_policy=FixedInertia(0.5),
            rng=np.random.default_rng(42),
        )
        self.assertIsNone(optimizer.run_metadata.replica_seed)
        self.assertIsNone(optimizer.run_metadata.rng_engine)

    def test_constraint_rejection_persists_failed_attempt_not_a_completed_result(self):
        problem = self.problem(
            upper=(5.0, 20.0), evaluation=lambda x: Evaluation(0.0, False, 2.0)
        )
        optimizer = LegacyCompatiblePSO(
            problem=problem,
            config=LegacyPSORunConfig(4, 1),
            inertia_policy=FixedInertia(0.5),
            rng=np.random.default_rng(42),
        )
        connection = sqlite3.connect(":memory:")
        self.addCleanup(connection.close)
        connection.row_factory = sqlite3.Row
        apply_migrations(connection)
        repository = ExperimentRepository(connection, load_metric_registry())
        repository.create_campaign(
            "constraints", "Unsupported constraints", {}, "test", "minimal"
        )
        instance = repository.add_problem_instance("test", "sphere", 2)
        repository.add_algorithm_configuration(
            "pso",
            "constraints",
            "PSO",
            optimizer.run_metadata.optimizer.version,
            optimizer.run_metadata.parameters,
            "evaluations",
            budget_evaluations=8,
            budget_iterations=1,
            population_size=4,
        )
        run = repository.plan_run("constraints", "pso", instance, 0)
        repository.start_campaign("constraints")
        with self.assertRaisesRegex(ValueError, "constraints"):
            ExperimentRunExecutor(repository).execute(run, optimizer)
        row = connection.execute(
            "SELECT status,failure_phase,objective_best,solution_json FROM runs"
        ).fetchone()
        self.assertEqual(tuple(row), ("failed", "optimization", None, None))
        self.assertEqual(
            connection.execute("SELECT status FROM run_attempts").fetchone()[0],
            "failed",
        )
