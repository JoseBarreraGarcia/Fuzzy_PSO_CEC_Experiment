# Copilot Instructions: Scalable Fuzzy PSO Parameter System

## Project Overview

**Scalable Fuzzy PSO Parameter System** - A configuration-driven metaheuristic optimization framework testing PSO with fuzzy logic inertia weight (w) control across multiple fuzzy sets (A, B, C, D). The system evaluates PSO variants on benchmark problems (BEN/CEC2017), Set Cover Problem (SCP), and Unicost SCP (USCP) without modifying solver code—only JSON configuration.

**Key Insight**: This is a *parameter optimization research platform*, not a single solver. Four fuzzy sets are pre-defined:
- **Set A** (conservative): w focused on 0.1-0.45 (exploitation-biased)
- **Set B** (balanced): w focused on 0.1-0.9 (standard)
- **Set C** (exploratory): w focused on 0.0-1.0 (uniform coverage)
- **Set D** (aggressive): w focused on 0.0-0.3 (exploration-biased)

---

## Critical Architecture Patterns

### 1. **Configuration-Driven Design** (JSON → Database → Solver Pipeline)

All experiments defined in `util/json/experiments_config.json`:
```json
{
  "ben": true,
  "scp": false,
  "mhs": ["PSO", "PSO_FCS"],
  "mh_params": {
    "PSO_FCS": [
      {"w_set": "A"},
      {"w_set": "B"},
      {"w_set": "C"},
      {"w_set": "D"}
    ]
  }
}
```

**Flow**: Config → `poblarDB.py` populates database → `main.py` executes experiments → `analisis.py` generates reports.

**When adding features**: 
1. Update JSON config first
2. Modify database schema if needed (in `BD/sqlite.py.construirTablas()`)
3. Update `poblarDB.py` to load new fields
4. Update solver callers in `main.py` if needed

### 2. **Three Problem Types with Different Dimensionality Handling**

- **BEN/CEC2017** (continuous): `Problem/Benchmark/` - dimensions from config or opfunu library (e.g., F1-F23)
- **SCP** (discrete): `Problem/SCP/` - dimensions from instance file headers (m × n matrix)
- **USCP** (discrete): `Problem/USCP/` - Same as SCP but with uniform costs

**Key**: SCP/USCP dimensions are read from problem instances (`Instances/` directories), not pre-configured. BEN dimensions come from `experiments_config.json` or opfunu defaults.

### 3. **Fuzzy Inertia Weight Controller** (Mamdani FIS)

Located in `FUZZY/fuzzy_controller_w.py`:
- **Inputs**: diversity_ratio (0-1), iteration_progress (0-1)
- **Output**: inertia weight w (wMin to wMax, typically 0.1-0.9)
- **Rules**: 3×3 lookup table (9 Mamdani rules per fuzzy set) in `self.rules` dict
- **Fuzzy Sets**: W_SETS dict defines membership functions for A, B, C, D

**Adding fuzzy set E**: 
1. Add to `W_SETS` dict in `fuzzy_controller_w.py` with triangular membership functions
2. Add to JSON config: `{"w_set": "E"}`
3. Run pipeline: `python reiniciarDB.py && python poblarDB.py && python main.py && python analisis.py`
4. No solver code changes needed—configuration-driven

### 4. **Database Schema (SQLite)**

Four main tables created in `BD/sqlite.py.construirTablas()`:
- **instancias**: Problem definitions (BEN, SCP, USCP) with optimum values
  - Columns: id_instancia, tipo_problema, nombre, optimo, param
- **experimentos**: Experiment configurations + state (pendiente/ejecutando/completado/error)
  - Columns: id_experimento, experimento, MH, binarizacion, paramMH, ML, paramML, ML_FS, paramML_FS, estado, fk_id_instancia
- **resultados**: Final fitness, execution time per experiment
  - Columns: id_resultado, fitness, tiempoEjecucion, solucion, fk_id_experimento
- **iteraciones**: Per-iteration CSV files (w, diversity, fitness data)
  - Columns: id_archivo, nombre, archivo (BLOB), fk_id_experimento

**Critical**: Experiments are stateful. Always run `reiniciarDB.py` before `poblarDB.py` to reset state.

---

## Essential Developer Workflows

### Full Experiment Pipeline
```bash
# 1. Reset database (WARNING: deletes all results)
python reiniciarDB.py

# 2. Populate with new experiments from config
python poblarDB.py

# 3. Run all pending experiments
python main.py

# 4. Generate 3-level hierarchical analysis
python analisis.py
```

### 3-Level Hierarchical Analysis Framework

Results now presented at 3 distinct hierarchical levels:

**Level 1: Raw Data (CSVs)**
- `scp_experiments_all_runs.csv` - All experiment results
- `scp_best_per_config.csv` - Best per configuration
- Location: `Resultados/resumen/level1_raw/`
- Use: Export to Excel/R for custom analysis, statistical tests

**Level 2: Aggregated Statistics & Plots**
- `descriptive_stats_by_mh.csv` - Mean, Std, CV%, IQR by algorithm
- `descriptive_stats_by_instance.csv` - Problem difficulty ranking
- Publication-quality plots: boxplots, percentile bars, violin plots
- Location: `Resultados/resumen/level2_aggregated/`
- Use: Conference papers, general performance overview

**Level 3: Disaggregated Rankings**
- `instance_SCP41_ranking.csv` - Which MH wins on SCP41?
- `config_PSO_S4_STD_ranking.csv` - Which instances is PSO_S4_STD best on?
- `top_configs_global.csv` - Best 20 configurations overall
- Location: `Resultados/resumen/level3_disaggregated/`
- Use: Algorithm specialization analysis, per-instance selection

### Fuzzy Set Visualizations

The system automatically generates 8 publication-quality PNG plots:

**Generated Plots** (in `FUZZY/plots/`):
1. `01_fuzzy_input_diversity.png` - Diversity membership functions (low/medium/high)
2. `02_fuzzy_input_progress.png` - Iteration progress membership functions (early/mid/late)
3. `03_fuzzy_output_w_set_A.png`, `03_fuzzy_output_w_set_B.png`, etc. - Inertia weight output per set
4. `04_fuzzy_rules_heatmap.png` - Mamdani rule base (3×3 matrix visualization)
5. `05_fuzzy_w_sets_comparison.png` - All 4 sets side-by-side comparison

**Features**:
- LNCS format (Times New Roman, 300 DPI)
- PNG format suitable for papers, presentations
- Automatic generation as part of `python analisis.py`
- Can be generated standalone: `python generate_fuzzy_plots.py`

### Quick Analysis Scripts

- `python compare_fuzzy_sets.py` - PSO_FCS:A vs B vs C comparison plots
- `python detailed_w_analysis.py` - Per-iteration breakdown of w values
- `python check_db.py` - Query experiment status and results

---

## Code Patterns & Conventions

### **Solver Function Signature** (all accept same interface)
```python
# Continuous problems (BEN/CEC2017)
def solverBEN(id, mh, maxIter, pop, function, lb, ub, dim, extra_params=None)

# Discrete problems (SCP/USCP)
def solverSCP(id, mh, maxIter, pop, instancia, ds, repair, parMH, unicost)
```
Parameters come directly from database `experimentos` table, parsed from JSON strings (e.g., `"iter:100,pop:50"` → dict).

### **Metaheuristics Module Pattern** (`Metaheuristics/Codes/`)
Each MH (PSO, GA, etc.) must implement:
- Constructor: `MH(pop, dim, lb, ub, seed=None)`
- Method: `iterate(population)` → updated_population
- Use vectorized numpy operations for speed

### **PSO with Fuzzy Controller (PSO_FCS)** (`Metaheuristics/Codes/PSO_FCS.py`)
```python
def iterarPSO_FCS(maxIter, iter, dim, population, best, pBest, vel, ub0,
                  maxDiversity, fcs: FuzzyInertiaController, w_set="B"):
    # Calculate diversity_ratio (0-1) and progress (0-1)
    # Call fcs.compute_w(diversity_ratio, progress) to get w
    # Apply w to velocity update equation
```

### **Diversity Tracking** (`Diversity/Codes/diversity.py`)
- `calculate_diversity()`: Population spread (0-1)
- `diversity_per_dimension()`: Per-dimension breakdown (essential for PSO inertia control)
- `compute_gap_rdp()`: Relative diversity and population entropy
- All normalized to [0,1] range for fuzzy inputs

### **Logging Strategy**
- `Util/console_logging.py`: Console output during execution
- `Util/csv_writer.py`: Per-iteration CSV logs (fitness, diversity, w values)
- Results stored in `Resultados/Transitorio/` (intermediate), then `Resultados/resumen/` after analysis

---

## Integration Points & Dependencies

| Component | Purpose | Input | Output |
|-----------|---------|-------|--------|
| `main.py` | Orchestrator | experiment_id | Calls solver, logs results |
| `FUZZY/fuzzy_controller_w.py` | FIS evaluator | (diversity, iteration) | w value |
| `Metaheuristics/Codes/PSO_FCS.py` | PSO with fuzzy | population, w_set | updated_population |
| `Problem/Benchmark/` | BEN fitness | x-vector, dim | fitness float |
| `Problem/SCP/` | SCP fitness | solution, instance | cost integer |
| `Diversity/Codes/` | Diversity metrics | population | diversity float (0-1) |
| `BD/sqlite.py` | State persistence | SQL queries | experiment records |

**Data Flow**: `main.py` → `solverBEN/solverSCP` → `PSO_FCS.iterarPSO_FCS` → `FuzzyInertiaController.compute_w` → `Diversity.calculate_diversity` → CSV logging in `Resultados/Transitorio/`

---

## Key Files for Different Tasks

| Task | Primary Files |
|------|----------------|
| Add experiment variant | `util/json/experiments_config.json`, `poblarDB.py` |
| Modify fuzzy logic rules | `FUZZY/fuzzy_controller_w.py` (rules dict + W_SETS dict) |
| Add new MH algorithm | `Metaheuristics/Codes/*.py`, `Solver/solverBEN.py` (add executor) |
| Fix bug in results storage | `Solver/solverBEN.py` / `solverSCP.py`, `Util/csv_writer.py` |
| Change analysis plots | `analysis_modules/compare_fuzzy_sets.py`, `detailed_w_analysis.py` |
| Debug experiment state | `BD/sqlite.py`, `check_db.py` (query experiment status) |
| Add problem type | `Problem/*/` new folder, `main.py` add executor, `BD/sqlite.py` add table |

---

## Common Debugging Patterns

**Experiment stuck in "ejecutando" state**: 
- Check `check_db.py` for incomplete records
- May indicate solver crash; examine `Resultados/Transitorio/` for partial CSV output
- Run `python check_db.py` to query database state

**Missing results in analysis**: 
- Ensure `analisis.py` executed and `generate_w_timeseries=True`
- CSV files must exist in `Resultados/resumen/SCP/` before plotting
- Check `Resultados/Transitorio/` for raw output

**Fuzzy set not applied**: 
- Verify `w_set` field in JSON matches exactly (case-sensitive: "A", "B", "C", "D")
- Verify membership functions added to `W_SETS` dict in `fuzzy_controller_w.py`
- Verify `Metaheuristics/Codes/PSO_FCS.py` uses `fcs.compute_w(diversity_ratio, progress)`

**Database corruption**: 
- Run `python reiniciarDB.py` (destructive), then rebuild from config
- Keep backups of `BD/resultados.db` before pipeline runs
- Use `Scripts/db_scanner.py` to analyze and reconstruct config.json from database

**NFE (Number of Function Evaluations) tracking**: 
- `Solver/solverBEN.py` tracks with `nfe_counter[0]`
- CSV output includes `nfe` column in header
- Passed to fitness evaluation function via `extra_params`

---

## Documentation Reference

- **Quick start** (5 min): `documentation/2_Readme_fuzzy_system.md`
- **Technical status** (15 min): `documentation/3_Implementation_status.md`
- **Fuzzy sets deep dive** (20 min): `documentation/4_Fuzzy_sets_deep_dive.md`
- **Complete reference** (40 min): `documentation/5_Final_report.txt`
- **Hierarchical analysis**: `documentation/hierarchical_analysis_guide.md`

**Start with `documentation/1_Index.md` for navigation.**
