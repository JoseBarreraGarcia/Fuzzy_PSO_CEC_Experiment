# Quick Start: Hierarchical Analysis

## TL;DR - Just run experiments and analyze

```bash
# After running main.py with your experiments:
python analisis.py

# That's it! You'll get 3 folders of results:
# ├── Resultados/resumen/level1_raw/          (CSVs for export)
# ├── Resultados/resumen/level2_aggregated/   (stats & plots)
# └── Resultados/resumen/level3_disaggregated/ (rankings)
```

---

## What Each Level Gives You

### LEVEL 1: "I need data to analyze"
**Files**: `*.csv`  
**Use when**: Exporting to Excel, R, or Python for custom analysis

Example question: *"I want to run a Friedman test on my results"*
→ Use: `scp_experiments_all_runs.csv` in R/Python

---

### LEVEL 2: "Show me overall performance"
**Files**: `descriptive_stats_by_mh.csv`, `boxplot_by_mh.png`, `percentile_by_mh.png`  
**Use when**: Writing paper, conference presentation, general overview

Example question: *"Which algorithm is most robust (lowest variability)?"*
→ Look at: `descriptive_stats_by_mh.csv` column `CV%` (lower = more robust)

Example question: *"Show me publication-ready plots"*
→ Use: `boxplot_by_mh.png` and `percentile_by_mh.png` (LNCS format, 300 dpi)

---

### LEVEL 3: "Which algorithm wins on this specific problem?"
**Files**: `instance_SCP41_ranking.csv`, `config_PSO_S4_STD_ranking.csv`  
**Use when**: Per-instance analysis, algorithm selection, specialization

Example question: *"Rank all algorithms for instance SCP41"*
→ Open: `instance_SCP41_ranking.csv`
```
rank | MH           | best_fitness | fitness_gap | std_fitness
-----|--------------|--------------|-------------|------------
  1  | PSO_S4_STD   |    123.45    |     2.3     |    0.8
  2  | PSO_S4_ELIT  |    125.12    |     4.0     |    1.2
  3  | GA_S4_STD    |    128.90    |     7.8     |    3.5
```
→ **Answer**: PSO_S4_STD is best for SCP41

Example question: *"For PSO_S4_STD, which instances are hardest?"*
→ Open: `config_PSO_S4_STD_ranking.csv` and sort by `best_fitness` (descending)

---

## Practical Examples

### Example 1: Writing a Paper

**Goal**: Compare PSO variants (PSO_FCS:A vs PSO_FCS:B)

**Steps**:
1. Run: `python analisis.py` (all levels enabled)
2. Level 2 → Get `boxplot_by_mh.png` for Figure 1
3. Level 2 → Get `descriptive_stats_by_mh.csv` for Table 1
   ```
   MH          | Mean    | Std   | CV%   | Min     | Max
   ------------|---------|-------|-------|---------|-------
   PSO_FCS:A   | 124.32  | 2.11  | 1.7%  | 121.23  | 128.45
   PSO_FCS:B   | 123.89  | 2.34  | 1.9%  | 120.11  | 129.12
   ```
4. Level 3 → Instance-wise comparisons in text
   - "PSO_FCS:A outperforms PSO_FCS:B on 7/10 instances"
   - Reference: `instance_SCP41_ranking.csv`, etc.

**Time**: 5-10 minutes total

---

### Example 2: Algorithm Selection for a New Problem

**Goal**: Which PSO config to use for instance SCP51?

**Steps**:
1. Run: `python analisis.py` (just Level 3 needed)
2. Open: `instance_SCP51_ranking.csv`
3. Check row 1 (best rank)
4. Verify column `std_fitness` (stability)
5. If variance is high, check row 2 also

**Example result**:
```
rank | MH              | best_fitness | std_fitness | fitness_gap
-----|-----------------|--------------|-------------|-------------
  1  | PSO_S4_STD_FCS  | 456.78       | 0.34        | 1.2
  2  | PSO_S4_ELIT_FCS | 457.23       | 0.78        | 1.65
```
→ **Decision**: Use PSO_S4_STD_FCS:A for SCP51 (most stable)

**Time**: 30 seconds

---

### Example 3: Deep Dive - Custom Analysis

**Goal**: Statistical comparison (Friedman test) of all algorithms

**Steps**:
1. Run: `python analisis.py` (just Level 1 needed)
2. Export: `scp_experiments_all_runs.csv`
3. Import to Python:
   ```python
   import pandas as pd
   from scipy.stats import friedmanchisquare
   
   df = pd.read_csv('Resultados/resumen/level1_raw/scp_experiments_all_runs.csv')
   
   # Pivot: rows=instances, cols=MH, values=fitness
   pivot = df.pivot_table(
       index='instancia_nombre',
       columns='MH',
       values='fitness',
       aggfunc='min'
   )
   
   # Friedman test
   stat, p = friedmanchisquare(*[pivot[mh].values for mh in pivot.columns])
   print(f"p-value: {p}")
   ```

**Time**: 15-20 minutes

---

## Configuration Tricks

### Run Only One Level

```python
# In analisis.py, set:
ANALYSIS_CONFIG = {
    "level1_raw_data": True,        # ← Only this
    "level2_aggregated": False,
    "level3_disaggregated": False,
    "generate_w_timeseries": False,
    "comparison_analysis": False,
    "detailed_analysis": False,
}
```

Then: `python analisis.py` → Runs in ~5 seconds (just CSVs)

### Run Only Level 2 + 3 (Skip raw data)

```python
ANALYSIS_CONFIG = {
    "level1_raw_data": False,       # ← Skip
    "level2_aggregated": True,
    "level3_disaggregated": True,
    ...
}
```

---

## Understanding the Metrics

### Level 2 Metrics Explained

| Metric | What it means | Target |
|--------|---------------|--------|
| **Mean** | Average fitness | Lower is better |
| **Std** | Standard deviation of results | Lower = more consistent |
| **CV%** | Coefficient of Variation = (Std/Mean)×100 | **< 20% = very robust** |
| **IQR** | Interquartile range (Q3-Q1) | Lower = stable mid-range |
| **Min** | Best result achieved | Self-explanatory |
| **Max** | Worst result achieved | Shows failure mode |
| **Range** | Max - Min | Lower = predictable |

**Example interpretation**:
- Algorithm A: Mean=100, Std=5, CV%=5% → **Very robust**
- Algorithm B: Mean=100, Std=20, CV%=20% → **Variable but ok**
- Algorithm C: Mean=100, Std=50, CV%=50% → **Unreliable**

### Level 3 Metrics Explained

| Column | Meaning |
|--------|---------|
| **rank** | Algorithm ranking for this instance (1=best) |
| **best_fitness** | Best result among all runs |
| **fitness_mean** | Average result |
| **fitness_std** | Consistency |
| **fitness_gap** | best_fitness - optimum (how far from known optimum) |

**Example**: If gap=2 and optimum is 100, best result was ~102 (2% away from optimum)

---

## Troubleshooting

**Q: "No data in Level 1 CSVs"**  
A: Check that you ran `main.py` and experiments finished (status='completado' in database)

**Q: "Missing plots in Level 2"**  
A: Check if `Resultados/resumen/level2_aggregated/plots/` folder exists. If not, re-run with verbose=True to see errors.

**Q: "Slow analysis (took 5+ minutes)"**  
A: Normal for 5000+ experiments. Disable Level 3 if you only need CSVs:
   ```python
   ANALYSIS_CONFIG["level3_disaggregated"] = False
   ```

**Q: "How to interpret `fitness_gap`?"**  
A: It's the difference from optimum. 
   - gap=0 → Found optimum (perfect!)
   - gap=5 → 5 units away from optimum
   - Useful for comparing relative performance

---

## Next Steps

1. ✅ Run experiments with `main.py`
2. ✅ Run analysis with `python analisis.py`
3. ✅ Check folders `Resultados/resumen/level1_2_3/`
4. Pick the level you need:
   - **Level 1** → Export & custom analysis
   - **Level 2** → Papers & presentations
   - **Level 3** → Specific problem answers

See `documentation/hierarchical_analysis_guide.md` for detailed guide and workflows.
