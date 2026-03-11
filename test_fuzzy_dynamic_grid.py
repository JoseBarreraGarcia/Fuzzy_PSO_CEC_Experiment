#!/usr/bin/env python3
"""
Test script para demostrar la adaptabilidad dinámica del grid de fuzzy plots.
Muestra cómo el sistema se ajusta automáticamente al número de sets disponibles.
"""

import sys
import os

# Add FUZZY to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'FUZZY'))

from fuzzy_plots import _get_available_w_sets, _calculate_grid_dims
from fuzzy_controller_w import FuzzyInertiaController

def test_dynamic_grid():
    """Test the dynamic grid calculation."""
    
    print("=" * 70)
    print("FUZZY DYNAMIC GRID ADAPTATION TEST")
    print("=" * 70)
    
    # Step 1: Get available w_sets
    print("\n[1] Detecting available w_sets from FuzzyInertiaController...")
    available_sets = _get_available_w_sets(FuzzyInertiaController)
    print(f"    ✓ Found {len(available_sets)} available set(s): {available_sets}")
    
    # Step 2: Calculate grid dimensions
    print(f"\n[2] Calculating optimal grid for {len(available_sets)} set(s)...")
    rows, cols, figsize = _calculate_grid_dims(len(available_sets))
    print(f"    ✓ Optimal grid: {rows} row(s) × {cols} col(s)")
    print(f"    ✓ Figure size: {figsize}")
    
    # Step 3: Show what would happen with different counts
    print("\n[3] Grid adaptation scenarios:")
    print("-" * 70)
    
    test_cases = [1, 2, 3, 4, 5, 6, 7, 8, 9]
    
    for num_sets in test_cases:
        rows, cols, figsize = _calculate_grid_dims(num_sets)
        efficiency = (num_sets / (rows * cols)) * 100
        print(f"   {num_sets} set(s) → {rows}×{cols} grid  (figsize={figsize})  "
              f"[{efficiency:.0f}% efficiency]")
    
    # Step 4: Actual test with current configuration
    print("\n[4] Testing with current configuration...")
    print("-" * 70)
    
    try:
        from fuzzy_plots import plot_all_w_sets_comparison
        result = plot_all_w_sets_comparison()
        
        print(f"   ✓ 3-label version: {result.get('3labels', 'NOT GENERATED')}")
        print(f"   ✓ 5-label version: {result.get('5labels', 'NOT GENERATED')}")
        
        # Check file sizes
        for version, path in result.items():
            if os.path.exists(path):
                size_kb = os.path.getsize(path) / 1024
                print(f"     → {version}: {size_kb:.1f} KB")
            else:
                print(f"     → {version}: FILE NOT FOUND")
    
    except Exception as e:
        print(f"   ✗ Error generating plots: {e}")
    
    print("\n" + "=" * 70)
    print("TEST COMPLETED")
    print("=" * 70)


if __name__ == "__main__":
    test_dynamic_grid()
