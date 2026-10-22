"""Experiment planning and execution orchestration."""

from .contracts import OptimizationRunResult, RunnableOptimizer
from .configuration import (
    CampaignSummary,
    ConfigurationError,
    ExecutionConfig,
    LoadedCampaignConfig,
    load_campaign_config,
    parse_campaign_config,
)
from .planning import (
    CampaignDefinition,
    CampaignPlanner,
    PersistedCampaignPlan,
    TreatmentDefinition,
)
from afcs.core import (
    NUMPY_RNG_ENGINE,
    PAIRED_SEED_PROTOCOL,
    RandomnessConfig,
    ReplicaRandomStreams,
)
from .runner import ExperimentRunExecutor, RunBindingError

__all__ = [
    "CampaignDefinition",
    "CampaignPlanner",
    "CampaignSummary",
    "ConfigurationError",
    "ExecutionConfig",
    "ExperimentRunExecutor",
    "OptimizationRunResult",
    "LoadedCampaignConfig",
    "PersistedCampaignPlan",
    "NUMPY_RNG_ENGINE",
    "PAIRED_SEED_PROTOCOL",
    "RandomnessConfig",
    "ReplicaRandomStreams",
    "RunBindingError",
    "RunnableOptimizer",
    "TreatmentDefinition",
    "load_campaign_config",
    "parse_campaign_config",
]
