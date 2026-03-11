"""
Master Script: Run All Paper Analysis Modules
Executes diversity, rule activation, and input space analyses

Run this after completing experiments with main.py

Author: Paper Analysis Pipeline
Date: January 2026
"""

import subprocess
import sys
from pathlib import Path

ANALYSIS_MODULES = [
    "analysis_modules/paper_diversity_analysis.py",
    "analysis_modules/paper_rule_activation_analysis.py",
    "analysis_modules/paper_input_space_analysis.py"
]

def run_module(module_path):
    """Run a single analysis module."""
    print("\n" + "=" * 70)
    print(f"RUNNING: {module_path}")
    print("=" * 70)
    
    result = subprocess.run(
        [sys.executable, module_path],
        capture_output=False,
        text=True
    )
    
    if result.returncode != 0:
        print(f"[WARN] Module failed with exit code {result.returncode}")
        return False
    
    return True

def main():
    """Run all analysis modules sequentially."""
    
    print("=" * 70)
    print("CONFERENCE PAPER ANALYSIS PIPELINE")
    print("=" * 70)
    print("\nThis script will generate:")
    print("  - 3 publication-ready figures (PDF + PNG)")
    print("  - 3 LaTeX tables ready for copy/paste")
    print("  - 3 CSV files with raw data")
    print("\n[INFO] Estimated time: 2-5 minutes")
    print("=" * 70)
    
    input("\nPress ENTER to start...\n")
    
    success_count = 0
    
    for module in ANALYSIS_MODULES:
        if not Path(module).exists():
            print(f"[ERROR] Module not found: {module}")
            continue
        
        if run_module(module):
            success_count += 1
        else:
            print(f"[WARN] Continuing despite error in {module}")
    
    print("\n" + "=" * 70)
    print("PIPELINE COMPLETE")
    print("=" * 70)
    print(f"\n[OK] Successfully completed: {success_count}/{len(ANALYSIS_MODULES)} modules")
    
    output_path = Path("Resultados/paper_outputs")
    if output_path.exists():
        files = list(output_path.glob("paper_*"))
        print(f"\n[DIR] Generated {len(files)} output files in:")
        print(f"   {output_path.absolute()}")
        
        print("\n[DATA] Figures for paper:")
        for f in sorted(output_path.glob("paper_fig_*.pdf")):
            print(f"   - {f.name}")
        
        print("\n[DATA] LaTeX tables for paper:")
        for f in sorted(output_path.glob("paper_table_*.tex")):
            print(f"   - {f.name}")
        
        print("\n[DATA] Raw data (optional):")
        for f in sorted(output_path.glob("paper_data_*.csv")):
            print(f"   - {f.name}")
    
    print("\n" + "=" * 70)
    print("NEXT STEPS:")
    print("=" * 70)
    print("1. Review figures in Resultados/paper_outputs/")
    print("2. Copy LaTeX tables into your conference paper")
    print("3. Use raw CSV data for additional statistical tests")
    print(f"\n[TARGET] Deadline: January 15, 2026 ({15-3} days remaining)")
    print("=" * 70)

if __name__ == "__main__":
    main()
