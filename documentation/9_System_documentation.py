"""
SCALABLE FUZZY PSO PARAMETER SYSTEM - QUICK START GUIDE

This document explains how the system works and how to extend it with new fuzzy sets.
"""

# SYSTEM FLOW DIAGRAM
"""
┌─────────────────────────────────────────────────────────────────────────────┐
│                         CONFIGURATION FILE                                  │
│              util/json/experiments_config.json                              │
│                                                                             │
│  "mh_params": {                                                            │
│    "PSO_FCS": [                                                            │
│      {"w_set": "A"},                                                       │
│      {"w_set": "B"}                                                        │
│    ]                                                                        │
│  }                                                                          │
└──────────────────┬──────────────────────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      DATABASE POPULATION                                     │
│                    poblarDB.py                                              │
│                                                                             │
│  For each MH, check mh_params:                                             │
│  - PSO_FCS has 2 variants → Create 2 experiment groups                     │
│  - Each group: 2 instances × 2 runs × 2 DS = 8 experiments                │
│  - Total: 2 × 8 = 16 PSO_FCS experiments (8 for A, 8 for B)               │
│                                                                             │
│  Experiments: "PSO_FCS:A", "PSO_FCS:B"                                    │
└──────────────────┬──────────────────────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        SOLVER EXECUTION                                      │
│                      main.py → solverSCP.py                                 │
│                                                                             │
│  1. Receive MH name: "PSO_FCS:A"                                           │
│  2. Parse: mh_base="PSO_FCS", w_set="A"                                   │
│  3. Look up metaheuristics["PSO_FCS"] using mh_base                        │
│  4. Initialize FuzzyInertiaController(..., w_set="A")                     │
│  5. Run solver with correct fuzzy set                                     │
│  6. Store results in database with experiment name "PSO_FCS:A"            │
└──────────────────┬──────────────────────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                       DATA ANALYSIS                                          │
│                    analisis.py → analisisSCP.py                             │
│                                                                             │
│  1. Read experiment data from database                                      │
│  2. Recognize MH variant names: "PSO_FCS:A", "PSO_FCS:B"                  │
│  3. For each variant, extract w values per iteration                       │
│  4. Calculate diversity and progress metrics                               │
│  5. Generate w_timeseries_{instance}_{DS}.csv                             │
│     Columns: MH, run, iter, w, div, progress                              │
│  6. Create plots and statistics                                            │
└──────────────────┬──────────────────────────────────────────────────────────┘
                   │
                   ▼
              RESULTS & PLOTS
"""

# STEP-BY-STEP: HOW TO ADD A NEW FUZZY SET

STEPS = """
EXAMPLE: Adding PSO_FCS:C

STEP 1: Define new fuzzy membership functions
═══════════════════════════════════════════════════════════════════════════════
File: FUZZY/fuzzy_controller_w.py

W_SETS = {
    'A': {
        'low':    (0.1, 0.1, 0.5),      # Triangle membership function
        'medium': (0.3, 0.5, 0.7),
        'high':   (0.5, 0.9, 0.9),
    },
    'B': {
        'low':    (0.1, 0.15, 0.4),
        'medium': (0.3, 0.5, 0.7),
        'high':   (0.5, 0.9, 0.9),
    },
    'C': {                              # NEW SET
        'low':    (0.1, 0.2, 0.3),      # Different shape = different behavior
        'medium': (0.25, 0.5, 0.75),
        'high':   (0.6, 0.9, 0.9),
    }
}


STEP 2: Update configuration
═══════════════════════════════════════════════════════════════════════════════
File: util/json/experiments_config.json

Change from:
    "mh_params": {
        "PSO_FCS": [
            {"w_set": "A"},
            {"w_set": "B"}
        ]
    }

To:
    "mh_params": {
        "PSO_FCS": [
            {"w_set": "A"},
            {"w_set": "B"},
            {"w_set": "C"}                  # NEW LINE
        ]
    }


STEP 3: Reset and populate database
═══════════════════════════════════════════════════════════════════════════════
Command line:

  python reiniciarDB.py      # Clear old experiments
  python poblarDB.py         # Create new experiments including PSO_FCS:C


STEP 4: Run experiments
═══════════════════════════════════════════════════════════════════════════════
Command line:

  python main.py             # Execute all experiments (including PSO_FCS:C)


STEP 5: Analyze results
═══════════════════════════════════════════════════════════════════════════════
Command line:

  python analisis.py         # Generate w_timeseries with PSO_FCS:C data
  python compare_fuzzy_sets.py  # Generate comparison plots

The system automatically recognizes PSO_FCS:C and includes it in all analyses!
"""

# KEY TECHNICAL DETAILS

TECHNICAL_DETAILS = """
WHY THIS ARCHITECTURE?
═══════════════════════════════════════════════════════════════════════════════

Problem Without System:
  - Testing PSO_FCS with 5 fuzzy sets would require:
    * PSO_FCS.py duplicate
    * PSO_FCS_A.py, PSO_FCS_B.py, ..., PSO_FCS_E.py
    * Solver modifications for each
    * Analysis code updates
  - Total: ~50+ lines of duplication, hard to maintain

Solution With Configuration-Driven System:
  - Single PSO_FCS.py function accepts w_set parameter
  - Configuration file defines variant combinations
  - Population system extracts mh_base for lookups
  - Solver passes full MH name for variant tracking
  - Analysis recognizes all variants automatically
  - Total: 3 lines in config file per new variant
  - Scales to 10+ variants with minimal overhead

Technical Pattern:
  "PSO_FCS:A" (experiment name) 
    ↓ Split on ':'
  ["PSO_FCS", "A"]
    ↓ Use for lookup + parameter
  metaheuristics["PSO_FCS"](..., w_set="A")
    ↓ Pass full "PSO_FCS:A" in tracking
  context["mh"] = "PSO_FCS:A"  → Preserves variant in output


ARCHITECTURE ROBUSTNESS
═══════════════════════════════════════════════════════════════════════════════

Files that NEED updating for new metaheuristic parameter:

  ✓ Configuration (mh_params)           → 1 JSON edit
  ✓ Metaheuristic function (w_set param) → 1 param addition
  ✓ imports.py (MH_ARG_MAP)             → 1 string entry
  
Files that DO NOT need updating:

  ✓ poblarDB.py → Already generic, reads mh_params
  ✓ solverSCP.py → Already parses "MH:param" format
  ✓ population_SCP.py → Already extracts mh_base
  ✓ analisisSCP.py → Already handles variant names

This means adding PSO_FCS:Z (or any new variant) requires:
  - 3 file edits (config, .py function, imports.py)
  - 0 solver/population/analysis changes
  - Scales linearly, not exponentially
"""

# MONITORING OUTPUT

MONITORING = """
HOW TO TRACK VARIANT EXECUTION
═══════════════════════════════════════════════════════════════════════════════

1. During main.py execution:
   
   Look for output like:
   ┌─ Procesando Experimento ID: 7
   ├─ Metaheurística: PSO_FCS:A          ← Shows variant tracking
   ├─ Instancia: 41
   └─ Parámetros: iter:100,pop:20,...


2. In w_timeseries output:

   First 3 rows of w_timeseries_SCP_41_S4-STD.csv:
   ┌─ MH,run,iter,w,div,progress
   ├─ PSO_FCS:A,1,0,nan,0.474,0.0        ← Set A, Run 1
   └─ PSO_FCS:B,1,0,nan,0.473,0.0        ← Set B, Run 1
   
   Each row's MH column shows which variant was used.


3. Verification with grep/select-string:

   Get counts per variant:
   $ Select-String "PSO_FCS:A" w_timeseries*.csv | Measure-Object
   $ Select-String "PSO_FCS:B" w_timeseries*.csv | Measure-Object
"""

# PRINT ALL DOCUMENTATION

if __name__ == "__main__":
    print("╔" + "═"*79 + "╗")
    print("║" + " "*79 + "║")
    print("║" + "SCALABLE FUZZY PSO PARAMETER SYSTEM - IMPLEMENTATION GUIDE".center(79) + "║")
    print("║" + " "*79 + "║")
    print("╚" + "═"*79 + "╝")
    print()
    print(STEPS)
    print("\n")
    print(TECHNICAL_DETAILS)
    print("\n")
    print(MONITORING)
    print("\n")
    print("═" * 80)
    print("NEXT STEPS")
    print("═" * 80)
    print("""
1. Review the comparison plot: Resultados/resumen/SCP/comparison_PSO_FCS_fuzzy_sets.png
2. Examine w_timeseries CSV: Resultados/resumen/SCP/w_timeseries_*.csv
3. Add new fuzzy set C to experiments_config.json following Step 2 above
4. Run: python reiniciarDB.py && python poblarDB.py && python main.py
5. Analyze results with compare_fuzzy_sets.py and detailed_w_analysis.py

The system is ready for production use!
""")
