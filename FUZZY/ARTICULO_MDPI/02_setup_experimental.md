# Setup experimental — Artículo MDPI Mathematics

> **Estado vigente al 2026-10-15.** El batch está completo: 63 426 corridas, 33 configuraciones, 62 instancias y 31 corridas por grupo, incluida F14 con pesos canónicos. Las semillas finales son distintas y se calculan como `42 + historical_exp_id`; `run_id` no constituye un bloque común entre configuraciones. Los análisis finales residen en `results/final_dataset_20261015/`: RQ3 es descriptiva, RQ4 emplea Mann–Whitney independiente con Bonferroni y Tabla 11 una familia independiente con Holm. Las rutas/planes históricos se conservan como referencia, no como procedimientos pendientes.

## Variables del estudio (factor design)

| Factor | Niveles | Origen |
|---|---|---|
| **Granularidad** (`num_labels`) | 3, 5, 7, 9 | Extensión MDPI (CLEI/WEA cubrían 3, 5) |
| **Rule-base pattern** (`rule_set`) | R1, R2, R3, R4, R5, R6, R7, R8 | Ocho patrones de consecuentes evaluados |
| **Output set** (`w_set`) | O1 | Fijo (uniform_triangular, overlap=1, shoulders=true) |
| **Input set** (`input_set`) | I1 | Fijo (uniform_triangular, overlap=1, shoulders=true) |
| **wMin / wMax** | 0.1 / 0.9 | Fijo |
| **MH baseline** | PSO clásico (w lineal 0.9→0.1, tal como se ejecutó) | Implementación `Metaheuristics/Codes/PSO.py` |
| **MH adaptativa** | PSO_FCS (32 configs = 4 × 8) | Esquema sistematizado (Fase 1) |

Total variantes PSO_FCS = 4 × 8 = **32**. Más PSO baseline = **33 configs** por instancia.

**Unidad de réplica y semillas.** Hay 31 corridas independientes por configuración–instancia. Cada corrida tiene una semilla única `seed = 42 + historical_exp_id`; no se comparte una semilla entre configuraciones. Por ello, los contrastes a nivel de corrida son independientes y no se emparejan por `run_id`.

### Nomenclatura canónica  *(D17, 2026-09-24)*

En el manuscrito, una configuración se nombra **`FCS-n-Rk`** (p. ej. `FCS-3-R1`). `O1` e `I1` son constantes de todo el experimento y por eso **no** forman parte de la etiqueta de lectura. Los identificadores extendidos (`PSO_FCS:O1:3:I1:R1`, `PSO_FCS:G3:I1:R1:O1`) quedan restringidos a los artefactos de datos y no deben aparecer en texto, tablas ni figuras.

Terminología uniforme: `rule-base pattern` (no `rule set`), `fixed-dimensional multimodal` (no `composed`), `normalized gap` en prosa, `S1` = F1–F13 y `S2` = F14–F23 definidos una sola vez.

## Benchmark

**Suite:** 23 funciones clásicas (F1–F23), implementadas en `Problem/Benchmark/Problem.py`. Documentación: `Problem/Benchmark/README_benchmark_functions.md` (Group 1).

**Referencia canónica para citar en el paper:**
> Abualigah, L., Diabat, A., Mirjalili, S., Abd Elaziz, M., & Gandomi, A. H. (2021). *The Arithmetic Optimization Algorithm*. **Computer Methods in Applied Mechanics and Engineering**, 376, 113609. https://doi.org/10.1016/j.cma.2020.113609

Las funciones individuales provienen de competiciones CEC anteriores y trabajos clásicos; este paper toma como referencia primaria la suite consolidada por Abualigah et al. (2021), consistente con OLA/CLEI/WEA previos.

| Tipo | Funciones | Dimensión |
|---|---|---|
| Unimodal | F1–F7 | libre (usaremos {10, 30, 50, 100}) |
| Multimodal escalable | F8–F13 | libre (usaremos {10, 30, 50, 100}) |
| Multimodal fija | F14, F16, F17, F18 | 2 (fija por fórmula) |
| Multimodal fija | F19 | 3 |
| Multimodal fija | F15, F21, F22, F23 | 4 |
| Multimodal fija | F20 | 6 |

**Instancias totales (full):** 13 funciones escalables × 4 dims + 10 funciones de dimensión fija = **62 instancias**.

**Nota crítica F8:** el óptimo almacenado en BD es `-418.9829` (valor por dimensión); el óptimo real para dim=d es `-418.9829 × d`. Tener en cuenta al computar gap%. Ver `Problem/Benchmark/README_benchmark_functions.md` para detalle.

## Configuración smoke (`config/experiments_mdpi_smoke.json`)

| Parámetro | Valor |
|---|---|
| `iter` | 500 |
| `pop` | 20 |
| `num_experimentos` | 2 |
| `parallel_workers` | 6 |
| `console_summary_only` | true |
| `use_seed` | true |
| `seed` | 42 |
| Funciones | F1, F5, F9, F12, F21, F23 |
| Dims F1/F5/F9/F12 | {30, 100} |
| Dims F21/F22/F23 | fija (4) |
| Variantes PSO_FCS | 4 = (3L-R1, 9L-R1, 3L-R8, 9L-R8) |
| **Total exp.** | (1 PSO + 4 PSO_FCS) × (4·2 + 2) instancias × 2 runs ≈ **100 experimentos** |

Objetivo: validar pipeline, ausencia de crashes, generación correcta de CSVs, tiempos por experimento (estimar costo del batch full).

## Configuración full (`config/experiments_mdpi_full.json`)

| Parámetro | Valor |
|---|---|
| `iter` | 1000 |
| `pop` | 20 |
| `num_experimentos` | 31 |
| `parallel_workers` | 6 |
| `console_summary_only` | true |
| `use_seed` | true |
| `seed` | 42 |
| Funciones | F1–F23 |
| Dims F1–F13 | {10, 30, 50, 100} |
| Dims F14–F23 | fija |
| Variantes PSO_FCS | 32 = {3,5,7,9} × {R1..R8} |
| **Total exp.** | 62 instancias × 33 configs × 31 runs ≈ **63.5k experimentos** |

## Verificaciones del batch completado

1. **Property tests del FIS PASS**: `python FUZZY/4_verify_fis_properties.py` → todas las propiedades matemáticas validadas (centros, Ruspini, cardinalidad reglas, saturación w, determinismo).
2. **Smoke test verde**: todos los experimentos del smoke en estado `completado` en BD; CSVs por iteración presentes en `Resultados/Transitorio/`.
3. **No-NaN en w**: inspección de 3 CSVs aleatorios del smoke; columna `w` siempre en [wMin, wMax] = [0.1, 0.9].
4. **Integridad final:** 63 426 registros, 62 instancias, 33 configuraciones y 31 corridas por grupo; F14 tiene 1 023 corridas corregidas y verificadas.
5. **Semillas:** 63 426 valores presentes y únicos; no se usan valores sintéticos del exportador para inferencia.

## NFE (Number of Function Evaluations)

- `NFE_total = iter × pop = 1000 × 20 = 20000` por experimento (full).
- Registrado en columna `nfe` de los CSV de iteración por `Solver/solverBEN.py:fo_vectorized`.

## Métricas a reportar

| Métrica | Origen |
|---|---|
| Fitness final, normalized gap y runtime | Dataset consolidado `results/final_dataset_20261015/consolidated_level1.parquet` |
| Ranks/configuración/función | Resúmenes validados en `results/final_dataset_20261015/tables/` |
| RQ3 | Dispersión descriptiva de rangos y log-gap por función y granularidad; no prueba de interacción |
| RQ4 | Mann–Whitney bilateral independiente, corrección Bonferroni en 1 984 comparaciones, $A_{12}$ |
| Tabla 11 | Mann–Whitney bilateral independiente, Holm en familia separada de 1 984 comparaciones, $A_{12}$ |
| Runtime | Cociente entre medianas de muestras independientes; sin join por `run_id` |
| Dinámica | Trayectorias consolidadas de $w(t)$ y XPL y curvas de convergencia representativas |

## Análisis específicos MDPI

| Análisis final | Método / estado |
|---|---|
| RQ1 | Friedman/Nemenyi sobre medianas por instancia |
| RQ2/RQ5 | Rankings y concordancia de Kendall descriptivos para clases y subconjuntos |
| RQ3 | Dispersión descriptiva entre patrones; no se informa inferencia factorial histórica |
| RQ4 / Tabla 11 | Dos familias distintas de pruebas Mann–Whitney independientes; Bonferroni / Holm |
| Runtime y dinámica | Ratio de medianas independientes; resúmenes de $w(t)$, XPL y convergencia |

Las tablas, figuras y salidas reproducibles para la versión final acompañan el PDF en `manuscript/Supplementary_Information_20261015.zip`. No se ejecutan nuevas corridas para reproducir los análisis descritos aquí.
