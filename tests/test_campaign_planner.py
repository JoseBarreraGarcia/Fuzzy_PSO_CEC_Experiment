import tempfile
import unittest
from pathlib import Path

import numpy as np

from afcs.core import SearchSpace
from afcs.experiments import (
    CampaignDefinition,
    CampaignPlanner,
    TreatmentDefinition,
)
from afcs.metrics import load_metric_registry
from afcs.optimizers.pso import FixedInertia, LegacyCompatiblePSO, LegacyPSORunConfig
from afcs.persistence import ExperimentRepository, initialize_v2_database
from afcs.problems import CallableProblem, ProblemMetadata


class TestCampaignPlanner(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.connection = initialize_v2_database(
            Path(self.temp_dir.name) / "planner.db"
        )
        self.repository = ExperimentRepository(self.connection, load_metric_registry())
        self.planner = CampaignPlanner(self.repository)

    def tearDown(self):
        self.connection.close()
        self.temp_dir.cleanup()

    def test_compact_definition_expands_replicas_with_paired_seeds(self):
        treatments = (
            self._treatment("pso-fixed", dimension=2),
            self._treatment("pso-fixed", dimension=3),
        )
        result = self.planner.persist(self._campaign(replicas=3), treatments)

        self.assertEqual(
            result.configuration_ids,
            ('campaign_configuration_v1:["campaign","pso-fixed"]',),
        )
        self.assertEqual(len(result.instance_ids), 2)
        self.assertEqual(len(result.run_ids), 6)
        rows = self.connection.execute(
            "SELECT replica_index, random_seed FROM runs ORDER BY run_id"
        ).fetchall()
        self.assertEqual([row["replica_index"] for row in rows], [0, 1, 2, 0, 1, 2])
        self.assertEqual([row["random_seed"] for row in rows], [42, 43, 44, 42, 43, 44])

    def test_31_replicas_use_seeds_42_through_72_for_every_treatment(self):
        treatments = (
            self._treatment("pso-fixed-04", dimension=2, inertia=0.4),
            self._treatment("pso-fixed-08", dimension=2, inertia=0.8),
        )
        self.planner.persist(self._campaign(replicas=31), treatments)

        rows = self.connection.execute(
            """
            SELECT configuration_id, replica_index, random_seed
            FROM runs ORDER BY configuration_id, replica_index
            """
        ).fetchall()
        by_configuration = {}
        for row in rows:
            by_configuration.setdefault(row["configuration_id"], []).append(
                row["random_seed"]
            )
        self.assertEqual(
            set(by_configuration),
            {
                'campaign_configuration_v1:["campaign","pso-fixed-04"]',
                'campaign_configuration_v1:["campaign","pso-fixed-08"]',
            },
        )
        for seeds in by_configuration.values():
            self.assertEqual(seeds, list(range(42, 73)))

    def test_conflicting_configuration_is_rejected_before_database_writes(self):
        first = self._treatment("same-id", dimension=2, inertia=0.4)
        conflicting = self._treatment("same-id", dimension=3, inertia=0.8)

        with self.assertRaisesRegex(ValueError, "conflicting definitions"):
            self.planner.persist(self._campaign(), (first, conflicting))

        count = self.connection.execute("SELECT COUNT(*) FROM campaigns").fetchone()[0]
        self.assertEqual(count, 0)

    def test_persistence_failure_rolls_back_the_entire_campaign(self):
        campaign = CampaignDefinition(
            campaign_id="invalid-metrics",
            name="Invalid metrics",
            source_config={"metrics": "does-not-exist"},
            code_commit="abc123",
            replicas=2,
            metric_selection="does-not-exist",
        )
        with self.assertRaises(ValueError):
            self.planner.persist(campaign, (self._treatment("pso-fixed", 2),))

        count = self.connection.execute("SELECT COUNT(*) FROM campaigns").fetchone()[0]
        self.assertEqual(count, 0)

    def _campaign(self, replicas: int = 2) -> CampaignDefinition:
        return CampaignDefinition(
            campaign_id="campaign",
            name="Planner test",
            source_config={"replicas": replicas},
            code_commit="abc123",
            replicas=replicas,
        )

    @staticmethod
    def _treatment(
        configuration_id: str,
        dimension: int,
        inertia: float = 0.6,
    ) -> TreatmentDefinition:
        problem = CallableProblem(
            ProblemMetadata(
                problem_id="sphere",
                family="test",
                search_space=SearchSpace.uniform(dimension, -5.0, 5.0),
                known_optimum=0.0,
                parameters={"variant": "sphere"},
            ),
            lambda candidate: sum(value * value for value in candidate),
        )
        optimizer = LegacyCompatiblePSO(
            problem=problem,
            config=LegacyPSORunConfig(population_size=4, max_iterations=2),
            inertia_policy=FixedInertia(inertia),
            rng=np.random.default_rng(1),
        )
        return TreatmentDefinition(configuration_id, optimizer.run_metadata)


if __name__ == "__main__":
    unittest.main()
