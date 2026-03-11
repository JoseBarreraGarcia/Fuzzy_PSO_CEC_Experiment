#!/usr/bin/env python3
"""
Test that plot_fuzzy_rules_heatmap() generates BOTH 3-label and 5-label variants
"""

import os
import sys

# Add path to FUZZY/
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fuzzy_plots import plot_fuzzy_rules_heatmap

def main():
    print("\n" + "="*80)
    print("TEST: plot_fuzzy_rules_heatmap() generates both 3 and 5 label variants")
    print("="*80)
    
    # Generate heatmaps
    result = plot_fuzzy_rules_heatmap()
    
    print(f"\nResult type: {type(result)}")
    
    if isinstance(result, dict):
        print(f"\n✅ Returned dictionary with keys:")
        for label_type, path in result.items():
            print(f"  {label_type}: {path}")
            exists = os.path.exists(path)
            print(f"    → File exists: {exists}")
    else:
        print(f"\n❌ Expected dict, got: {result}")
        return
    
    # List all fuzzy heatmap files
    print(f"\nFuzzy heatmap files in FUZZY/plots:")
    heatmap_files = [f for f in os.listdir('./FUZZY/plots') if 'heatmap' in f]
    for f in sorted(heatmap_files):
        full_path = os.path.join('./FUZZY/plots', f)
        print(f"  - {f}")

if __name__ == '__main__':
    main()
