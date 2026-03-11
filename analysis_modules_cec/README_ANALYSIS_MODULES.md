# Analysis Modules for CEC2017 Benchmarks

## Quick Start

```bash
# Ejecutar análisis completo
python analysis_modules_cec/cec_analysis_pipeline.py

# O ejecutar interactivo
python run_cec_analysis.py
```

## Output

Gráficos en: `Resultados/resumen/level2_aggregated_cec/`

### Convergence (convergencia)
- `convergence_F*.png` - 1 por función CEC
- `convergence_overlay_all_functions.png` - Comparativa global
- `convergence_mean_std_bands.png` - Con incertidumbre (±σ)
- `convergence_improvement_rate.png` - Tasa de mejora

### Diversity (diversidad)  
- `diversity_evolution_F*.png` - 1 por función CEC
- `diversity_overlay_all_functions.png` - Comparativa global
- `diversity_vs_fitness_scatter.png` - Correlación
- `diversity_distribution_boxplot.png` - Distribución
- `diversity_timeline_all_mh.png` - Timeline por MH

## Modules

| Módulo | Propósito |
|--------|----------|
| `level1_raw_data_cec.py` | Extrae CSVs crudos de BD |
| `level2_aggregated_cec.py` | Gráficos comparativos |
| `convergence_analysis_cec.py` | Análisis de convergencia |
| `diversity_analysis_cec.py` | Análisis de diversidad |
| `cec_analysis_pipeline.py` | Orquestador (4 pasos) |

## Requirements

- pandas, numpy, matplotlib, seaborn, scipy
- `Resultados/resumen/level1_raw_cec/ben_experiments_all_runs.csv`

