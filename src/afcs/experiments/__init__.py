"""Experiment planning and execution orchestration."""

from .contracts import OptimizationRunResult, RunnableOptimizer
from .configuration import (
    CampaignSummary,
    ConfigurationError,
    ExecutionConfig,
    LoadedCampaignConfig,
    TraceConfig,
    load_campaign_config,
    parse_campaign_config,
)
from .factory import OptimizerFactory
from .orchestration import (
    CampaignExecutionSummary,
    CampaignRecoveryRequired,
    SequentialCampaignOrchestrator,
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
    "CampaignExecutionSummary",
    "CampaignPlanner",
    "CampaignRecoveryRequired",
    "CampaignSummary",
    "ConfigurationError",
    "ExecutionConfig",
    "ExperimentRunExecutor",
    "OptimizationRunResult",
    "OptimizerFactory",
    "LoadedCampaignConfig",
    "PersistedCampaignPlan",
    "NUMPY_RNG_ENGINE",
    "PAIRED_SEED_PROTOCOL",
    "RandomnessConfig",
    "ReplicaRandomStreams",
    "RunBindingError",
    "RunnableOptimizer",
    "SequentialCampaignOrchestrator",
    "TreatmentDefinition",
    "TraceConfig",
    "load_campaign_config",
    "parse_campaign_config",
]
