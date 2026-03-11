# Hierarchical Analysis Framework (3 Levels)

## Overview

The analysis system now presents results at **3 distinct hierarchical levels**, each serving a different purpose:

```
LEVEL 1: Raw Data (CSVs)
    ↓
LEVEL 2: Aggregated Statistics & Plots
    ↓
LEVEL 3: Disaggregated Rankings (Per-Instance & Per-Config)
```

---

## Level 1: Raw Data Extraction

**Purpose**: Extract clean, structured CSVs from the database for manual analysis and data export.

**Location**: `Resultados/resumen/level1_raw/`

### Output Files

- **`scp_experiments_all_runs.csv`** (All runs)
  - Columns: id_experimento, MH, binarizacion, paramMH, iteraciones, poblacion, fitness, tiempoEjecucion, estado, instancia_nombre, instancia_optimo
  - Use case: Export all results for external analysis, machine learning, detailed reporting

- **`scp_best_per_config.csv`** (Best per configuration)
  - Best result for each unique (MH, binarizacion, iteraciones, poblacion) combination
  - Use case: Quick overview of what works best without noise from multiple runs

- **`mh_configs_summary.csv`** (Configurations tested)
  - Summary of all MH configurations with run counts
  - Columns: MH, binarizacion, w_set, iteraciones, poblacion, num_runs
  - Use case: Experimental design verification, reproducibility check

- **`scp_<instance>_<mh>.csv`** (Per-instance/MH)
  - Individual CSV for each combination of instance + metaheuristic
  - Use case: Detailed analysis of specific instance-algorithm pairs

### When to Use Level 1

- ✅ Exporting data to external tools (Excel, R, Python, etc.)
- ✅ Building custom visualizations
- ✅ Archiving results
- ✅ Reproducibility and documentation
- ✅ Filtering data manually

---

## Level 2: Aggregated Analysis

**Purpose**: Descriptive statistics and aggregate visualizations showing overall performance patterns **without instance-specific breakdown**.

**Location**: `Resultados/resumen/level2_aggregated/`

### Output Files

#### Statistics CSV
- **`descriptive_stats_by_mh.csv`**
  - Columns: MH, Count, Mean, Median, Min, Max, Range, Std, CV%, Q1, Q3, IQR
  - Shows which MH is best/worst overall
  - **CV% (Coefficient of Variation)** = (Std / Mean) × 100 → robustness measure

- **`descriptive_stats_by_instance.csv`**
  - Columns: Instance, Optimum, Count, Mean, Median, Min, Max, Range, Std, CV%
  - Shows which instances are hardest/easiest for all MH combined
  - Use case: Identify problem difficulty ranking

#### Plots (LNCS Format, PNG, 300 dpi)
- **`boxplot_by_mh.png`**
  - Box plot of all MH fitness distributions
  - Shows median, quartiles, outliers
  - Best for: Quick visual comparison of algorithm robustness

- **`percentile_by_mh.png`**
  - Bar chart with P10, P25, P50, P75, P90 for each MH
  - Shows tail behavior and concentration
  - Best for: Understanding best-case vs worst-case performance

- **`violinplot_by_mh.png`**
  - Kernel density estimation of distributions
  - Shows multimodality, skewness
  - Best for: Detailed distribution shape analysis

- **`boxplot_by_instance.png`** (if ≤ 20 instances)
  - Box plot showing difficulty of each instance
  - Best for: Instance ranking by difficulty

### When to Use Level 2

- ✅ Reporting overall algorithm performance
- ✅ Conference/publication quality plots (LNCS format)
- ✅ Identifying algorithms with consistent vs variable performance
- ✅ Ranking problem difficulty
- ✅ General audience communication (non-specialist)

### Interpreting the Metrics

| Metric | Interpretation |
|--------|-----------------|
| **Mean** | Average performance; lower = better |
| **Std** | Consistency; lower = more reliable |
| **CV%** | Relative variability; < 20% = very robust |
| **IQR** | Middle 50% spread; shows stability |
| **Min/Max** | Best/worst possible results |

---

## Level 3: Disaggregated Analysis

**Purpose**: Detailed per-instance and per-config rankings showing **which algorithm wins on which specific problem**.

**Location**: `Resultados/resumen/level3_disaggregated/`

### Output Files

#### Best Results Summary
- **`best_results_by_instance_mh.csv`**
  - For each (Instance, MH), the **best configuration** and its stats
  - Columns: instance, optimum, MH, binarizacion, w_set, iteraciones, poblacion, fitness_best, fitness_mean, fitness_std, runs_count, fitness_gap
  - Use case: "Which MH should I use for SCP41?"

#### Global Top Configs
- **`top_configs_global.csv`** (top 20)
  - Ranking of best MH configurations globally
  - Columns: rank, MH, binarizacion, w_set, fitness_mean, fitness_min, fitness_max, fitness_std, num_runs
  - Use case: "What are the best 20 configurations overall?"

#### Per-Instance Rankings
- **`instance_SCP41_ranking.csv`**
- **`instance_SCP51_ranking.csv`**
- ... (one per instance)

  - MH ranked by best fitness on that specific instance
  - Columns: rank, MH, optimum, num_runs, best_fitness, mean_fitness, median_fitness, worst_fitness, std_fitness, fitness_gap
  - Shows: **For SCP41, PSO is #1, GA is #2, ...**

#### Per-Configuration Rankings
- **`config_PSO_S4_STD_ranking.csv`**
- **`config_PSO_S4_STD_FCS-A_ranking.csv`**
- ... (one per MH config)

  - Instances ranked by best fitness on that config
  - Columns: rank, instance, optimum, num_runs, best_fitness, mean_fitness, median_fitness, worst_fitness, std_fitness, fitness_gap
  - Shows: **For PSO_S4_STD, SCP41 is hardest, SCP51 is easiest, ...**

### When to Use Level 3

- ✅ Answering specific questions:
  - "Which algorithm wins on instance X?"
  - "Which instances does algorithm Y struggle with?"
  - "Ranking of MH for problem SCP51?"
  - "Ranking of instances for config PSO_FCS:A?"
  
- ✅ Instance-specific algorithm selection
- ✅ Identifying algorithm specialization (best on easy vs hard)
- ✅ Benchmarking and competitive analysis
- ✅ Hyperparameter tuning per-instance

### Example: Using Level 3 Data

**Question**: "What's the best algorithm for SCP41?"

1. Open `instance_SCP41_ranking.csv`
2. Check rank 1 → "PSO_S4_STD with fitness_best = 123, fitness_mean = 125"
3. Verify stability → "std_fitness = 1.2, fitness_gap = 2" (gap from optimum)
4. Decision: PSO_S4_STD is the choice (or PSO_S4_STD_FCS:A if fuzzy variant available)

---

## Workflow Example

### Scenario: You want to write a paper comparing PSO variants

**Step 1: Level 2 (Aggregated)**
- Run `python analisis.py` with `level2_aggregated: True`
- Check `descriptive_stats_by_mh.csv` → Which PSO variant has best Mean/Std/CV?
- Use `boxplot_by_mh.png` and `percentile_by_mh.png` for paper figures

**Step 2: Level 3 (Disaggregated)**
- Run with `level3_disaggregated: True`
- Check `top_configs_global.csv` → Where do PSO variants rank?
- Open instance rankings → "PSO_FCS:A wins on SCP41, SCP51, ... | PSO_FCS:B wins on ..."

**Step 3: Level 1 (Raw Data)**
- Export `scp_experiments_all_runs.csv` to Excel/R
- Create custom statistical tables (e.g., Friedman test, Wilcoxon)
- Add instance-wise performance matrices

---

## Configuration

Edit `analisis.py` to enable/disable levels:

```python
ANALYSIS_CONFIG = {
    "level1_raw_data": True,        # CSV extractions
    "level2_aggregated": True,      # Stats & plots
    "level3_disaggregated": True,   # Per-instance rankings
    "verbose": False,               # Detailed output
}
```

---

## Performance Notes

- **Level 1**: Fast (seconds) - direct DB query
- **Level 2**: Medium (10-30 sec) - aggregation + plotting
- **Level 3**: Slowest (30-60 sec) - many groupby operations + per-instance CSVs

For massive runs (1000+ experiments), disable Level 3 initially and run selectively.

---

## Quick Commands

```bash
# Full analysis (all 3 levels)
python analisis.py

# Only aggregate statistics & plots
python -c "from analysis_modules import level2_aggregated; level2_aggregated.main(verbose=True)"

# Only disaggregated rankings
python -c "from analysis_modules import level3_disaggregated; level3_disaggregated.main(verbose=True)"

# Extract raw CSVs only
python -c "from analysis_modules import level1_raw_data; level1_raw_data.main(verbose=True)"
```
