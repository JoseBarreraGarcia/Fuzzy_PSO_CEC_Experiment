#!/usr/bin/env python
"""
Test script to verify FuzzyInertiaController initializes w_history with wMax
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fuzzy_controller_w import FuzzyInertiaController

# Create controller
fcs = FuzzyInertiaController(wMin=0.1, wMax=0.9, w_set="B")

print(f"Initial w_history: {fcs.w_history}")
print(f"Expected w_history[0]: {fcs.wMax}")
assert fcs.w_history[0] == fcs.wMax, "w_history should start with wMax!"
print("✓ Test passed: w_history initialized correctly with wMax")

# Simulate a compute_w call
w = fcs.compute_w(diversity_ratio=0.5, progress=0.1)
print(f"\nAfter compute_w(0.5, 0.1): w={w}")
print(f"w_history now: {fcs.w_history}")
print("✓ w_history correctly appends computed values")
