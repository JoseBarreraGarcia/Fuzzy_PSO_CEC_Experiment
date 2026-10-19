# Reproducibility Guide: MDPI Analysis Pipeline

> **Complete analysis of 63,426 PSO/PSO_FCS experiments on Classical Benchmark Suite (F1–F23).**  
> Generates level-1 raw data → level-2 aggregated statistics → level-3 rankings → hypothesis tests → publication figures and tables.

## Status of the open-data deposit

**Not deposited yet.** Until a public repository and DOI exist, the manuscript must not claim that the data are available (see `03_decisiones_metodologicas.md::D18` and `01_task_list.md::7.12`).

Minimum package to prepare before submission:

- GitHub or Zenodo repository, with DOI for the dataset if possible.
- Final CSV files and the scripts that regenerate every table and figure.
- Configuration file of the 32 FCS variants and the PSO baseline.
- Random seeds used (`seed = 42 × run_id`).
- Rule-bank generator and fuzzy-partition generator.
- Minimal README with run instructions.
- SQLite database, if its size allows it.
- Supplementary material with the complete rankings.

Target wording for the data-availability statement, to be used **only once the deposit exists**:

> The full experimental configuration, random seeds, raw results, processed CSV files, and analysis scripts are available in the associated repository. The repository includes the rule-bank generator, the fuzzy-partition generator, and the scripts required to reproduce all tables and figures reported in this article.

## Quick Start

The manuscript can be rebuilt from the archived run-level database/results without rerunning PSO. From the repository root, with the Python environment and required packages active:

```bash
cd FUZZY/ARTICULO_MDPI/code

# Extract/aggregate the existing completed runs and generate rankings.
python 00_generate_level1_raw_data.py
python 01_generate_level2_aggregated_stats.py
python 02_generate_level3_rankings.py

# Generate stored analysis outputs used by the paper.
python 04_run_scaling_curves.py
python 05_run_pareto_problemtype.py
python 09_run_h1_friedman_nemenyi.py
python 10_run_h4_wilcoxon_vs_baseline.py
python 18_h3_function_dispersion.py

# Generate publication figures/tables and manuscript-specific analyses.
python 06_generate_paper_figures.py
python 07_generate_paper_tables.py
python 08_export_results_to_manuscript.py
python 11_generate_function_level_analysis.py
python 12_analyze_rule_structure.py
python 13_analyze_granularity.py
python 14_analyze_controller_dynamics.py
python 15_generate_mean_dispersion_maps.py
python 16_generate_benchmark_landscapes.py
```

This is an analysis-only workflow; `2_main.py` is not run. `07_generate_paper_tables.py` requires the function-level H3 dispersion file from script 18. Script 13 also reads `results/tests/h3_factorial_anova/summary.json` and script 06 reads `std_across_R_vs_n.csv` for historical diagnostics/plots. Those outputs are retained in the results archive; they come from the earlier unblocked factorial analysis and must not be interpreted as confirmatory H3 evidence. Script 17 reproduces the separate blocked exploratory record and is not needed for the manuscript's descriptive H3 claims.

Manuscript outputs appear in `manuscript/{figures,tables,generated}/`; scripts 11--16 additionally write their designated manuscript fragments/assets directly.

---

## Prerequisites

### Python Environment

**Tested on**: Python 3.14.4 (Windows 11)  
**Conda/venv**: Yes, using local `env/` venv in repo root.

### Required Python Packages

Install via:
```bash
pip install numpy pandas pyarrow scikit-posthocs statsmodels scipy matplotlib seaborn
```

**Verified versions** (see `requirements.txt`):
- pandas >= 2.0
- numpy >= 1.23
- pyarrow >= 14.0
- scikit-posthocs >= 0.17
- statsmodels >= 0.15
- scipy >= 1.18
- matplotlib >= 3.10
- seaborn >= 0.13

### Database

**Required**: `BD/resultados.db` (SQLite)  
Must contain:
- Table `experimentos` (id, experimento, MH, paramMH, estado, ...)
- Table `instancias` (id, tipo_problema, nombre, optimo, param)
- Table `resultados` (id, fitness, tiempoEjecucion, fk_id_experimento)
- Table `iteraciones` (id, archivo [BLOB], fk_id_experimento)

Pre-populate using the outer pipeline:
```bash
python 0_1_reiniciarDB.py     # Reset DB
python 1_0_poblarDB.py        # Load 63,426 experiment records
python 2_main.py              # Run PSO/PSO_FCS solvers (NOT needed for analysis-only run)
```

---

## Detailed Script Execution

### Script 00: Level-1 Raw Data Extraction

**Purpose**: Extract 63,426 experiment records + 63.4M iteration points from BD/resultados.db.

```bash
python 00_generate_level1_raw_data.py [--limit N] [--meta-only]
```

**Options**:
- `--limit N`: Extract only first N experiments (default: all). Useful for testing.
- `--meta-only`: Skip iteration blobs; save only experiment metadata.

**Outputs** (to `results/level1_raw/`):
- `experiments_meta.parquet` (1.7 MB, 63,426 rows)
- `experiments_meta.csv` (7.8 MB, human-readable)
- `iterations.parquet` (2.33 GB, 63,489,426 rows) — **one row per (exp, iteration)**
- `summary.json` (metadata counts + checks)

**Execution time**: ~55 minutes (full dataset)

**Sanity checks** (automated):
- 31 runs per config × instance (1922 instances × 32 PSO_FCS + 1 PSO = 63,426 ✓)
- F8 optimum rescaling per dimension ✓
- 1001 iterations per run ✓
- w ∈ [0.1, 0.9] for PSO (linear schedule) ✓
- 0 NaN values in numeric columns ✓

---

### Script 01: Level-2 Aggregated Statistics

**Purpose**: Compute descriptive statistics (mean, median, std, IQR, success rate, CV%) per configuration/instance marginal.

```bash
python 01_generate_level2_aggregated_stats.py [--eps 1e-6]
```

**Options**:
- `--eps`: success threshold on gap_final (default 1e-6). A run counts as "success" if `fitness_best` within `eps` of known optimum.

**Outputs** (to `results/level2_aggregated/`):
- `stats_by_config_instance.parquet` (2,046 rows; 33 configs × 62 (function, dim) instances)
- `stats_by_config.parquet` (33 rows; marginal over all instances per algorithm)
- `stats_by_n_R.parquet` (32 rows; PSO_FCS only: n_labels × rule_set aggregates)
- `stats_by_function.parquet` (23 rows; problem difficulty ranking)
- `stats_by_dim.parquet` (8 rows; scaling analysis)
- `summary.json` (key statistics + best/worst configs)

**Execution time**: ~2 minutes

**Key columns**:
- `gap_final`: (fitness_best − optimum) / max(|optimum|, 1), clipped ≥ 0
- `success_rate`: fraction of 31 runs where gap_final ≤ eps
- `cv_pct_best`: coefficient of variation (std/mean × 100)

---

### Script 02: Level-3 Rankings

**Purpose**: Rank configurations within each (function, dim) instance; produce per-instance winners and global specialization profiles.

```bash
python 02_generate_level3_rankings.py [--rank-metric {gap_median,gap_mean}]
```

**Outputs** (to `results/level3_rankings/`):
- `ranking_per_instance.parquet` (2,046 rows; ranked (mh) inside each instance)
- `winners_per_instance.parquet` (225 rows; best config per instance, ties preserved)
- `top_configs_global.parquet` (10 rows; configs with most first-place finishes)
- `config_specialization.parquet` (33 rows; mean/median rank per config across all instances)
- `rank_matrix_median.parquet` (33 × 62 matrix; for Friedman test inputs)

**Execution time**: ~1 minute

---

### Script 03: H3 Factorial ANOVA (Interaction n × R)

**Purpose**: Test whether granularity (n_labels ∈ {3,5,7,9}) and rule set (R ∈ {R1,...,R8}) interact significantly; or whether sensitivity to R decreases with n (diminishing returns on granularity).

```bash
python 03_run_factorial_anova.py [--response {gap_final,fitness_best}]
```

**Model**: Two-way ANOVA on log₁₀(gap_final + 1e-12), factors n_labels × rule_set.  
Both **parametric** (Type-II ANOVA via statsmodels) and **non-parametric** (Scheirer–Ray–Hare) tests run.

**Outputs** (to `results/tests/h3_factorial_anova/`):
- `anova_table.csv` (ANOVA F-statistics, p-values, sum-of-squares)
- `srh_table.csv` (Scheirer-Ray-Hare H-statistic, df, p-value)
- `variance_partition.csv` (partial η² per factor)
- `std_across_R_vs_n.csv` (standard deviation of response across R1–R8 per n; declining trend would support H3)
- `residual_diagnostics.json` (Shapiro-Wilk, Levene tests on residuals)

**Execution time**: ~2 minutes (61,504 PSO_FCS observations)

**Expected result**: 
- Main effect of R highly significant (p < 1e-200)
- Main effect of n weakly significant or insignificant
- Interaction n×R **not significant** (p > 0.05) → **H3 rejected**

---

### Script 04: Scaling Curves (Dimensional Analysis)

**Purpose**: Fit log-log scaling of gap_final vs dimension for F1–F13 (the scalable subset) across all configurations.

```bash
python 04_run_scaling_curves.py [--metric {gap_median,gap_mean}]
```

**Model**: log₁₀(gap + 1e-12) = a + b log₁₀(dim), fit via OLS.  
Slope `b` quantifies how quickly convergence quality degrades with dimension.

**Outputs** (to `results/tests/scaling_curves/`):
- `scaling_long.parquet` (1,716 rows; F1–F13 × dims {10,30,50,100})
- `scaling_slopes.parquet` (429 rows; one per (config, function))
- `scaling_slopes_by_mh.parquet` (33 rows; aggregated slopes per config)
- `summary.json` (best/worst scaling; global slope statistics)

**Execution time**: ~1 minute

**Interpretation**: Negative slope → degrades with dimension. R4 typically has gentler slope (~2.3), R1/R5 steeper (~8–12).

---

### Script 05: H2/H5 Pareto and Kendall τ Analysis

**Purpose**: 
- **H2**: Test whether best rule set depends on problem class (unimodal / multimodal / composed).
- **H5**: Test whether a single (n*, R*) dominates both subgroup S1 (F1–F13) and S2 (F14–F23).

```bash
python 05_run_pareto_problemtype.py [--metric {gap_median,gap_mean}]
```

**Outputs** (to `results/tests/h5_pareto_problemtype/`):
- `ranking_by_class.parquet` (99 rows; configs ranked inside unimodal/multimodal/composed)
- `winners_by_class.parquet` (3 rows; best config per class)
- `kendall_tau_by_class.csv` (3×3 matrix of Kendall τ; >0.7 = agreement, <0.3 = low)
- `ranking_by_subgroup.csv` (ranks on S1 vs S2)
- `kendall_tau_S1_vs_S2.json` (main H5 test statistic)
- `pareto_front.parquet` (non-dominated configs in rank(S1) vs rank(S2) space)

**Execution time**: ~1 minute

**Expected result** (for Q1 impact):
- Kendall τ(S1, S2) **significantly < 0.7** (rankings diverge)
- Best config on S1 ≠ best config on S2 (no universal optimum)
- → **H5 supported**: justifies multi-strategy approach

---

### Script 06: Publication Figures

**Purpose**: Generate 7 PNG + PDF figures ready for Q1 journal submission.

```bash
python 06_generate_paper_figures.py [--top-scaling 5] [--top-wilcoxon 10]
```

**Outputs** (to `results/figures_all/`):
1. `fig_cd_diagram_h1.{png,pdf}` — Critical Difference diagram (Friedman + Nemenyi post-hoc)
2. `fig_rule_class_heatmap.{png,pdf}` — Gap median heatmap: (n, R) × problem class
3. `fig_pareto_s1_s2.{png,pdf}` — Pareto front in rank(S1) vs rank(S2) space (H5)
4. `fig_scaling_curves.{png,pdf}` — Gap vs dimension (top-5 configs)
5. `fig_boxplot_gap_by_n.{png,pdf}` — Distribution of gap_final by granularity n
6. `fig_std_R_vs_n.{png,pdf}` — Sensitivity of rule set (std across R) vs n
7. `fig_h4_wilcoxon_bars.{png,pdf}` — Wins/ties/losses vs PSO baseline (top-10 configs)

**Resolution**: 300 DPI, suitable for print/PDF. Format: Times New Roman, LNCS style.

**Execution time**: ~5 seconds

---

### Script 07: LaTeX Tables

**Purpose**: Generate 5 publication-ready booktabs tables.

```bash
python 07_generate_paper_tables.py
```

**Outputs** (to `results/tables_all/`):
1. `tab_top_configs.tex` — Top-10 configs by mean Friedman rank
2. `tab_h4_wilcoxon.tex` — Wilcoxon vs PSO: wins/ties/losses + A₁₂ effect size
3. `tab_kendall_class.tex` — Kendall τ between problem classes
4. `tab_scaling_slopes.tex` — Best/worst scaling slopes (top-5, bottom-5)
5. `tab_hypothesis_summary.tex` — H1–H5 verdicts, key statistics

**All tables**: TeX escaping applied (_, %, <, > → \_ \% \textless{} etc.)

**Execution time**: ~1 second

---

### Script 08: Export to Manuscript

**Purpose**: Copy figures and tables into manuscript tree with relative paths.

```bash
python 08_export_results_to_manuscript.py
```

**Copies**:
- All PNG + PDF → `manuscript/figures/`
- All LaTeX tables → `manuscript/tables/`
- Generates `manuscript/generated/inputs.tex` with commented-out `\input{...}` and `\includegraphics{...}` snippets for copy-paste into main.tex

**Execution time**: <1 second

---

### Script 09: H1 Friedman + Nemenyi

**Purpose**: Rank 33 configurations across 62 instances via Friedman omnibus test, then Nemenyi post-hoc for pairwise significance.

```bash
python 09_run_h1_friedman_nemenyi.py [--alpha 0.05]
```

**Model**: 
- For each instance, rank configurations by median fitness_best.
- Friedman test (non-parametric ANOVA): χ² statistic on ranks.
- Nemenyi post-hoc: Critical Difference (CD) diagram.

**Outputs** (to `results/tests/h1_friedman_nemenyi/`):
- `mean_rank_matrix.parquet` (33 × 62 matrix of ranks)
- `mean_rank_per_config.csv` (configs sorted by mean rank across instances)
- `friedman_omnibus.json` (χ², df, p-value; typically p < 1e-100 → reject H0)
- `nemenyi_pvalues.csv` (528 pairwise p-values)
- `critical_difference.json` (CD threshold; configs within CD of best are not significantly different)
- `cd_diagram_data.csv` (pretty format for CD-diagram visualization in script 06)

**Execution time**: ~2 minutes

**Key result**: 
- Friedman χ² typically >> critical value → strong evidence configurations differ significantly
- CD threshold typically 6–7 ranks → many configs indistinguishable (effect size context)

---

### Script 10: H4 Wilcoxon vs Baseline PSO

**Purpose**: Paired comparison of each PSO_FCS config vs classical PSO on every instance (32 configs × 62 instances = 1,984 tests).

```bash
python 10_run_h4_wilcoxon_vs_baseline.py [--alpha 0.05]
```

**Model**:
- For each (config, instance), collect 31 paired runs (PSO_FCS vs PSO).
- Wilcoxon signed-rank test (non-parametric paired t-test).
- Vargha-Delaney A₁₂ effect size (interpretation: A₁₂ > 0.5 favors PSO_FCS).
- Bonferroni correction over all 1,984 tests.

**Outputs** (to `results/tests/h4_wilcoxon_vs_baseline/`):
- `wilcoxon_pairs.parquet` (1,984 rows; one per config×instance)
- `wilcoxon_config_summary.csv` (32 rows; wins/ties/losses per config, raw α and Bonferroni)
- `top_configs_wins.csv` (top-10 by fractional wins)
- `summary.json` (H4 criterion check: any config with ≥50% wins?)

**Execution time**: ~3 minutes

**Expected result**: 
- Best PSO_FCS config ≈ 27–40 wins out of 62 instances (typically < 50%)
- → **H4 likely rejected** under strict ≥50% criterion
- But Vargha-Delaney A₁₂ ≈ 0.6–0.7 for top configs → moderate effect size (favorable but not overwhelming)

---

## Full Pipeline Execution Time

| Script | Time | Output Size | Notes |
|--------|------|------------|-------|
| 00 | ~55 min | 2.5 GB | Parquet + CSV; depends on DB size |
| 01 | ~2 min | 50 MB | Aggregations |
| 02 | ~1 min | 10 MB | Rankings |
| 03 | ~2 min | 1 MB | ANOVA |
| 04 | ~1 min | 20 MB | Scaling fits |
| 05 | ~1 min | 5 MB | Kendall + Pareto |
| 06 | ~5 sec | 1 MB | Figures |
| 07 | ~1 sec | 100 KB | LaTeX tables |
| 08 | <1 sec | — | Copy + symlink |
| 09 | ~2 min | 5 MB | Friedman + Nemenyi |
| 10 | ~3 min | 10 MB | Wilcoxon + A₁₂ |
| **TOTAL** | **~2.5 hours** | **2.6 GB** | Single-threaded; SSD recommended |

---

## Output Structure

```
FUZZY/ARTICULO_MDPI/
├── code/
│   ├── 00_generate_level1_raw_data.py
│   ├── 01_generate_level2_aggregated_stats.py
│   ├── ... (scripts 02–10)
├── results/
│   ├── level1_raw/
│   │   ├── experiments_meta.parquet (63,426 runs)
│   │   ├── iterations.parquet (63.4M iteration records)
│   │   └── summary.json
│   ├── level2_aggregated/
│   │   ├── stats_by_config_instance.parquet
│   │   ├── stats_by_config.parquet
│   │   ├── stats_by_n_R.parquet
│   │   ├── stats_by_function.parquet
│   │   └── summary.json
│   ├── level3_rankings/
│   │   ├── ranking_per_instance.parquet
│   │   ├── top_configs_global.parquet
│   │   ├── rank_matrix_median.parquet
│   │   └── summary.json
│   ├── tests/
│   │   ├── h3_factorial_anova/
│   │   │   ├── anova_table.csv
│   │   │   ├── srh_table.csv
│   │   │   └── variance_partition.csv
│   │   ├── h1_friedman_nemenyi/
│   │   │   ├── mean_rank_matrix.parquet
│   │   │   ├── critical_difference.json
│   │   │   └── nemenyi_pvalues.csv
│   │   ├── h4_wilcoxon_vs_baseline/
│   │   │   ├── wilcoxon_pairs.parquet
│   │   │   ├── wilcoxon_config_summary.csv
│   │   │   └── summary.json
│   │   ├── h5_pareto_problemtype/
│   │   │   ├── pareto_front.parquet
│   │   │   ├── kendall_tau_by_class.csv
│   │   │   └── summary.json
│   │   └── scaling_curves/
│   │       ├── scaling_slopes.parquet
│   │       └── summary.json
│   ├── figures_all/
│   │   ├── fig_cd_diagram_h1.{png,pdf}
│   │   ├── fig_pareto_s1_s2.{png,pdf}
│   │   └── ... (7 figures total)
│   └── tables_all/
│       ├── tab_top_configs.{tex,csv}
│       ├── tab_hypothesis_summary.{tex,csv}
│       └── ... (5 tables total)
└── manuscript/
    ├── figures/ ← copies of PNG + PDF
    ├── tables/  ← copies of LaTeX .tex
    └── generated/
        └── inputs.tex ← commented snippets for main.tex
```

---

## Sanity Checks & Validation

Each script emits a `summary.json` with:
- Row counts (expected vs actual)
- Numerical ranges (NaN count, min/max, median/std)
- Test statistics (p-values, effect sizes, R²)
- Boolean flags for hypothesis support/rejection

**After running script 01**, verify:
```python
import pandas as pd
meta = pd.read_parquet("results/level1_raw/experiments_meta.parquet")
l2 = pd.read_parquet("results/level2_aggregated/stats_by_config_instance.parquet")

assert len(meta) == 63426
assert meta["gap_final"].isna().sum() == 0
assert (meta["w"] >= 0.1) & (meta["w"] <= 0.9).all()  # PSO baseline
```

---

## Citation & Reproducibility

To cite this analysis pipeline in a Q1 manuscript:

> "All analyses were conducted using Python 3.14 with pandas, numpy, scipy, statsmodels, and scikit-posthocs.  
> Raw data (63,426 experiments, 63.4M iteration records) extracted from SQLite database via custom ETL pipeline.  
> Statistical tests: Friedman ANOVA + Nemenyi post-hoc (Demsar 2006), Wilcoxon signed-rank paired with Vargha-Delaney A₁₂ effect size,  
> two-way ANOVA + Scheirer-Ray-Hare non-parametric alternative, Kendall's τ for ranking concordance.  
> Code and results: [GitHub link / supplementary material]"

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError: scipy` | `pip install scipy statsmodels scikit-posthocs` |
| `FileNotFoundError: BD/resultados.db` | Ensure outer pipeline (0_1, 1_0, 2_main) completed first |
| Parquet file corruption | Delete `results/level1_raw/*.parquet` and re-run script 00 |
| Memory error on script 00 | Use `--limit 10000` for subset extraction; scale linearly |
| LaTeX table corruption in compilation | Ensure `\usepackage{booktabs}` in main.tex; check manifest in tab_.tex files |
| Figures not appearing | Run script 08 to copy PNGs to manuscript/figures/; verify paths in `\includegraphics{...}` |

---

## Contact & Questions

For reproducibility issues or questions about methodology, refer to:
- `FUZZY/ARTICULO_MDPI/04_hipotesis_metricas_analisis.md` — formal hypothesis definitions
- `FUZZY/ARTICULO_MDPI/code/*.py` — inline documentation in each script
- Git commit messages — detailed justifications for each analysis choice
