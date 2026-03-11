# Analysis Modules for CEC2017 Benchmarks

Estructura de análisis multinivel para benchmarks CEC2017 con PSO y PSO_FCS.

## Estructura

```
analysis_modules_cec/
├── __init__.py
├── level1_raw_data_cec.py      # Extrae datos crudos de la BD
├── level2_aggregated_cec.py    # Genera gráficos agregados
└── cec_analysis_pipeline.py    # Orquesta Level 1 + Level 2
```

## Uso

### Opción 1: Ejecutar pipeline completo

```bash
python analysis_modules_cec/cec_analysis_pipeline.py
```

### Opción 2: Ejecutar por niveles

**Level 1: Extraer datos crudos**
```bash
python analysis_modules_cec/level1_raw_data_cec.py
```

Genera:
- `Resultados/resumen/level1_raw_cec/ben_experiments_all_runs.csv`
- `Resultados/resumen/level1_raw_cec/ben_best_per_config.csv`
- `Resultados/resumen/level1_raw_cec/ben_mh_comparison.csv`

**Level 2: Generar gráficos**
```bash
python analysis_modules_cec/level2_aggregated_cec.py
```

Genera:
- `Resultados/resumen/level2_aggregated_cec/comparison/` (4 gráficos por función)
- `Resultados/resumen/level2_aggregated_cec/comparison/` (distribuciones de gap)

## Métricas Analizadas

### Por Experimento
- **Fitness final**: Mejor valor alcanzado
- **Tiempo de ejecución**: Segundos totales
- **Gap al óptimo**: `(fitness - optimo) / optimo * 100%`

### Agregadas por Función
- **Mejor fitness alcanzado** (min)
- **Fitness promedio** (mean ± std)
- **Gap promedio al óptimo**
- **Tiempo promedio de ejecución**
- **Distribución de resultados** (boxplot)

### Comparativa PSO vs PSO_FCS
Los gráficos de comparación muestran 4 métricas:
1. Mejor fitness alcanzado
2. Error relativo al óptimo global
3. Promedio ± Desviación (robustez)
4. Eficiencia computacional (tiempo)

## Estructura de Datos

### Level 1 Output CSVs

**ben_experiments_all_runs.csv**
- Todas las corridas completadas
- Columnas: id_experimento, MH, funcion, fitness, tiempoEjecucion, gap_optimo_pct

**ben_best_per_config.csv**
- Estadísticas por configuración (MH x Función)
- Columnas: funcion, MH, fitness_min, fitness_max, fitness_mean, fitness_std, n_runs, tiempo_medio, gap_medio_pct

**ben_mh_comparison.csv**
- Ranking de MH por función
- Columnas: funcion, MH, fitness_min, fitness_mean, fitness_std, tiempo_medio, gap_pct_medio

### Level 2 Output Gráficos

**comparison_FX.png**: 4 subgráficos para función X
- Mejor fitness alcanzado (barras)
- Error al óptimo (barras)
- Promedio ± Desviación (scatter)
- Tiempo de ejecución (barras)

**gap_distribution_FX.png**: Boxplot de error al óptimo
- Muestra distribución, mediana, cuartiles
- Compara todos los MH para función X

## Próximos Pasos

Cuando haya datos de convergencia disponibles, se generarán:
- `convergence/convergence_FX.png` - Fitness vs iteración
- `diversity/diversity_FX.png` - Diversidad vs iteración

Estos requieren que los archivos de iteraciones estén disponibles en la BD.
