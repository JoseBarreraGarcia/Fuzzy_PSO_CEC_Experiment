"""Strict JSON values and immutable, independent metadata snapshots."""

from __future__ import annotations

import math
from collections.abc import Mapping
from types import MappingProxyType
from typing import Any


def _json_value(value: Any, *, immutable: bool, active: set[int]) -> Any:
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("JSON numbers must be finite")
        return value
    if not isinstance(value, (Mapping, list, tuple)):
        raise TypeError(f"Unsupported JSON value type: {type(value).__name__}")
    identity = id(value)
    if identity in active:
        raise ValueError("JSON values must not contain circular references")
    active.add(identity)
    try:
        if isinstance(value, Mapping):
            if any(not isinstance(key, str) for key in value):
                raise TypeError("JSON object keys must be strings")
            result = {
                key: _json_value(item, immutable=immutable, active=active)
                for key, item in value.items()
            }
            return MappingProxyType(result) if immutable else result
        items = [
            _json_value(item, immutable=immutable, active=active) for item in value
        ]
        return tuple(items) if immutable else items
    finally:
        active.remove(identity)


def json_value(value: Any) -> Any:
    """Return a detached JSON-compatible value, rejecting lossy/invalid inputs."""

    return _json_value(value, immutable=False, active=set())


def freeze_json(value: Any) -> Any:
    """Return a detached JSON snapshot with read-only mappings and tuples."""

    return _json_value(value, immutable=True, active=set())


def freeze_json_mapping(value: Mapping[str, Any]) -> Mapping[str, Any]:
    """Copy JSON metadata recursively into read-only mappings and tuples."""

    if not isinstance(value, Mapping):
        raise TypeError("JSON metadata must be a mapping")
    return freeze_json(value)
