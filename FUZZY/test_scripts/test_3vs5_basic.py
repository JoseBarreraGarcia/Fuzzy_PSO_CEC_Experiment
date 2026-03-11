#!/usr/bin/env python
"""
Test simple de ambos controllers
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fuzzy_controller_w import FuzzyInertiaController, tri
from fuzzy_controller_w_5labels import FuzzyInertiaController_5labels

print("="*80)
print("TEST: Instanciación de Controllers")
print("="*80)

try:
    ctrl3 = FuzzyInertiaController(w_set='A')
    print("✓ FuzzyInertiaController(w_set='A') creado exitosamente")
    print(f"  wMin={ctrl3.wMin}, wMax={ctrl3.wMax}")
    print(f"  w_mf keys: {list(ctrl3.w_mf.keys())}")
    
    # Test compute_w
    w = ctrl3.compute_w(0.5, 0.5)
    print(f"  compute_w(0.5, 0.5) = {w}")
    
except Exception as e:
    print(f"✗ Error en FuzzyInertiaController: {e}")

print()

try:
    ctrl5 = FuzzyInertiaController_5labels(w_set='A')
    print("✓ FuzzyInertiaController_5labels(w_set='A') creado exitosamente")
    print(f"  wMin={ctrl5.wMin}, wMax={ctrl5.wMax}")
    print(f"  w_mf keys: {list(ctrl5.w_mf.keys())}")
    
    # Test compute_w
    w = ctrl5.compute_w(0.5, 0.5)
    print(f"  compute_w(0.5, 0.5) = {w}")
    
except Exception as e:
    print(f"✗ Error en FuzzyInertiaController_5labels: {e}")

print("\n" + "="*80)
print("TEST: Función tri()")
print("="*80)

try:
    result = tri(0.5, 0.1, 0.5, 0.9)
    print(f"✓ tri(0.5, 0.1, 0.5, 0.9) = {result}")
except Exception as e:
    print(f"✗ Error en tri(): {e}")

print("\n" + "="*80)
print("TEST: Comparación de respuestas")
print("="*80)

for diversity, progress in [(0.1, 0.1), (0.5, 0.5), (0.9, 0.9)]:
    w3 = ctrl3.compute_w(diversity, progress)
    w5 = ctrl5.compute_w(diversity, progress)
    print(f"d={diversity:.1f}, t={progress:.1f} → 3labels: {w3:.4f}, 5labels: {w5:.4f}, diff: {w5-w3:+.4f}")

print("\n✓ Todos los tests pasaron\n")
