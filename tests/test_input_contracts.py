from __future__ import annotations

import json
import sqlite3
import unittest
from dataclasses import replace
from pathlib import Path

from afcs.core import RandomnessConfig, ReplicaRandomStreams, SearchSpace
from afcs.core.randomness import MAX_SEED
from afcs.core.serialization import freeze_json_mapping
from afcs.experiments import (
    CampaignDefinition,
    CampaignPlanner,
    ConfigurationError,
    ExperimentRunExecutor,
    OptimizerFactory,
    parse_campaign_config,
)
from afcs.experiments.cli import campaign_preview
from afcs.fuzzy import MamdaniController, fuzzify, uniform_partition
from afcs.metrics import load_metric_registry
from afcs.optimizers.ga import RealCodedGA, RealCodedGARunConfig
from afcs.optimizers.pso import FixedInertia, LegacyCompatiblePSO, LegacyPSORunConfig
from afcs.persistence import (
    ExperimentRepository,
    MigrationError,
    RepositoryError,
    apply_migrations,
    canonical_json,
    encode_metric_value,
)
from afcs.problems import CallableProblem, ProblemMetadata


def small_config():
    raw = json.loads(
        Path("config/campaigns/cec2017_pso_v2.example.json").read_text(encoding="utf-8")
    )
    raw["campaign"].update(id="inputs", name="Input contracts", replicas=1)
    raw["problems"] = [{"family": "CLASSICAL", "functions": [1], "dimensions": [2]}]
    raw["treatments"] = raw["treatments"][:1]
    raw["treatments"][0]["parameters"].update(population_size=4, max_iterations=1)
    return raw


class TestInputContracts(unittest.TestCase):
    def setUp(self):
        self.connection = sqlite3.connect(":memory:")
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys=ON")
        apply_migrations(self.connection)
        self.repository = ExperimentRepository(self.connection, load_metric_registry())

    def tearDown(self):
        self.connection.close()

    def test_seed_boundaries_and_last_replica_are_validated_before_writes(self):
        for seed in (0, MAX_SEED):
            with self.subTest(seed=seed):
                self.assertEqual(RandomnessConfig(seed).seed_for_replica(0), seed)
                self.assertEqual(
                    ReplicaRandomStreams(seed)
                    .generator("initialization")
                    .random(2)
                    .size,
                    2,
                )
        for seed in (-1, MAX_SEED + 1):
            for constructor in (RandomnessConfig, ReplicaRandomStreams):
                with self.subTest(seed=seed, constructor=constructor):
                    with self.assertRaises(ValueError):
                        constructor(seed)
        for seed in (True, 1.5, "42"):
            with self.assertRaises(TypeError):
                RandomnessConfig(seed)
        self.assertEqual(RandomnessConfig(MAX_SEED - 1).seed_for_replica(1), MAX_SEED)
        with self.assertRaises(ValueError):
            RandomnessConfig(MAX_SEED).seed_for_replica(1)
        with self.assertRaises(ValueError):
            CampaignDefinition("bad", "bad", {}, "test", 2, RandomnessConfig(MAX_SEED))
        raw = small_config()
        raw["randomness"]["base_seed"] = MAX_SEED
        raw["campaign"]["replicas"] = 2
        with self.assertRaisesRegex(ConfigurationError, "replica seed"):
            parse_campaign_config(raw, code_commit="test")
        with self.assertRaises(RepositoryError):
            self.repository.create_campaign(
                "bad",
                "bad",
                {},
                "test",
                base_seed=MAX_SEED + 1,
                seed_protocol="paired_by_replica_v1",
                rng_engine="numpy_seedsequence_pcg64_v1",
            )
        self.assertEqual(
            self.connection.execute("SELECT COUNT(*) FROM campaigns").fetchone()[0], 0
        )

    def test_maximum_seed_persists_and_executes(self):
        raw = small_config()
        raw["randomness"]["base_seed"] = MAX_SEED
        loaded = parse_campaign_config(raw, code_commit="test")
        plan = CampaignPlanner(self.repository).persist(
            loaded.campaign, loaded.treatments
        )
        run_id = plan.run_ids[0]
        stored = self.repository.get_planned_run(run_id)
        self.assertEqual(stored.random_seed, MAX_SEED)
        with self.assertRaises(RepositoryError):
            self.repository.plan_run("inputs", stored.algorithm, 1, 1, MAX_SEED + 1)
        self.repository.start_campaign("inputs")
        optimizer = OptimizerFactory().build(
            stored, selected_metrics=self.repository.selected_metric_ids("inputs")
        )
        result = ExperimentRunExecutor(self.repository).execute(run_id, optimizer)
        self.assertEqual(result.evaluations, 8)

    def test_nested_snapshots_are_detached_and_protected_through_persistence(self):
        raw = small_config()
        raw["campaign"]["metrics"] = {"profile": "minimal", "include": []}
        loaded = parse_campaign_config(raw, code_commit="test")
        raw["treatments"][0]["parameters"]["population_size"] = 999
        for snapshot in (loaded.resolved_config, loaded.campaign.source_config):
            self.assertEqual(
                snapshot["treatments"][0]["parameters"]["population_size"], 4
            )
            with self.assertRaises(TypeError):
                snapshot["treatments"][0]["parameters"]["population_size"] = 999
            with self.assertRaises(TypeError):
                snapshot["problems"][0]["dimensions"][0] = 999
        with self.assertRaises(TypeError):
            loaded.campaign.metric_selection["profile"] = "all"
        preview = campaign_preview(loaded)
        self.assertEqual(json.loads(json.dumps(preview))["summary"]["total_runs"], 1)
        self.assertEqual(preview["problems"][0]["dimensions"], [2])
        plan = CampaignPlanner(self.repository).persist(
            loaded.campaign, loaded.treatments
        )
        stored = self.repository.get_planned_run(plan.run_ids[0])
        self.assertEqual(stored.population_size, 4)
        self.assertEqual(
            stored.campaign_config["treatments"][0]["parameters"]["population_size"], 4
        )
        for snapshot in (
            stored.campaign_config,
            self.repository.campaign_config("inputs"),
        ):
            with self.assertRaises(TypeError):
                snapshot["treatments"][0]["parameters"]["population_size"] = 999

    def test_problem_and_optimizer_metadata_freeze_nested_values(self):
        parameters = {"nested": {"values": [1, 2]}}
        problem = ProblemMetadata(
            "sphere", "test", SearchSpace.uniform(2, -5.0, 5.0), parameters=parameters
        )
        parameters["nested"]["values"][0] = 999
        self.assertEqual(problem.parameters["nested"]["values"], (1, 2))
        with self.assertRaises(TypeError):
            problem.parameters["nested"]["values"][0] = 999
        loaded = parse_campaign_config(small_config(), code_commit="test")
        metadata = replace(loaded.treatments[0].run_metadata, parameters=parameters)
        parameters["nested"]["values"][0] = 888
        self.assertEqual(metadata.parameters["nested"]["values"][0], 999)
        with self.assertRaises(TypeError):
            metadata.parameters["nested"]["values"][0] = 777
        self.assertEqual(
            canonical_json(metadata.parameters), '{"nested":{"values":[999,2]}}'
        )

    def test_strict_json_rejects_nonfinite_nested_values_keys_and_cycles(self):
        cyclic = []
        cyclic.append(cyclic)
        for invalid in (
            {"nested": [float("nan")]},
            {"nested": [float("inf")]},
            {"nested": [float("-inf")]},
            {1: "value"},
            cyclic,
            {"set": {1}},
        ):
            with self.subTest(invalid_type=type(invalid).__name__):
                with self.assertRaises((TypeError, ValueError)):
                    canonical_json(invalid)
                with self.assertRaises(RepositoryError):
                    encode_metric_value(invalid, "json")
        value = {"nested": [None, True, 2, 0.5, {"label": "valid"}]}
        snapshot = freeze_json_mapping(value)
        self.assertEqual(json.loads(canonical_json(snapshot)), value)
        self.assertEqual(canonical_json(value), canonical_json(snapshot))
        raw = small_config()
        raw["_documentation"] = {"invalid": [float("nan")]}
        with self.assertRaisesRegex(ConfigurationError, "finite"):
            parse_campaign_config(raw, code_commit="test")

    def test_invalid_json_trace_does_not_leave_partial_checkpoint(self):
        self.repository.create_campaign(
            "json", "json", {}, "test", ["fuzzy_membership_degrees"]
        )
        instance = self.repository.add_problem_instance("test", "sphere", 2)
        self.repository.add_algorithm_configuration(
            "config", "json", "PSO", "test", {}, "evaluations", budget_evaluations=8
        )
        run_id = self.repository.plan_run("json", "config", instance, 0)
        self.repository.start_campaign("json")
        self.repository.start_run(run_id)
        with self.assertRaisesRegex(RepositoryError, "finite"):
            self.repository.record_trace(
                run_id,
                0,
                0,
                4,
                {
                    "objective_best": 1.0,
                    "fuzzy_membership_degrees": {"bad": [float("inf")]},
                },
            )
        self.assertEqual(
            self.connection.execute("SELECT COUNT(*) FROM trace_points").fetchone()[0],
            0,
        )
        self.assertEqual(self.repository.run_status(run_id), "running")

    def test_migrations_reject_active_transaction_without_committing_or_rollback(self):
        self.connection.execute("CREATE TABLE probe(value TEXT)")
        self.connection.commit()
        self.connection.execute("INSERT INTO probe VALUES('pending')")
        with self.assertRaisesRegex(MigrationError, "active transaction"):
            apply_migrations(self.connection)
        self.assertTrue(self.connection.in_transaction)
        self.assertEqual(
            self.connection.execute("SELECT COUNT(*) FROM probe").fetchone()[0], 1
        )
        self.connection.rollback()
        self.assertEqual(
            self.connection.execute("SELECT COUNT(*) FROM probe").fetchone()[0], 0
        )
        self.assertEqual(apply_migrations(self.connection), ())
        fresh = sqlite3.connect(":memory:")
        self.addCleanup(fresh.close)
        fresh.execute("CREATE TABLE probe(value TEXT)")
        fresh.execute("INSERT INTO probe VALUES('pending')")
        with self.assertRaisesRegex(MigrationError, "active transaction"):
            apply_migrations(fresh)
        self.assertTrue(fresh.in_transaction)
        self.assertIsNone(
            fresh.execute(
                "SELECT name FROM sqlite_master WHERE name='schema_migrations'"
            ).fetchone()
        )
        fresh.rollback()
        self.assertEqual(fresh.execute("SELECT COUNT(*) FROM probe").fetchone()[0], 0)


class TestFuzzyFiniteInputs(unittest.TestCase):
    def test_both_inputs_reject_nonfinite_for_both_families_and_modes(self):
        for family in ("triangular_v1", "gaussian_v1"):
            partition = uniform_partition(granularity=3, family=family, overlap=1.0)
            for mode in ("dense_v1", "sparse_v1"):
                controller = MamdaniController(
                    granularity=3,
                    rule_base="R5",
                    membership_family=family,
                    diversity_overlap=1.0,
                    progress_overlap=1.0,
                    output_overlap=1.0,
                    evaluation_mode=mode,
                )
                for value in (float("nan"), float("inf"), float("-inf")):
                    with self.subTest(family=family, mode=mode, value=value):
                        with self.assertRaisesRegex(ValueError, "finite"):
                            fuzzify(
                                value,
                                partition,
                                zero_overlap_boundary_policy="nearest_center_tie_upper",
                            )
                        with self.assertRaisesRegex(ValueError, "finite"):
                            controller.infer(value, 0.5)
                        with self.assertRaisesRegex(ValueError, "finite"):
                            controller.infer(0.5, value)
                self.assertEqual(
                    controller.infer(-1.0, 0.5), controller.infer(0.0, 0.5)
                )
                self.assertEqual(controller.infer(2.0, 0.5), controller.infer(1.0, 0.5))
                self.assertEqual(
                    controller.infer(0.5, -1.0), controller.infer(0.5, 0.0)
                )
                self.assertEqual(controller.infer(0.5, 2.0), controller.infer(0.5, 1.0))


class TestOptimizerSingleUse(unittest.TestCase):
    def test_success_and_failure_consume_instance_without_second_evaluation(self):
        for algorithm in ("PSO", "GA"):
            for failure in (None, "objective", "clock"):
                with self.subTest(algorithm=algorithm, failure=failure):
                    calls = []
                    clock_calls = []

                    def clock():
                        clock_calls.append(None)
                        if failure == "clock":
                            raise ValueError("synthetic clock failure")
                        return float(len(clock_calls))

                    def objective(candidate):
                        calls.append(candidate)
                        if failure == "objective":
                            raise ValueError("synthetic objective failure")
                        return sum(value * value for value in candidate)

                    problem = CallableProblem(
                        ProblemMetadata(
                            "sphere", "test", SearchSpace.uniform(2, -5.0, 5.0)
                        ),
                        objective,
                    )
                    if algorithm == "PSO":
                        optimizer = LegacyCompatiblePSO(
                            problem=problem,
                            config=LegacyPSORunConfig(4, 1),
                            inertia_policy=FixedInertia(0.5),
                            random_streams=ReplicaRandomStreams(42),
                            clock=clock,
                        )
                    else:
                        optimizer = RealCodedGA(
                            problem=problem,
                            config=RealCodedGARunConfig(4, 1),
                            random_streams=ReplicaRandomStreams(42),
                            clock=clock,
                        )
                    if failure:
                        with self.assertRaisesRegex(ValueError, "synthetic"):
                            optimizer.run()
                    else:
                        self.assertEqual(optimizer.run().evaluations, 8)
                    count = len(calls)
                    clock_count = len(clock_calls)
                    with self.assertRaisesRegex(RuntimeError, "single-use"):
                        optimizer.run()
                    self.assertEqual(len(calls), count)
                    self.assertEqual(len(clock_calls), clock_count)


if __name__ == "__main__":
    unittest.main()
