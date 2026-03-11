"""
ORCHESTRATOR FOR CEC2017 ANALYSIS (LEVEL 1 + LEVEL 2)

Executes the complete pipeline:
1. Level 1: Extracts raw CSVs from the DB
2. Level 2: Generates aggregated plots based on CSVs
"""

import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

# Importar módulos
from analysis_modules_cec import (
    level1_raw_data_cec, 
    level2_aggregated_cec,
    convergence_analysis_cec,
    diversity_analysis_cec
)


def main():
    """Execute complete CEC2017 analysis."""
    
    start_time = time.time()
    
    print("\n" + "=" * 80)
    print("ANALYSIS PIPELINE FOR CEC2017 BENCHMARKS")
    print("=" * 80 + "\n")
    
    # LEVEL 1: Extract raw data
    print("[STEP 1/4] Executing Level 1 (Raw Data Extraction)...\n")
    try:
        level1_raw_data_cec.main()
    except Exception as e:
        print(f"[ERROR] Level 1 failed: {e}")
        return
    
    # LEVEL 2: Generate aggregated plots
    print("\n[STEP 2/4] Executing Level 2 (Aggregated Statistics & Plots)...\n")
    try:
        level2_aggregated_cec.main()
    except Exception as e:
        print(f"[ERROR] Level 2 failed: {e}")
        return
    
    # CONVERGENCE ANALYSIS
    print("\n[STEP 3/4] Executing Convergence Analysis...\n")
    try:
        convergence_analysis_cec.main()
    except Exception as e:
        print(f"[ERROR] Convergence Analysis failed: {e}")
        # Continue without failing
    
    # DIVERSITY ANALYSIS
    print("\n[STEP 4/4] Executing Diversity Analysis...\n")
    try:
        diversity_analysis_cec.main()
    except Exception as e:
        print(f"[ERROR] Diversity Analysis failed: {e}")
        # Continue without failing
    
    # Summary
    elapsed_time = time.time() - start_time
    
    print("\n" + "=" * 80)
    print("EXECUTION SUMMARY")
    print("=" * 80)
    print(f"\nTotal time: {elapsed_time:.2f} seconds")
    print("\nGenerated outputs:")
    print("  > Resultados/resumen/level1_raw_cec/")
    print("    - ben_experiments_all_runs.csv")
    print("    - ben_best_per_config.csv")
    print("    - ben_convergence_data.csv")
    print("    - ben_diversity_metrics.csv")
    print("    - ben_mh_comparison.csv")
    print("\n  > Resultados/resumen/level2_aggregated_cec/")
    print("    - convergence/")
    print("      ✓ convergence_by_function.png")
    print("      ✓ convergence_overlay_all_functions.png")
    print("      ✓ convergence_improvement_rate.png")
    print("      ✓ convergence_mean_std_bands.png")
    print("    - diversity/")
    print("      ✓ diversity_evolution_by_function.png")
    print("      ✓ diversity_overlay_all_functions.png")
    print("      ✓ diversity_vs_fitness_scatter.png")
    print("      ✓ diversity_distribution_boxplot.png")
    print("      ✓ diversity_timeline_all_mh.png")
    print("    - comparison/")
    print("\n[OK] ANALYSIS COMPLETED\n")


if __name__ == '__main__':
    main()
