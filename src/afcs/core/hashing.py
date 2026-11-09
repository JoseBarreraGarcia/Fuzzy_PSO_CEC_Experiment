"""Versioned canonical identity for optimizer population/state arrays."""

import hashlib

import numpy as np

INITIAL_STATE_HASH_VERSION = "array_f64le_shape_v1"


def array_sha256(values: np.ndarray) -> str:
    """Hash shape, little-endian float64 dtype and C-order bytes, in that order."""

    canonical = np.ascontiguousarray(values, dtype="<f8")
    payload = (
        str(canonical.shape).encode("ascii")
        + canonical.dtype.str.encode("ascii")
        + canonical.tobytes()
    )
    return hashlib.sha256(payload).hexdigest()
