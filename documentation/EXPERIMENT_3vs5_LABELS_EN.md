# Experiment: 3 vs. 5 Linguistic Labels in Fuzzy PSO

## Objective

Compare PSO_FCS performance with **3 linguistic labels** (original) vs. **5 linguistic labels** (new) to determine whether increased granularity in fuzzy logic improves inertia weight adaptation.

## Implementation Summary

### 1. **New Controller: `fuzzy_controller_w_5labels.py`**

Class `FuzzyInertiaController_5labels` with:

#### Inputs (diversity and iteration progress) with 5 labels each:
```
Diversity:        very_low  │  low  │  medium  │  high  │  very_high
                    (0,0.1,0.2) (0.1,0.25,0.4) (0.3,0.5,0.7) (0.6,0.75,0.9) (0.8,0.9,1.0)

Progress:         very_early│ early │   mid   │ late  │  very_late
                    (0,0.1,0.2) (0.1,0.25,0.4) (0.3,0.5,0.7) (0.6,0.75,0.9) (0.8,0.9,1.0)
```

#### Output (inertia weight) with 5 labels each:
```
Inertia Weight w:  very_low   │   low   │  medium  │   high   │  very_high
Set A:            (0,0.1,0.2) (0.1,0.2,0.35) (0.25,0.4,0.55) (0.45,0.6,0.75) (0.65,0.85,1.0)
Set B:            (0,0.15,0.3) (0.15,0.3,0.45) (0.35,0.5,0.65) (0.55,0.7,0.85) (0.7,0.85,1.0)
Set C:            (0,0.2,0.4) (0.2,0.35,0.5) (0.3,0.5,0.7) (0.5,0.65,0.8) (0.6,0.8,1.0)
Set D:            (0,0.1,0.25) (0.1,0.25,0.4) (0.25,0.4,0.55) (0.45,0.65,0.85) (0.75,0.9,1.0)
```

#### Mamdani Rules: 5×5 = 25 rules

Semantic logic:
- Low diversity + early iteration → maximum exploration (very_high)
- Low diversity + late iteration → accept convergence (low/very_low)
- High diversity → favor exploration (high/very_high)
- Smooth transitions in intermediate states

### 2. **Changes to `fuzzy_controller_w.py` (3 labels)**

- **wMin** changed: `0.1` → `0.0`
- **wMax** changed: `0.9` → `1.0`
- Factory function added: `get_fuzzy_controller(w_set, num_labels=3|5)`

Rationale for wMin/wMax change:
- Range [0,1] is **standard in optimization literature**
- Clearer semantics: 0 = pure exploration, 1 = pure exploitation
- Provides more **space for fuzzy variation** (previously: only 0.8 range)
- Fairer comparison between versions

### 3. **Updated `Solver/solverBEN.py` and `Solver/solverSCP.py`**

Fuzzy controller initialization change:

**Before:**
```python
from FUZZY.fuzzy_controller_w import FuzzyInertiaController
fcs = FuzzyInertiaController(w_set=w_set, wMin=0.1, wMax=0.9)
```

**Now:**
```python
from FUZZY.fuzzy_controller_w import get_fuzzy_controller
num_labels = int(extra_params.get('num_labels', 3)) if extra_params else 3
fcs = get_fuzzy_controller(w_set, num_labels=num_labels)
```

### 4. **Configuration: `experiments_config.json`**

**Before** (4 variants):
```json
"PSO_FCS": [
    {"w_set": "A"},
    {"w_set": "B"},
    {"w_set": "C"},
    {"w_set": "D"}
]
```

**Now** (8 variants):
```json
"PSO_FCS": [
    {"w_set": "A", "num_labels": 3},
    {"w_set": "B", "num_labels": 3},
    {"w_set": "C", "num_labels": 3},
    {"w_set": "D", "num_labels": 3},
    {"w_set": "A", "num_labels": 5},
    {"w_set": "B", "num_labels": 5},
    {"w_set": "C", "num_labels": 5},
    {"w_set": "D", "num_labels": 5}
]
```

System automatically parses these parameters → solvers.

### 5. **Visualization Script: `compare_3vs5_labels_lncs.py`**

Generates LNCS-formatted figures:
1. Membership function comparison (3 vs. 5 for each set)
2. Response table at 9 test points (diversity × iteration combinations)
3. Bar chart comparisons at critical operating points

**Format**: Times New Roman, 300 DPI, English

## Resulting Experiment

### Benchmark Functions (F1, F8, F9, F16)
- **PSO** (baseline): 1 variant
- **PSO_FCS (3 labels)**: 4 variants (A, B, C, D)
- **PSO_FCS (5 labels)**: 4 variants (A, B, C, D)

**Total**: 5 algorithms × 4 functions × 31 runs = **620 new records**

### Research Questions

1. **Does granularity improve performance?** → 5 labels > 3 labels?
2. **Which set is best?** → A vs. B vs. C vs. D in both versions
3. **What matters most?** → Label count vs. semantic characterization?
4. **Does PSO_FCS:5labels approach PSO?** → Gap reduction?

### Metrics of Interest

For each (function, algorithm, num_labels):
- **Mean fitness** (lower is better)
- **Standard deviation** (consistency)
- **Gap to optimum** (%)
- **Convergence speed** (iteration to plateau)
- **w adaptability** (range used, changes per iteration)

## Experiment Execution

```bash
# 1. Generate comparative visualizations
python compare_3vs5_labels_lncs.py

# 2. Reset database (WARNING: deletes previous results)
python reiniciarDB.py

# 3. Populate with 8 PSO_FCS variants
python poblarDB.py

# 4. Execute all experiments
python main.py

# 5. Analyze results
python analisis.py
```

## Key Differences

| Aspect | 3 Labels | 5 Labels |
|--------|----------|----------|
| Rules | 9 (3×3) | 25 (5×5) |
| Granularity | Low | High |
| Transitions | Abrupt | Smooth |
| Complexity | Low | Medium |
| Precision | ±0.15 w | ±0.10 w |
| wMin | 0.0 | 0.0 |
| wMax | 1.0 | 1.0 |

## Expected Outcomes

**Optimistic Hypothesis:**
> 5 labels → finer granularity → better adaptation → PSO_FCS(5) ≈ PSO performance

**Realistic Hypothesis:**
> 5 labels → more rules but same fundamental issue → small improvement (5-15%)

**Conservative Hypothesis:**
> Increased complexity without semantic change → no significant improvement

---

**Next iteration:** If 5 labels don't show substantial improvement, proceed to **fuzzy schemes** (discrete vs. continuous) as originally planned.
