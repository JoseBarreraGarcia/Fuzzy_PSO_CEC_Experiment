"""
Analysis Modules for CEC2017 Benchmarks

Structured analysis framework with 3-level hierarchy:
- Level 1: Raw data extraction from database
- Level 2: Aggregated statistics and visualizations
- Convergence Analysis: Detailed convergence plots
- Diversity Analysis: Detailed diversity plots
"""

from . import level1_raw_data_cec
from . import level2_aggregated_cec
from . import convergence_analysis_cec
from . import diversity_analysis_cec

__all__ = [
    'level1_raw_data_cec', 
    'level2_aggregated_cec',
    'convergence_analysis_cec',
    'diversity_analysis_cec'
]
