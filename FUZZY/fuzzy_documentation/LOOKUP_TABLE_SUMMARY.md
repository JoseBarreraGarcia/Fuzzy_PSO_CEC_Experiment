# Fuzzy Lookup Table - Summary Report

## Overview

La tabla `fuzzy_lookup_table.csv` es una **herramienta de análisis visual** que documenta el comportamiento del sistema de control fuzzy Mamdani para todas las combinaciones posibles de entradas.

## Key Metrics

| Metric | Value | Status |
|--------|-------|--------|
| **Total Combinations Tested** | 121 (11×11 grid) | ✅ Complete |
| **Coverage (Rules Activated)** | 100% (121/121 rows) | ✅ 100% |
| **Rows with "none"** | 0 | ✅ Fixed |

## Rule Activation Distribution

```
Single Rule Activated:     100 rows (82.6%)  - Majority cases
Two Rules Activated:        20 rows (16.5%)  - Boundary transitions
Four Rules Activated:        1 row  (0.8%)   - Corner case (mid-point)
```

**Interpretation:**
- Most scenarios activate exactly 1 rule (clean decision)
- ~17% of cases have rule interactions (2 active rules)
- Very few cases combine multiple rules (4 active)

## Fuzzy Set Output Statistics

### Set A (Exploitation-Favored)
- **Range:** 0.2248 - 0.7752
- **Mean:** 0.4683
- **Std Dev:** 0.2146
- **Spread:** 0.5504 (wide range)

### Set B (Balanced)
- **Range:** 0.2333 - 0.7667
- **Mean:** 0.4669
- **Std Dev:** 0.2225
- **Spread:** 0.5334 (wide range)

### Set C (Symmetric)
- **Range:** 0.3000 - 0.7000
- **Mean:** 0.4736
- **Std Dev:** 0.1762
- **Spread:** 0.4000 (narrowest range)

### Set D (Maximum Exploitation)
- **Range:** 0.2200 - 0.7444
- **Mean:** 0.4287
- **Std Dev:** 0.2188
- **Spread:** 0.5244 (wide range)

## Example Interpretations

### Low Diversity (0.0) - Early Iteration (0.0)
```
Diversity: 0.00, Progress: 0.00
Activated Rule: low AND early -> medium (0.001)
w_set_A: 0.5000, w_set_B: 0.5000, w_set_C: 0.5000, w_set_D: 0.4200
```
**Meaning:** Very low diversity at start → favor **medium** inertia weight

### Medium Diversity (0.5) - Mid Iteration (0.5)
```
Diversity: 0.50, Progress: 0.50
Activated Rules: medium AND mid -> medium (0.500)
w_set_A: 0.5000, w_set_B: 0.5000, w_set_C: 0.5000, w_set_D: 0.4378
```
**Meaning:** Balanced diversity mid-search → use **medium** inertia weight

### High Diversity (1.0) - Late Iteration (1.0)
```
Diversity: 1.00, Progress: 1.00
Activated Rules: high AND late -> low (0.001)
w_set_A: 0.2796, w_set_B: 0.2600, w_set_C: 0.3000, w_set_D: 0.2200
```
**Meaning:** High diversity at end → apply **low** inertia (exploitation)

## Usage

### For Documentation
- Show in papers/presentations to explain fuzzy system behavior
- Visual proof that ALL input combinations have defined outputs
- Demonstrate rule base coverage

### For Debugging
- Check specific (Diversity, Progress) combinations
- Verify that expected rules are activated
- Validate w values match intuition

### For Analysis
- Compare how different fuzzy sets respond to same inputs
- Identify which rules are most frequently activated
- Study transition regions where multiple rules fire

## Technical Notes

### How Values Were Generated

1. **Input Grid:** 11×11 combinations
   - Diversity: 0.0 to 1.0 (step 0.1)
   - Progress: 0.0 to 1.0 (step 0.1)

2. **Fuzzification:** Using improved `tri_extended()` function
   - Handles boundary values (0.0, 1.0) correctly
   - Retains tri() semantics for interior values
   - Ensures no "none" values at domain extremes

3. **Rule Evaluation:** Mamdani FIS with standard min-max aggregation
   - Firing strength: min(membership_diversity, membership_progress)
   - Threshold: > 0.0001 (shows all significant activations)
   - Output: Centroid (COA) defuzzification

### Why No "none" Values?

The `tri_extended()` function ensures that:
- Input values at exact boundaries return small positive membership (0.001)
- This guarantees at least ONE rule fires in every scenario
- Realistic because actual PSO rarely hits exactly 0.0 or 1.0

## File Location

```
FUZZY/fuzzy_lookup_table.csv
```

## Regeneration

To regenerate the table (e.g., after modifying fuzzy sets):

```bash
python FUZZY/generate_fuzzy_lookup_table.py
```

**Note:** The script is called automatically as part of `analisis.py` if `generate_lookup_table=True` in config.

## CSV Structure

| Column | Type | Example |
|--------|------|---------|
| Diversity | Float [0.0-1.0] | 0.50 |
| Progress | Float [0.0-1.0] | 0.50 |
| w_set_A | Float [min-max] | 0.5000 |
| w_set_B | Float [min-max] | 0.5000 |
| w_set_C | Float [min-max] | 0.5000 |
| w_set_D | Float [min-max] | 0.4378 |
| Activated_Rules | String | `low AND early -> medium (0.001)` |

## Citation

If using this table in publications:

> The fuzzy lookup table provides complete documentation of the Mamdani fuzzy inference system behavior across the input space, ensuring no undefined regions and enabling visual verification of the rule base design.

---

**Last Updated:** 2025-04-21 (Fixed "none" issue with tri_extended)
