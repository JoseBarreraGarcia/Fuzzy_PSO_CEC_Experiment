"""Versioned common-random-number protocol for paired replicas."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


PAIRED_SEED_PROTOCOL = "paired_by_replica_v1"
NUMPY_RNG_ENGINE = "numpy_seedsequence_pcg64_v1"
_STREAM_IDS = {
    "initialization": 0,
    "dynamics": 1,
    "controller": 2,
}


@dataclass(frozen=True, slots=True)
class RandomnessConfig:
    """Campaign-level seed contract shared by all comparable treatments."""

    base_seed: int = 42
    protocol: str = PAIRED_SEED_PROTOCOL
    engine: str = NUMPY_RNG_ENGINE

    def __post_init__(self) -> None:
        if isinstance(self.base_seed, bool) or not isinstance(self.base_seed, int):
            raise TypeError("base_seed must be an integer")
        if self.base_seed < 0:
            raise ValueError("base_seed must be non-negative")
        if self.protocol != PAIRED_SEED_PROTOCOL:
            raise ValueError(f"Unsupported seed protocol: {self.protocol!r}")
        if self.engine != NUMPY_RNG_ENGINE:
            raise ValueError(f"Unsupported RNG engine: {self.engine!r}")

    def seed_for_replica(self, replica_index: int) -> int:
        if isinstance(replica_index, bool) or not isinstance(replica_index, int):
            raise TypeError("replica_index must be an integer")
        if replica_index < 0:
            raise ValueError("replica_index must be non-negative")
        return self.base_seed + replica_index


@dataclass(frozen=True, slots=True)
class ReplicaRandomStreams:
    """Create deterministic named NumPy substreams from one replica seed."""

    replica_seed: int
    engine: str = NUMPY_RNG_ENGINE

    def __post_init__(self) -> None:
        if isinstance(self.replica_seed, bool) or not isinstance(
            self.replica_seed, int
        ):
            raise TypeError("replica_seed must be an integer")
        if self.replica_seed < 0:
            raise ValueError("replica_seed must be non-negative")
        if self.engine != NUMPY_RNG_ENGINE:
            raise ValueError(f"Unsupported RNG engine: {self.engine!r}")

    def generator(self, stream: str) -> np.random.Generator:
        try:
            stream_id = _STREAM_IDS[stream]
        except KeyError as error:
            raise ValueError(f"Unknown random stream: {stream!r}") from error
        sequence = np.random.SeedSequence(
            entropy=self.replica_seed,
            spawn_key=(stream_id,),
        )
        return np.random.default_rng(sequence)
