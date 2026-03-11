#!/usr/bin/env python3
"""
Verify the rule content in both 3-label and 5-label controllers
"""

import sys
import os

sys.path.insert(0, os.getcwd())

from FUZZY.fuzzy_controller_w import FuzzyInertiaController
from FUZZY.fuzzy_controller_w_5labels import FuzzyInertiaController_5labels

def main():
    print("\n" + "="*80)
    print("RULES COMPARISON: 3-Labels vs 5-Labels")
    print("="*80)
    
    # 3-Label controller
    print("\n[3-LABEL CONTROLLER] Rules for Set A:")
    print("-" * 50)
    controller3 = FuzzyInertiaController('A')
    
    print("\n  Diversity → Progress → Output w")
    for diversity in ['low', 'medium', 'high']:
        for progress in ['early', 'mid', 'late']:
            output = controller3.rules.get((diversity, progress), 'unknown')
            print(f"  {diversity:8s} → {progress:8s} → {output}")
    
    # 5-Label controller
    print("\n[5-LABEL CONTROLLER] Rules for Set A:")
    print("-" * 50)
    controller5 = FuzzyInertiaController_5labels('A')
    
    print("\n  Diversity → Progress → Output w")
    for diversity in ['low', 'medium', 'high']:
        for progress in ['early', 'mid', 'late']:
            output = controller5.rules.get((diversity, progress), 'unknown')
            print(f"  {diversity:8s} → {progress:8s} → {output}")
    
    # Highlight differences
    print("\n" + "="*80)
    print("KEY DIFFERENCE DETECTED:")
    print("="*80)
    rule_3_low_early = controller3.rules.get(('low', 'early'))
    rule_5_low_early = controller5.rules.get(('low', 'early'))
    print(f"\n  ('low', 'early') rule:")
    print(f"    3-labels: {rule_3_low_early}")
    print(f"    5-labels: {rule_5_low_early}")

if __name__ == '__main__':
    main()
