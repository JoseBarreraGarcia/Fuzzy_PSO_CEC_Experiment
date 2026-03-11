# Analysis System - Quick Start Guide

## What Changed

The analysis code has been consolidated from **4 fragmented files** into a **unified modular system** with a central control hub.

### Before
```
analisis.py (broken)
analisisSCP.py (large, not modular)
compare_fuzzy_sets.py (standalone)
detailed_w_analysis.py (standalone)
```

### After
```
analisis.py ← Central hub with configuration menu
analysis_modules/
  ├── compare_fuzzy_sets.py
  └── detailed_w_analysis.py
```

---

## How to Use

### 1. Edit Configuration (Optional)

Open `analisis.py` and modify `ANALYSIS_CONFIG`:

```python
ANALYSIS_CONFIG = {
    "generate_w_timeseries": True,      # Generate CSV with w values
    "comparison_analysis": True,         # Compare fuzzy sets A, B, C
    "detailed_analysis": True,          # Iteration-by-iteration breakdown
    "verbose": True,                     # Print detailed messages
}
```

Set any to `False` to skip that analysis.

### 2. Run

```bash
cd "(solver_bioinspirados)"
env/Scripts/python.exe analisis.py
```

### 3. Results

- **w_timeseries CSV**: `Resultados/resumen/SCP/w_timeseries_SCP_41_S4-ELIT.csv`
- **Comparison plot**: `Resultados/resumen/SCP/comparison_fuzzy_sets_LNCS.png` (LNCS-formatted, 300 DPI)
- **Console output**: Statistical summary and iteration breakdown

---

## Output Breakdown

### A. w_timeseries Generation
Extracts inertia weight per iteration from database:
- Creates CSV with columns: `MH`, `run`, `iter`, `w`, `div`, `progress`
- One row per particle per iteration
- Shows all fuzzy sets: PSO_FCS:A, PSO_FCS:B, PSO_FCS:C

### B. Comparison Analysis
Compares three fuzzy sets across 4 metrics:

**Figure: `comparison_fuzzy_sets_LNCS.png`**
- Panel 1: Inertia weight evolution (line plot with std bands)
- Panel 2: Population diversity over iterations
- Panel 3: Weight vs Diversity relationship (scatter)
- Panel 4: Weight vs Progress relationship (scatter)

**Summary Stats**:
```
PSO_FCS:A:
  Inertia Weight - Mean: 0.355969
  Inertia Weight - Std:  0.115443
  ...

PSO_FCS:B:
  Inertia Weight - Mean: 0.345508
  ...

PSO_FCS:C:
  Inertia Weight - Mean: 0.376000
  ...
```

### C. Detailed Analysis
Iteration-by-iteration breakdown for iterations 0-10:

**Format**:
```
Iteration 1:
  PSO_FCS:A    | w=0.720401 | div= 0.222 | progress= 0.02
  PSO_FCS:B    | w=0.740000 | div= 0.217 | progress= 0.02
  PSO_FCS:C    | w=0.700000 | div= 0.229 | progress= 0.02
```

**Statistical Summaries**:
1. **Inertia Weight Statistics**: Mean, std dev, min/max, convergence point
2. **Diversity Adaptation**: Initial/final values, sharp drops, trends
3. **W-Diversity Relationship**: Correlation, operational phases

---

## LNCS Compliance

The comparison plot meets **LNCS (Lecture Notes in Computer Science)** publication standards:

✓ Font: Times New Roman 10pt  
✓ Resolution: 300 DPI  
✓ Size: ~12.4cm width (fits single column)  
✓ Language: English  
✓ Colors: Professional scheme  
✓ Layout: Clean, readable grid  

**Use for**: Conference papers, journal submissions

---

## Data Files

| File | Purpose | Location |
|------|---------|----------|
| `w_timeseries_SCP_41_S4-ELIT.csv` | Raw w data | `Resultados/resumen/SCP/` |
| `comparison_fuzzy_sets_LNCS.png` | Publication-ready plot | `Resultados/resumen/SCP/` |

---

## Fuzzy Sets Explained

The system compares three inertia weight adaptation strategies:

| Set | Behavior | w Range | Use Case |
|-----|----------|---------|----------|
| **A** | Strict transitions | 0.27-0.73 | Sharp exploration→exploitation |
| **B** | Smooth transitions | 0.26-0.75 | Balanced exploration-exploitation |
| **C** | Conservative | 0.30-0.70 | Stable, gradual convergence |

All three sets adapt weight based on **population diversity** and **search progress**.

---

## Configuration Examples

### Example 1: Compare Fuzzy Sets Only
```python
ANALYSIS_CONFIG = {
    "generate_w_timeseries": False,     # Skip CSV generation
    "comparison_analysis": True,         # Run comparison
    "detailed_analysis": False,         # Skip detailed breakdown
    "verbose": True,
}
```
**Result**: ~2 seconds, only comparison plot generated

### Example 2: Full Analysis
```python
ANALYSIS_CONFIG = {
    "generate_w_timeseries": True,      # Generate fresh CSV
    "comparison_analysis": True,
    "detailed_analysis": True,
    "verbose": True,
}
```
**Result**: ~9 seconds, all analyses complete

### Example 3: Minimal Output
```python
ANALYSIS_CONFIG = {
    "generate_w_timeseries": True,
    "comparison_analysis": True,
    "detailed_analysis": False,
    "verbose": False,                   # Less console output
}
```
**Result**: ~4 seconds, less text output

---

## Troubleshooting

### "No hay datos de w disponibles"
This is normal - it means the database doesn't have w values for that instance/binarization.
The system continues and loads pre-existing CSVs.

### Plot not generated
Check that `Resultados/resumen/SCP/` directory exists:
```bash
mkdir -p Resultados/resumen/SCP
```

### Import errors
Ensure `analysis_modules/` folder exists with:
```
analysis_modules/
  ├── __init__.py
  ├── compare_fuzzy_sets.py
  └── detailed_w_analysis.py
```

---

## Key Metrics Explained

| Metric | Meaning | Ideal Range |
|--------|---------|------------|
| **w (inertia weight)** | Controls exploration vs exploitation | 0.0-1.0 |
| **diversity** | Population spread in search space | 0.0-1.0 (high=spread) |
| **progress** | Iteration count normalized | 0.0-1.0 (0=start, 1=end) |
| **Correlation(w, div)** | How much w adapts to diversity | 0.5-0.8 (strong adaptation) |

---

## Next Steps

For conference papers:
1. Run full analysis: `python analisis.py`
2. Use `comparison_fuzzy_sets_LNCS.png` in paper
3. Copy console output for supplementary material
4. Add table of summary statistics

For code comparison:
1. Disable w_timeseries generation (use cached CSV)
2. Focus on comparison_analysis for visual insights
3. Use detailed_analysis for phase transitions

---

## Technical Details

See [ANALYSIS_REFACTORING_SUMMARY.md](ANALYSIS_REFACTORING_SUMMARY.md) for:
- Architecture details
- Function signatures
- Data flow diagrams
- Implementation notes
