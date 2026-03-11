"""
Analysis modules for Scalable Fuzzy PSO System

Provides modular analysis at 3 hierarchical levels:
- Level 1: Raw data extraction (CSVs)
- Level 2: Aggregated statistics & plots
- Level 3: Disaggregated rankings (per-instance, per-config)

Plus legacy fuzzy-specific modules:
- Fuzzy set comparison
- Detailed iteration breakdown
- LNCS-formatted plots
"""

import sys
from pathlib import Path

# Add parent directory to path so submodules can import BD, Util, etc.
sys.path.insert(0, str(Path(__file__).parent.parent))

from . import compare_fuzzy_sets
from . import detailed_w_analysis
from . import level1_raw_data
from . import level2_aggregated
from . import level3_disaggregated

__all__ = [
    'compare_fuzzy_sets', 
    'detailed_w_analysis',
    'level1_raw_data',
    'level2_aggregated',
    'level3_disaggregated',
]
