"""
Quick test of hierarchical analysis framework.
Tests data extraction without requiring actual experiments to be run.
"""

import sys
import os

# Test imports
try:
    from analysis_modules import level1_raw_data, level2_aggregated, level3_disaggregated
    print("[OK] All analysis modules imported successfully")
except ImportError as e:
    print(f"[ERROR] Failed to import modules: {e}")
    sys.exit(1)

# Test that directories can be created
try:
    level1_raw_data.ensure_directories()
    level2_aggregated.ensure_directories()
    level3_disaggregated.ensure_directories()
    print("[OK] All output directories created/verified")
except Exception as e:
    print(f"[ERROR] Failed to create directories: {e}")
    sys.exit(1)

# Test database connection (if any experiments exist)
try:
    from BD.sqlite import BD
    bd = BD()
    bd.conectar()
    
    # Check if we have any completed experiments
    bd.getCursor().execute("SELECT COUNT(*) FROM experimentos WHERE estado IN ('completado', 'completada')")
    count = bd.getCursor().fetchone()[0]
    bd.desconectar()
    
    if count == 0:
        print("[WARN] No completed experiments found in database")
        print("[INFO] Framework is ready; run experiments with main.py first")
    else:
        print(f"[OK] Database connection verified ({count} completed experiments)")
except Exception as e:
    print(f"[ERROR] Database connection failed: {e}")
    sys.exit(1)

print("\n" + "=" * 70)
print("[OK] Hierarchical analysis framework is ready!")
print("=" * 70)
print("\nTo run analysis on completed experiments:")
print("  python analisis.py")
print("\nOr run specific levels:")
print("  from analysis_modules import level1_raw_data")
print("  level1_raw_data.main(verbose=True)")
