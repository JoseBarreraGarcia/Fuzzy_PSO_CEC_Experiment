#!/usr/bin/env python3
"""Test input plots generation"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fuzzy_plots import plot_fuzzy_input_diversity, plot_fuzzy_input_progress

print("Generating input plots...")
print("1. Diversity input...")
path1 = plot_fuzzy_input_diversity()
print(f"   ✅ {path1}")

print("2. Progress input...")
path2 = plot_fuzzy_input_progress()
print(f"   ✅ {path2}")

print("\n✅ Input plots generated successfully!")
