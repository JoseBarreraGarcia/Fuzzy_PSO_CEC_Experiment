# Analysis System Refactoring - Summary

## Overview
The analysis code has been refactored from a fragmented 4-file structure into a unified, modular architecture with a central control hub and LNCS-formatted plot generation.

## Architecture

### Central Hub: `analisis.py`
**Purpose**: Main entry point with configuration-driven analysis selection

**Key Features**:
- `ANALYSIS_CONFIG` dictionary controls which analyses to run
- Four modular analysis functions:
  - `generate_w_timeseries()` - Generate w values per iteration from database
  - `run_comparison_analysis()` - Compare fuzzy sets (A, B, C)
  - `run_detailed_analysis()` - Iteration-by-iteration breakdown
  - `print_summary()` - Display execution results
- Execution timing and status reporting
- English language throughout
- No Unicode characters (Windows terminal compatibility)

**Usage**:
```python
# Edit ANALYSIS_CONFIG to enable/disable analyses
ANALYSIS_CONFIG = {
    "generate_w_timeseries": True,      # ✓ Enable
    "comparison_analysis": True,         # ✓ Enable
    "detailed_analysis": True,          # ✓ Enable
    "verbose": True,                     # Detailed output
}

python analisis.py
```

### Analysis Modules Package: `analysis_modules/`

#### 1. `analysis_modules/compare_fuzzy_sets.py`
**Function**: `analyze_comparison()`

**Features**:
- Loads w_timeseries CSV data
- Compares all fuzzy sets (PSO_FCS:A, B, C)
- Generates 4-panel LNCS-formatted figure:
  - Panel 1: Inertia weight evolution with std bands
  - Panel 2: Population diversity over iterations
  - Panel 3: w vs Diversity scatter plot
  - Panel 4: w vs Progress scatter plot
- Prints summary statistics (mean, std, min, max for all variants)
- Output: `Resultados/resumen/SCP/comparison_fuzzy_sets_LNCS.png`

**LNCS Formatting Applied**:
- Font: Times New Roman 10pt (serif)
- Figure size: 12x9 inches (~12.4cm single column compliant)
- DPI: 300 (publication quality)
- Colors: Blue (A), Orange (B), Purple (C)
- Grid: Light dashed grid for readability
- Legend: Positioned optimally with transparency

#### 2. `analysis_modules/detailed_w_analysis.py`
**Function**: `analyze_detailed()`

**Features**:
- Displays iteration-by-iteration w values for first 10 iterations
- Three statistical analyses:
  1. **Inertia Weight Statistics**:
     - Initial value (iter=1), mean, median, std dev
     - Min/max values
     - Percentage of iterations in ranges (w<0.3, w<0.5, w>0.7)
     - First convergence iteration (w<0.3)
  
  2. **Diversity Adaptation**:
     - Initial/final diversity values
     - Mean, min, max diversity
     - Sharp drops detection (>0.05)
  
  3. **W-Diversity Relationship**:
     - Pearson correlation coefficient
     - Operational phase detection (Exploration, Balanced, Exploitation)

- All three fuzzy sets (A, B, C) analyzed

**Output**: Console report with formatted tables

#### 3. `analysis_modules/__init__.py`
**Purpose**: Package initialization, imports submodules

---

## Data Flow

```
analisis.py (Central Hub)
    ↓
[ANALYSIS_CONFIG determines what to run]
    ↓
    ├→ generate_w_timeseries()
    │   └→ analisisSCP.analizar_instancias()
    │       └→ Generates: w_timeseries_SCP_41_S4-ELIT.csv
    │
    ├→ run_comparison_analysis()
    │   └→ analysis_modules.compare_fuzzy_sets.analyze_comparison()
    │       ├→ Loads: w_timeseries_SCP_41_S4-ELIT.csv
    │       ├→ Creates: comparison_fuzzy_sets_LNCS.png (300 DPI, LNCS-compliant)
    │       └→ Prints: Summary statistics
    │
    └→ run_detailed_analysis()
        └→ analysis_modules.detailed_w_analysis.analyze_detailed()
            ├→ Loads: w_timeseries_SCP_41_S4-ELIT.csv
            ├→ Displays: Iteration breakdown (iter 0-10)
            └→ Prints: Statistical analysis report
```

---

## Run Example

```bash
cd "(solver_bioinspirados)"
env/Scripts/python.exe analisis.py
```

**Output**:
```
======================================================================
                 SCALABLE FUZZY PSO - ANALYSIS CENTER
======================================================================

Configuration:
  generate_w_timeseries          [OK]
  comparison_analysis            [OK]
  detailed_analysis              [OK]

[*] Generating w_timeseries from database...
[OK] w_timeseries generation completed

[*] Running comparison analysis (Fuzzy sets A vs B vs C...)...
[OK] Comparison plot saved: Resultados/resumen/SCP/comparison_fuzzy_sets_LNCS.png

[*] Running detailed iteration analysis...
[OK] Detailed analysis completed

======================================================================
                           ANALYSIS SUMMARY
======================================================================
  w_timeseries generation                        [OK]
  Fuzzy sets comparison                          [OK]
  Detailed iteration analysis                    [OK]
======================================================================

Total execution time: 8.98 seconds
[INFO] Analysis completed.
```

---

## Key Improvements

### Before (Fragmented)
- `analisis.py`: 52 lines, broken w detection (reports "No hay datos de w")
- `analisisSCP.py`: 655 lines, generates CSV but no modular interface
- `compare_fuzzy_sets.py`: 80 lines, standalone script, old formatting
- `detailed_w_analysis.py`: 107 lines, standalone script, mixed language
- **Problem**: Users had to manually edit scripts to change analysis behavior

### After (Unified)
- `analisis.py`: 135 lines, central control with configuration menu
- `analysis_modules/compare_fuzzy_sets.py`: 160 lines, callable function, LNCS formatting
- `analysis_modules/detailed_w_analysis.py`: 180 lines, callable function, structured output
- `analisisSCP.py`: Unchanged (still generates CSV correctly)
- **Solution**: Users edit config dictionary, all analyses run via one command

---

## LNCS Compliance Features

### `comparison_fuzzy_sets_LNCS.png`
✓ **Format**: Times New Roman 10pt serif font  
✓ **Size**: 12x9 inches (fits single column at ~12.4cm)  
✓ **Resolution**: 300 DPI (publication quality)  
✓ **Language**: English (no Spanish)  
✓ **Layout**: 2x2 subplot grid, tight_layout applied  
✓ **Colors**: Professional color scheme (blue, orange, purple)  
✓ **Grid**: Light dashed lines for readability  
✓ **Legend**: Clear labels, transparent background  
✓ **Titles**: Descriptive, no trailing periods  

---

## Configuration Options

Edit `ANALYSIS_CONFIG` in `analisis.py`:

```python
ANALYSIS_CONFIG = {
    "generate_w_timeseries": True,      # Generate w per iteration
    "comparison_analysis": True,         # Compare A, B, C fuzzy sets
    "detailed_analysis": True,          # Show iteration breakdown
    "verbose": True,                     # Print detailed messages
}
```

Set any to `False` to skip that analysis.

---

## Testing Status

✓ **analisis.py**: Runs without errors, all analyses execute sequentially  
✓ **compare_fuzzy_sets.py**: Generates LNCS plot, prints statistics  
✓ **detailed_w_analysis.py**: Displays iteration analysis, detects phases  
✓ **Data files**: w_timeseries CSV loads correctly  
✓ **Output plots**: Generated at 300 DPI in correct location  

---

## Future Enhancements

1. Add plot saving options (PDF, SVG for vector output)
2. Implement benchmark comparison across multiple problem instances
3. Add statistical hypothesis testing (ANOVA, Wilcoxon)
4. Support for custom fuzzy sets beyond A, B, C
5. Generate LATEX tables for paper integration
6. Add multi-instance analysis (aggregate across problems)

---

## File Organization

```
(solver_bioinspirados)/
├── analisis.py                    ← Central hub (REFACTORED)
├── analisisSCP.py                 ← w_timeseries generator
├── analysis_modules/              ← NEW package
│   ├── __init__.py
│   ├── compare_fuzzy_sets.py     ← Comparison analysis (REFACTORED)
│   └── detailed_w_analysis.py    ← Detailed analysis (REFACTORED)
└── Resultados/resumen/SCP/
    └── comparison_fuzzy_sets_LNCS.png  ← LNCS-formatted plot
```

---

## Notes

- All output is in English for conference paper compatibility
- No special Unicode characters (Windows terminal friendly)
- Statistical summaries print to console (can be redirected to file)
- LNCS formatting ensures figures meet publication standards for LNCS proceedings
