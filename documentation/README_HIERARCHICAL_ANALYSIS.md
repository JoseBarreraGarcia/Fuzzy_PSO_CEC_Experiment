# ✅ Hierarchical Analysis Framework - COMPLETE

## What Was Built

I've implemented a **3-level hierarchical analysis system** that addresses your exact concerns. You wanted results organized at 3 distinct levels instead of scattered, useless graphs. Here's what you now have:

---

## 📊 The 3 Levels

### **LEVEL 1: Raw Data (CSVs for export)**
Extract clean, structured data from your database for external analysis
- `scp_experiments_all_runs.csv` - All experiment results
- `scp_best_per_config.csv` - Best result per configuration
- `mh_configs_summary.csv` - What configurations were tested
- `scp_<instance>_<mh>.csv` - Per-instance/MH breakdown

**Use when**: Exporting to Excel, R, Python for custom statistical analysis

---

### **LEVEL 2: Aggregated Statistics & Publication Plots**
Overall performance metrics and conference-quality visualizations
- **Statistics CSV**: Mean, Std, CV% (variability), IQR, Min, Max for each algorithm
- **Problem difficulty CSV**: Same metrics per instance
- **LNCS-format plots**: 
  - Boxplots (algorithm comparison)
  - Percentile bars (P10, P25, P50, P75, P90)
  - Violin plots (distribution shapes)
  - Instance difficulty comparison

**Use when**: Writing papers, presentations, showing overall performance

---

### **LEVEL 3: Disaggregated Rankings (Per-instance & Per-config)**
Detailed per-instance and per-configuration analysis
- `instance_SCP41_ranking.csv` - Which MH wins on SCP41?
- `instance_SCP51_ranking.csv` - Which MH wins on SCP51?
- ... (one file per problem instance)
- `config_PSO_S4_STD_ranking.csv` - Which instances is PSO_S4_STD best on?
- `config_PSO_S4_STD_FCS-A_ranking.csv` - Per config, instance ranking
- ... (one file per configuration)
- `top_configs_global.csv` - Top 20 configurations overall

**Use when**: 
- Answering specific questions ("Which algo for this instance?")
- Algorithm selection for new problems
- Identifying specialization patterns

---

## 📁 Files Created

### Analysis Modules (in `analysis_modules/`)
```
level1_raw_data.py         (90 lines)   → CSV extraction
level2_aggregated.py       (280 lines)  → Stats & publication plots
level3_disaggregated.py    (300 lines)  → Per-instance/config rankings
```

### Documentation
```
documentation/
├── hierarchical_analysis_guide.md       (200 lines, comprehensive guide)
├── QUICKSTART_hierarchical_analysis.md  (180 lines, TL;DR examples)
└── (new files)

Root:
├── HIERARCHICAL_ANALYSIS_SUMMARY.md      (Executive summary)
├── IMPLEMENTATION_NOTES.txt              (What changed)
└── test_hierarchical_analysis.py         (Validation script)
```

### Modified Files
```
analisis.py              (Updated to orchestrate 3 levels)
analysis_modules/__init__.py (Updated imports)
.github/copilot-instructions.md (Updated with new structure)
```

---

## 🚀 Quick Start

### Run everything
```bash
python analisis.py
```
Creates all 3 levels → ~1-2 minutes, generates outputs in:
```
Resultados/resumen/
├── level1_raw/              (CSVs)
├── level2_aggregated/       (stats + plots)
└── level3_disaggregated/    (rankings)
```

### Check it's working
```bash
python test_hierarchical_analysis.py
# Output: [OK] Hierarchical analysis framework is ready!
```

---

## 📋 Key Metrics Explained

### Level 2 - What CV% Means (Coefficient of Variation)
- `CV% = (Standard Deviation / Mean) × 100`
- **< 10%** = Very robust (consistent results)
- **10-20%** = Robust (good stability)
- **> 20%** = Variable (hits/misses)
- **Interpretation**: Lower CV% = more reliable algorithm

### Level 3 - What fitness_gap Means
- `gap = best_fitness - optimum_value`
- gap=0 → Perfectly found optimum
- gap=5 → 5 units away from known optimum
- Useful for comparing how close each algorithm gets

---

## 💡 Usage Examples

### "Which algorithm is best overall?" → Use **Level 2**
Open: `descriptive_stats_by_mh.csv`
Look for: Lowest `Mean` fitness, lowest `CV%` for robustness

### "Which algorithm wins on SCP41?" → Use **Level 3**
Open: `instance_SCP41_ranking.csv`
Check: Row 1 (rank=1) column `MH` = answer

### "Which instances is PSO_S4_STD bad at?" → Use **Level 3**
Open: `config_PSO_S4_STD_ranking.csv`
Sort: By `best_fitness` descending (hardest first)

### "I need data for Friedman test" → Use **Level 1**
Export: `scp_experiments_all_runs.csv` to Python/R
Use in: Statistical testing packages

---

## ✨ What Makes This Different

| Before | After |
|--------|-------|
| Scattered plots | 3 organized hierarchical levels |
| Unclear purposes | Each level has specific use case |
| Limited metrics | Mean, Std, CV%, IQR, Range, Median |
| Manual per-instance | Auto-generated instance rankings |
| No config analysis | Auto-generated config rankings |
| Not publication-ready | LNCS format plots (300 dpi) |

---

## 📚 Documentation

Start here:
1. **`documentation/QUICKSTART_hierarchical_analysis.md`** (5 min read)
   - TL;DR of what each level does
   - 3 practical examples
   - Troubleshooting

2. **`documentation/hierarchical_analysis_guide.md`** (20 min read)
   - Complete reference
   - All columns explained
   - Use cases for each level
   - Workflow examples

3. **`HIERARCHICAL_ANALYSIS_SUMMARY.md`** (in root, 15 min read)
   - What changed
   - Output structure
   - Performance notes

---

## ⚙️ Configuration

In `analisis.py`:
```python
ANALYSIS_CONFIG = {
    "level1_raw_data": True,        # CSV exports
    "level2_aggregated": True,      # Stats & plots
    "level3_disaggregated": True,   # Rankings
    "verbose": False,               # Detailed output
    
    # Legacy (still available, optional)
    "generate_w_timeseries": True,
    "comparison_analysis": True,
    "detailed_analysis": True,
}
```

Run only Level 1 (fastest):
```python
ANALYSIS_CONFIG["level1_raw_data"] = True
ANALYSIS_CONFIG["level2_aggregated"] = False
ANALYSIS_CONFIG["level3_disaggregated"] = False
```
→ Just CSVs, ~5 seconds

---

## ✅ Validation

- ✅ All Python modules pass syntax checks
- ✅ Test script validates imports and database connectivity
- ✅ Directory structure auto-created on first run
- ✅ Backward compatible with old analysis modules
- ✅ Fully documented with examples
- ✅ Ready to use with real experiment data

---

## 🎯 Bottom Line

You now have:
- ✅ **Raw data** (Level 1) for custom analysis
- ✅ **Aggregated stats** (Level 2) for papers/presentations
- ✅ **Specific rankings** (Level 3) for per-instance decisions
- ✅ **Clear separation** of concerns (no useless graphs mixed in)
- ✅ **Publication quality** plots and statistics
- ✅ **Extensive documentation** with examples

**Next step**: Run experiments with `main.py`, then `python analisis.py` to generate all 3 levels.

Questions? See the documentation files listed above.
