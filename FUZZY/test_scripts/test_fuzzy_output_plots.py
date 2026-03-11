#!/usr/bin/env python
"""Test plot_fuzzy_output_w_set for both 3 and 5 labels"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fuzzy_plots import plot_fuzzy_output_w_set

print("\n" + "="*80)
print("TEST: plot_fuzzy_output_w_set() generates both 3 and 5 label plots")
print("="*80 + "\n")

for w_set in ['A', 'B']:
    print(f"\nGenerating plots for Set {w_set}...")
    result = plot_fuzzy_output_w_set(w_set)
    
    print(f"  Result type: {type(result)}")
    
    if isinstance(result, dict):
        print(f"  3-labels: {result.get('3labels')}")
        print(f"  5-labels: {result.get('5labels')}")
        
        # Verify files exist
        if result.get('3labels'):
            exists_3 = os.path.exists(result['3labels'])
            print(f"    → File exists: {exists_3}")
        
        if result.get('5labels'):
            exists_5 = os.path.exists(result['5labels'])
            print(f"    → File exists: {exists_5}")
    else:
        print(f"  Unexpected result type: {result}")

print("\n" + "="*80)
print("TEST COMPLETED")
print("="*80 + "\n")

# List all fuzzy_output files
fuzzy_plots_dir = "FUZZY/plots"
if os.path.exists(fuzzy_plots_dir):
    output_files = [f for f in os.listdir(fuzzy_plots_dir) if f.startswith('03_fuzzy_output')]
    print(f"\nFuzzy output files in {fuzzy_plots_dir}:")
    for f in sorted(output_files):
        print(f"  - {f}")
else:
    print(f"\nDirectory {fuzzy_plots_dir} does not exist")
