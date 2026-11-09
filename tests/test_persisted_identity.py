import csv
import hashlib
import json
import sqlite3
import tempfile
import unittest
from contextlib import closing
from dataclasses import fields, replace
from pathlib import Path

import numpy as np

from afcs.analysis import export_campaign_csv
from afcs.core import ReplicaRandomStreams, SearchSpace
from afcs.experiments import (
    CampaignPlanner,
    ExperimentRunExecutor,
    OptimizerFactory,
    parse_campaign_config,
)
from afcs.metrics import load_metric_registry
from afcs.optimizers.ga import RealCodedGA, RealCodedGARunConfig
from afcs.optimizers.pso import FixedInertia, LegacyCompatiblePSO, LegacyPSORunConfig
from afcs.persistence import (
    ExperimentRepository,
    RepositoryError,
    apply_migrations,
    discover_migrations,
)
from afcs.problems import CallableProblem, ProblemMetadata


def small_config(campaign_id, *, ga=False):
    filename = "real_coded_ga_v2.example.json" if ga else "cec2017_pso_v2.example.json"
    raw = json.loads(
        Path("config").joinpath("campaigns", filename).read_text(encoding="utf-8")
    )
    raw["campaign"].update(id=campaign_id, replicas=1, metrics="minimal")
    raw["problems"] = [{"family": "CLASSICAL", "functions": [1], "dimensions": [2]}]
    raw["treatments"] = raw["treatments"][:1]
    raw["treatments"][0]["id"] = "shared-label"
    raw["treatments"][0]["parameters"].update(population_size=4, max_iterations=1)
    return parse_campaign_config(raw, code_commit="test")


class TestPersistedIdentity(unittest.TestCase):
    def setUp(self):
        self.connection = sqlite3.connect(":memory:")
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys=ON")
        self.addCleanup(self.connection.close)
        apply_migrations(self.connection)
        self.repository = ExperimentRepository(self.connection, load_metric_registry())

    def test_same_local_treatment_id_coexists_and_executes_across_campaigns(self):
        plans = []
        for campaign_id in ("first", "second"):
            loaded = small_config(campaign_id, ga=campaign_id == "second")
            plan = CampaignPlanner(self.repository).persist(
                loaded.campaign, loaded.treatments
            )
            plans.append(plan)
            self.repository.start_campaign(campaign_id)
            optimizer = OptimizerFactory().build(
                self.repository.get_planned_run(plan.run_ids[0]),
                selected_metrics=self.repository.selected_metric_ids(campaign_id),
            )
            result = ExperimentRunExecutor(self.repository).execute(
                plan.run_ids[0], optimizer
            )
            self.assertEqual(result.evaluations, 8)
        self.assertNotEqual(plans[0].configuration_ids, plans[1].configuration_ids)
        rows = self.connection.execute(
            "SELECT configuration_id, treatment_id FROM algorithm_configurations"
        ).fetchall()
        self.assertEqual([row["treatment_id"] for row in rows], ["shared-label"] * 2)
        hashes = self.connection.execute(
            "SELECT initial_population_sha256,initial_state_hash_version FROM runs"
        ).fetchall()
        self.assertEqual(tuple(hashes[0]), tuple(hashes[1]))
        with tempfile.TemporaryDirectory() as directory:
            for campaign_id in ("first", "second"):
                runs = Path(directory) / (campaign_id + ".csv")
                traces = Path(directory) / (campaign_id + "-traces.csv")
                export_campaign_csv(self.connection, campaign_id, runs, traces)
                with runs.open(encoding="utf-8", newline="") as file:
                    row = next(csv.DictReader(file))
                self.assertEqual(row["configuration_id"], "shared-label")
                self.assertIn(
                    row["configuration_key"],
                    [item["configuration_id"] for item in rows],
                )
                self.assertEqual(
                    row["initial_state_hash_version"], "array_f64le_shape_v1"
                )
                self.assertEqual(len(row["initial_population_sha256"]), 64)
                with traces.open(encoding="utf-8", newline="") as file:
                    trace = next(csv.DictReader(file))
                self.assertEqual(trace["configuration_key"], row["configuration_key"])
                self.assertEqual(trace["instance_id"], row["instance_id"])

    def test_configuration_scope_is_unambiguous_and_keeps_local_label_unique(self):
        plans = []
        for campaign_id, label in (("a:b", "c"), ("a", "b:c")):
            loaded = small_config(campaign_id)
            treatments = (replace(loaded.treatments[0], configuration_id=label),)
            plans.append(
                CampaignPlanner(self.repository).persist(loaded.campaign, treatments)
            )
        self.assertNotEqual(plans[0].configuration_ids, plans[1].configuration_ids)
        self.repository.create_campaign("direct", "direct", {}, "test")
        self.repository.add_algorithm_configuration(
            "key-one",
            "direct",
            "PSO",
            "test",
            {},
            "evaluations",
            budget_evaluations=8,
            treatment_id="label",
        )
        with self.assertRaises((RepositoryError, sqlite3.IntegrityError)):
            self.repository.add_algorithm_configuration(
                "key-two",
                "direct",
                "PSO",
                "test",
                {},
                "evaluations",
                budget_evaluations=8,
                treatment_id="label",
            )

    def test_problem_conflicts_are_explicit_and_never_mutate_shared_metadata(self):
        first = self.repository.add_problem_instance(
            "test", "same", 2, 0.0, "minimize", {"variant": 1}, "a" * 64
        )
        self.assertEqual(
            first,
            self.repository.add_problem_instance(
                "test", "same", 2, 0.0, "minimize", {"variant": 1}, "a" * 64
            ),
        )
        for optimum, direction, digest in (
            (10.0, "minimize", "a" * 64),
            (0.0, "maximize", "a" * 64),
            (0.0, "minimize", "b" * 64),
            (None, "minimize", "a" * 64),
            (0.0, "minimize", None),
        ):
            with self.subTest(optimum=optimum, direction=direction, digest=digest):
                with self.assertRaisesRegex(RepositoryError, "identity conflict"):
                    self.repository.add_problem_instance(
                        "test", "same", 2, optimum, direction, {"variant": 1}, digest
                    )
        row = self.connection.execute(
            "SELECT * FROM problem_instances WHERE instance_id=?", (first,)
        ).fetchone()
        self.assertEqual(
            (row["optimum"], row["direction"], row["data_sha256"]),
            (0.0, "minimize", "a" * 64),
        )
        distinct = self.repository.add_problem_instance(
            "test", "same", 2, 0.0, "minimize", {"variant": 2}, "a" * 64
        )
        self.assertNotEqual(first, distinct)

    def test_problem_conflict_rolls_back_second_campaign(self):
        first = small_config("first")
        CampaignPlanner(self.repository).persist(first.campaign, first.treatments)
        second = small_config("second")
        metadata = second.treatments[0].run_metadata
        conflict = replace(
            second.treatments[0],
            run_metadata=replace(
                metadata, problem=replace(metadata.problem, known_optimum=123.0)
            ),
        )
        with self.assertRaisesRegex(RepositoryError, "identity conflict"):
            CampaignPlanner(self.repository).persist(second.campaign, (conflict,))
        self.assertEqual(
            self.connection.execute("SELECT campaign_id FROM campaigns").fetchall()[0][
                0
            ],
            "first",
        )
        self.assertEqual(
            self.connection.execute("SELECT COUNT(*) FROM campaigns").fetchone()[0], 1
        )

    def test_export_preserves_distinct_instance_ids_and_parameters_with_same_labels(
        self,
    ):
        self.repository.create_campaign("instances", "Instances", {}, "test")
        self.repository.add_algorithm_configuration(
            "config",
            "instances",
            "PSO",
            "test",
            {},
            "evaluations",
            budget_evaluations=8,
        )
        run_ids = []
        for variant in (1, 2):
            instance_id = self.repository.add_problem_instance(
                "test", "same-label", 2, parameters={"variant": variant}
            )
            run_ids.append(
                self.repository.plan_run("instances", "config", instance_id, 0)
            )
        self.repository.start_campaign("instances")
        for run_id in run_ids:
            self.repository.start_run(run_id)
            self.repository.record_trace(run_id, 0, 0, 8, {"objective_best": 1.0})
            self.repository.complete_run(
                run_id, 1.0, [0.0, 0.0], 8, 0.01, metrics={"objective_best": 1.0}
            )
        with tempfile.TemporaryDirectory() as directory:
            runs = Path(directory) / "runs.csv"
            traces = Path(directory) / "traces.csv"
            export_campaign_csv(self.connection, "instances", runs, traces)
            with runs.open(encoding="utf-8", newline="") as file:
                rows = list(csv.DictReader(file))
            with traces.open(encoding="utf-8", newline="") as file:
                points = list(csv.DictReader(file))
        self.assertEqual(len({row["instance_id"] for row in rows}), 2)
        self.assertEqual(
            {json.loads(row["problem_parameters_json"])["variant"] for row in rows},
            {1, 2},
        )
        self.assertEqual(
            {row["instance_id"] for row in rows},
            {point["instance_id"] for point in points},
        )

    def test_hash_provenance_requires_a_population_hash_and_recovery_clears_it(self):
        loaded = small_config("provenance")
        plan = CampaignPlanner(self.repository).persist(
            loaded.campaign, loaded.treatments
        )
        self.repository.start_campaign("provenance")
        run_id = plan.run_ids[0]
        self.repository.start_run(run_id)
        for version in ("", " ", 1, "array_f64le_shape_v1"):
            with self.subTest(version=version):
                with self.assertRaises(RepositoryError):
                    self.repository.complete_run(
                        run_id,
                        0.0,
                        [0.0, 0.0],
                        8,
                        0.01,
                        initial_state_hash_version=version,
                    )
        self.assertEqual(self.repository.run_status(run_id), "running")
        self.connection.execute(
            "UPDATE runs SET initial_population_sha256=?,initial_state_hash_version=? "
            "WHERE run_id=?",
            ("a" * 64, "array_f64le_shape_v1", run_id),
        )
        self.connection.commit()
        self.repository.recover_interrupted_run("provenance", run_id, "test recovery")
        row = self.connection.execute(
            "SELECT initial_population_sha256,initial_state_hash_version FROM runs "
            "WHERE run_id=?",
            (run_id,),
        ).fetchone()
        self.assertEqual(tuple(row), (None, None))

    def test_migration_preserves_existing_keys_labels_and_unknown_hash_provenance(self):
        with closing(sqlite3.connect(":memory:")) as connection:
            connection.row_factory = sqlite3.Row
            connection.execute(
                "CREATE TABLE schema_migrations(version INTEGER PRIMARY KEY,"
                "name TEXT NOT NULL UNIQUE,applied_at TEXT NOT NULL)"
            )
            for migration in discover_migrations()[:5]:
                connection.executescript(migration.path.read_text(encoding="utf-8"))
            connection.execute(
                "INSERT INTO campaigns(campaign_id,name,config_json,config_sha256,"
                "code_commit,metric_registry_version,schema_version,created_at) "
                "VALUES('old','Old','{}',?,'test',1,5,'test')",
                ("a" * 64,),
            )
            connection.execute(
                "INSERT INTO algorithm_configurations(configuration_id,campaign_id,"
                "algorithm,optimizer_version,parameters_json,parameters_sha256,"
                "budget_type,budget_evaluations,created_at) "
                "VALUES('old-label','old','GA','test','{}',?,'evaluations',8,'test')",
                ("b" * 64,),
            )
            connection.execute(
                "INSERT INTO problem_instances(problem_family,name,dimension) "
                "VALUES('test','same',2)"
            )
            connection.execute(
                "INSERT INTO runs(campaign_id,configuration_id,instance_id,replica_index,"
                "status,initial_population_sha256) VALUES('old','old-label',1,0,'planned',?)",
                ("c" * 64,),
            )
            connection.commit()
            self.assertEqual(apply_migrations(connection), (6, 7))
            row = connection.execute(
                "SELECT configuration_id,treatment_id FROM algorithm_configurations"
            ).fetchone()
            self.assertEqual(tuple(row), ("old-label", "old-label"))
            row = connection.execute(
                "SELECT configuration_id,initial_population_sha256,"
                "initial_state_hash_version,finalization_status,failure_phase FROM runs"
            ).fetchone()
            self.assertEqual(tuple(row), ("old-label", "c" * 64, None, None, None))
            self.assertEqual(
                connection.execute("PRAGMA foreign_key_check").fetchall(), []
            )


class TestInitialStateIdentity(unittest.TestCase):
    def test_same_population_has_same_versioned_hash_for_pso_and_ga(self):
        problem = CallableProblem(
            ProblemMetadata("sphere", "test", SearchSpace.uniform(2, -5.0, 5.0)),
            lambda candidate: sum(value * value for value in candidate),
        )
        pso = LegacyCompatiblePSO(
            problem=problem,
            config=LegacyPSORunConfig(4, 1),
            inertia_policy=FixedInertia(0.5),
            random_streams=ReplicaRandomStreams(42),
        ).run()
        ga = RealCodedGA(
            problem=problem,
            config=RealCodedGARunConfig(4, 1),
            random_streams=ReplicaRandomStreams(42),
        ).run()
        self.assertEqual(pso.initial_population_sha256, ga.initial_population_sha256)
        self.assertEqual(pso.initial_state_hash_version, ga.initial_state_hash_version)
        self.assertEqual(ga.initial_state_hash_version, "array_f64le_shape_v1")
        self.assertEqual(
            pso.initial_population_sha256,
            "d19fa74e6fb8ffc61343158baaedeb96f2c1c793ec2af4d03e5560e66f8f8bb4",
        )
        for result in (pso, ga):
            external_result = type(result)(
                **{
                    field.name: getattr(result, field.name)
                    for field in fields(result)
                    if field.name != "initial_state_hash_version"
                }
            )
            self.assertIsNone(external_result.initial_state_hash_version)

    def test_hash_canonicalizes_byte_order_layout_and_includes_shape(self):
        from afcs.core.hashing import array_sha256

        matrix = np.arange(6, dtype=float).reshape(2, 3)
        self.assertEqual(array_sha256(matrix), array_sha256(matrix.astype(">f8")))
        self.assertEqual(array_sha256(matrix), array_sha256(np.asfortranarray(matrix)))
        self.assertNotEqual(array_sha256(matrix), array_sha256(matrix.reshape(3, 2)))
        self.assertNotEqual(array_sha256(matrix), array_sha256(matrix + 1.0))
        expected = hashlib.sha256(
            b"(2, 3)<f8" + np.ascontiguousarray(matrix, dtype="<f8").tobytes()
        ).hexdigest()
        self.assertEqual(array_sha256(matrix), expected)
