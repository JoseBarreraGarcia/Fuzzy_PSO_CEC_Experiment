#!/usr/bin/env python3
"""
Integration test for fuzzy plots generation in analisis.py
"""

import sys
import os

# Add workspace to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_imports():
    """Test that all necessary modules can be imported."""
    print("[TEST] Testing imports...")
    try:
        from fuzzy_plots import generate_all_fuzzy_plots
        print("  [OK] fuzzy_plots imported")
        return True
    except Exception as e:
        print(f"  [FAIL] Import failed: {e}")
        return False

def test_fuzzy_plots():
    """Test that fuzzy plots can be generated."""
    print("\n[TEST] Testing fuzzy plots generation...")
    try:
        from fuzzy_plots import generate_all_fuzzy_plots
        plots = generate_all_fuzzy_plots(verbose=False)
        
        if len(plots) != 8:
            print(f"  [WARN] Expected 8 plots, got {len(plots)}")
            return False
        
        # Check that files exist
        for plot_path in plots:
            if not os.path.exists(plot_path):
                print(f"  [FAIL] Plot file not found: {plot_path}")
                return False
        
        print(f"  [OK] Generated {len(plots)} fuzzy set plots")
        return True
    except Exception as e:
        print(f"  [FAIL] Fuzzy plots generation failed: {e}")
        return False

def test_analisis_imports():
    """Test that analisis.py can be imported."""
    print("\n[TEST] Testing analisis.py imports...")
    try:
        import analisis
        print("  [OK] analisis module imported")
        return True
    except Exception as e:
        print(f"  [FAIL] analisis import failed: {e}")
        return False

def main():
    """Run all integration tests."""
    print("=" * 70)
    print("FUZZY PLOTS INTEGRATION TEST")
    print("=" * 70)
    
    results = []
    
    results.append(("Imports", test_imports()))
    results.append(("Fuzzy Plots", test_fuzzy_plots()))
    results.append(("Analisis Module", test_analisis_imports()))
    
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    
    for test_name, passed in results:
        status = "[PASS]" if passed else "[FAIL]"
        print(f"  {test_name:<30} {status}")
    
    all_passed = all(passed for _, passed in results)
    
    print("\n" + "=" * 70)
    if all_passed:
        print("[SUCCESS] All integration tests passed!")
        print("\nTo run the full analysis:")
        print("  python analisis.py")
        print("\nFuzzy plots will be saved in:")
        print("  FUZZY/plots/")
        return 0
    else:
        print("[FAILURE] Some tests failed. Check output above.")
        return 1

if __name__ == '__main__':
    sys.exit(main())
