"""Load, validate and resolve the v2 metric registry without side effects."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Iterable, Mapping


DEFAULT_REGISTRY_PATH = (
    Path(__file__).resolve().parents[1] / "config" / "metrics_registry.json"
)

REQUIRED_DEFINITION_FIELDS = frozenset(
    {
        "version",
        "name",
        "description",
        "scope",
        "source",
        "dtype",
        "unit",
        "direction",
        "valid_range",
        "sampling",
        "aggregation",
        "missing_policy",
    }
)


class MetricRegistryError(ValueError):
    """Raised when a registry or metric selection violates the contract."""


@dataclass(frozen=True)
class MetricDefinition:
    metric_id: str
    version: int
    name: str
    description: str
    scope: tuple[str, ...]
    source: str
    dtype: str
    unit: str
    direction: str
    valid_range: str
    sampling: str
    aggregation: str
    missing_policy: str


@dataclass(frozen=True)
class MetricRegistry:
    schema_version: int
    required_metrics: tuple[str, ...]
    profiles: Mapping[str, tuple[str, ...]]
    metrics: Mapping[str, MetricDefinition]

    def resolve(self, selection: Any = "minimal") -> tuple[str, ...]:
        """Resolve a profile, ``all``, an explicit list, or a selection object.

        Required metrics are always included and cannot be excluded. Returned
        identifiers follow registry order to keep schemas deterministic.
        """

        selected = set(self.required_metrics)

        if isinstance(selection, str):
            if selection == "all":
                selected.update(self.metrics)
            elif selection in self.profiles:
                selected.update(self.profiles[selection])
            else:
                raise MetricRegistryError(f"Unknown metric profile: {selection!r}")
        elif isinstance(selection, (list, tuple, set, frozenset)):
            selected.update(self._validate_metric_ids(selection, "selection"))
        elif isinstance(selection, Mapping):
            unknown_keys = set(selection) - {"profile", "include", "exclude"}
            if unknown_keys:
                raise MetricRegistryError(
                    f"Unknown metric selection keys: {sorted(unknown_keys)}"
                )

            profile = selection.get("profile", "minimal")
            if profile == "all":
                selected.update(self.metrics)
            elif profile in self.profiles:
                selected.update(self.profiles[profile])
            else:
                raise MetricRegistryError(f"Unknown metric profile: {profile!r}")

            selected.update(
                self._validate_metric_ids(selection.get("include", ()), "include")
            )
            excluded = set(
                self._validate_metric_ids(selection.get("exclude", ()), "exclude")
            )
            forbidden = excluded.intersection(self.required_metrics)
            if forbidden:
                raise MetricRegistryError(
                    "Required metrics cannot be excluded: "
                    + ", ".join(sorted(forbidden))
                )
            selected.difference_update(excluded)
        else:
            raise MetricRegistryError(
                "Metric selection must be a profile name, 'all', a list, or an object"
            )

        return tuple(metric_id for metric_id in self.metrics if metric_id in selected)

    def _validate_metric_ids(
        self, metric_ids: Iterable[str], field_name: str
    ) -> tuple[str, ...]:
        if isinstance(metric_ids, (str, bytes)):
            raise MetricRegistryError(f"{field_name} must be a list of metric IDs")
        values = tuple(metric_ids)
        unknown = set(values) - set(self.metrics)
        if unknown:
            raise MetricRegistryError(
                f"Unknown metric IDs in {field_name}: {sorted(unknown)}"
            )
        return values


def load_metric_registry(path: str | Path = DEFAULT_REGISTRY_PATH) -> MetricRegistry:
    registry_path = Path(path)
    with registry_path.open("r", encoding="utf-8") as registry_file:
        raw = json.load(registry_file)
    return parse_metric_registry(raw)


def parse_metric_registry(raw: Mapping[str, Any]) -> MetricRegistry:
    expected_top_level = {"schema_version", "required_metrics", "profiles", "metrics"}
    missing = expected_top_level - set(raw)
    extra = set(raw) - expected_top_level
    if missing or extra:
        raise MetricRegistryError(
            f"Invalid registry keys; missing={sorted(missing)}, extra={sorted(extra)}"
        )

    schema_version = raw["schema_version"]
    if not isinstance(schema_version, int) or schema_version < 1:
        raise MetricRegistryError("schema_version must be a positive integer")

    raw_metrics = raw["metrics"]
    if not isinstance(raw_metrics, Mapping) or not raw_metrics:
        raise MetricRegistryError("metrics must be a non-empty object")

    definitions: dict[str, MetricDefinition] = {}
    for metric_id, definition in raw_metrics.items():
        if not isinstance(metric_id, str) or not metric_id:
            raise MetricRegistryError("Every metric ID must be a non-empty string")
        if not isinstance(definition, Mapping):
            raise MetricRegistryError(f"Metric {metric_id!r} must be an object")
        missing_fields = REQUIRED_DEFINITION_FIELDS - set(definition)
        extra_fields = set(definition) - REQUIRED_DEFINITION_FIELDS
        if missing_fields or extra_fields:
            raise MetricRegistryError(
                f"Invalid fields for {metric_id!r}; "
                f"missing={sorted(missing_fields)}, extra={sorted(extra_fields)}"
            )
        if not isinstance(definition["version"], int) or definition["version"] < 1:
            raise MetricRegistryError(f"Metric {metric_id!r} has invalid version")
        scope = definition["scope"]
        if not isinstance(scope, list) or not scope or not all(
            isinstance(value, str) and value for value in scope
        ):
            raise MetricRegistryError(f"Metric {metric_id!r} has invalid scope")

        definitions[metric_id] = MetricDefinition(
            metric_id=metric_id,
            scope=tuple(scope),
            **{key: definition[key] for key in REQUIRED_DEFINITION_FIELDS - {"scope"}},
        )

    required_metrics = _validate_registry_metric_list(
        raw["required_metrics"], definitions, "required_metrics"
    )

    raw_profiles = raw["profiles"]
    if not isinstance(raw_profiles, Mapping) or "minimal" not in raw_profiles:
        raise MetricRegistryError("profiles must be an object containing 'minimal'")
    profiles = {
        name: _validate_registry_metric_list(values, definitions, f"profile {name!r}")
        for name, values in raw_profiles.items()
    }

    return MetricRegistry(
        schema_version=schema_version,
        required_metrics=required_metrics,
        profiles=profiles,
        metrics=definitions,
    )


def _validate_registry_metric_list(
    values: Any, definitions: Mapping[str, MetricDefinition], field_name: str
) -> tuple[str, ...]:
    if not isinstance(values, list) or not all(isinstance(value, str) for value in values):
        raise MetricRegistryError(f"{field_name} must be a list of metric IDs")
    if len(values) != len(set(values)):
        raise MetricRegistryError(f"{field_name} contains duplicate metric IDs")
    unknown = set(values) - set(definitions)
    if unknown:
        raise MetricRegistryError(f"Unknown metric IDs in {field_name}: {sorted(unknown)}")
    return tuple(values)
