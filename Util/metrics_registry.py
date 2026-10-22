"""Compatibility bridge for the metric registry moved to :mod:`afcs.metrics`.

New code must import from `afcs.metrics`. This module contains no independent
implementation and may be removed after all external consumers have migrated.
"""

from afcs.metrics import (
    DEFAULT_REGISTRY_PATH,
    MetricDefinition,
    MetricRegistry,
    MetricRegistryError,
    load_metric_registry,
    parse_metric_registry,
)

__all__ = [
    "DEFAULT_REGISTRY_PATH",
    "MetricDefinition",
    "MetricRegistry",
    "MetricRegistryError",
    "load_metric_registry",
    "parse_metric_registry",
]

