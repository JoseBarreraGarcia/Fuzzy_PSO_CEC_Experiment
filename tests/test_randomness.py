import unittest
from concurrent.futures import ThreadPoolExecutor

import numpy as np

from afcs.core import RandomnessConfig, ReplicaRandomStreams


class TestPairedRandomness(unittest.TestCase):
    def test_replica_count_determines_sequential_seed_range(self):
        config = RandomnessConfig(base_seed=42)
        self.assertEqual(
            [config.seed_for_replica(index) for index in range(31)],
            list(range(42, 73)),
        )
        self.assertEqual(config.seed_for_replica(99), 141)

    def test_named_streams_are_reproducible_and_independent(self):
        streams = ReplicaRandomStreams(42)
        init_a = streams.generator("initialization").random(8)
        dynamics_a = streams.generator("dynamics").random(8)
        init_b = ReplicaRandomStreams(42).generator("initialization").random(8)
        dynamics_b = ReplicaRandomStreams(42).generator("dynamics").random(8)

        np.testing.assert_array_equal(init_a, init_b)
        np.testing.assert_array_equal(dynamics_a, dynamics_b)
        self.assertFalse(np.array_equal(init_a, dynamics_a))

    def test_optional_stream_consumption_does_not_shift_common_streams(self):
        streams = ReplicaRandomStreams(57)
        expected_init = streams.generator("initialization").random(5)
        expected_dynamics = streams.generator("dynamics").random(5)

        streams.generator("controller").random(10_000)
        streams.generator("problem").random(10_000)

        np.testing.assert_array_equal(
            streams.generator("initialization").random(5), expected_init
        )
        np.testing.assert_array_equal(
            streams.generator("dynamics").random(5), expected_dynamics
        )

    def test_order_and_worker_count_do_not_change_replica_streams(self):
        seeds = list(range(42, 73))

        def sample(seed: int) -> tuple[int, tuple[float, ...]]:
            values = ReplicaRandomStreams(seed).generator("dynamics").random(6)
            return seed, tuple(float(value) for value in values)

        sequential = dict(sample(seed) for seed in seeds)
        reversed_order = dict(sample(seed) for seed in reversed(seeds))
        with ThreadPoolExecutor(max_workers=4) as pool:
            parallel = dict(pool.map(sample, reversed(seeds)))

        self.assertEqual(sequential, reversed_order)
        self.assertEqual(sequential, parallel)


if __name__ == "__main__":
    unittest.main()
