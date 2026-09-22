# Setup experimental — Artículo MDPI Biomimetics

## Variables del estudio (factor design)

| Factor | Niveles | Origen |
|---|---|---|
| **Granularidad** (`num_labels`) | 3, 5, 7, 9 | Extensión MDPI (CLEI/WEA cubrían 3, 5) |
| **Rule set** (`rule_set`) | R1, R2, R3, R4, R5, R6, R7, R8 | Conjunto ortogonal aditivo WEA2026 |
| **Output set** (`w_set`) | O1 | Fijo (uniform_triangular, overlap=1, shoulders=true) |
| **Input set** (`input_set`) | I1 | Fijo (uniform_triangular, overlap=1, shoulders=true) |
| **wMin / wMax** | 0.1 / 0.9 | Fijo |
| **MH baseline** | PSO clásico (w lineal 0.9→0.4) | OLA/CLEI/WEA previos |
| **MH adaptativa** | PSO_FCS (32 configs = 4 × 8) | Esquema sistematizado (Fase 1) |

Total variantes PSO_FCS = 4 × 8 = **32**. Más PSO baseline = **33 configs** por instancia.

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

## Verificaciones previas a Fase 4 (batch completo)

1. **Property tests del FIS PASS**: `python FUZZY/4_verify_fis_properties.py` → todas las propiedades matemáticas validadas (centros, Ruspini, cardinalidad reglas, saturación w, determinismo).
2. **Smoke test verde**: todos los experimentos del smoke en estado `completado` en BD; CSVs por iteración presentes en `Resultados/Transitorio/`.
3. **No-NaN en w**: inspección de 3 CSVs aleatorios del smoke; columna `w` siempre en [wMin, wMax] = [0.1, 0.9].
4. **Backup de BD**: `Copy-Item BD/resultados.db BD/resultados.db.bak_smoke_$(Get-Date -Format yyyyMMddHHmm)` antes de empezar el batch completo.
5. **Reset previo**: `python 0_0_reiniciar.py` antes de poblar con la nueva config.

## NFE (Number of Function Evaluations)

- `NFE_total = iter × pop = 1000 × 20 = 20000` por experimento (full).
- Registrado en columna `nfe` de los CSV de iteración por `Solver/solverBEN.py:fo_vectorized`.

## Métricas a reportar

| Métrica | Origen |
|---|---|
| Best fitness final | `Resultados/resumen/level1_raw_cec/` |
| Gap = (best - optimum) / |optimum| (clip ≥ 0) | `compute_gap_rdp()` |
| RDP (relative dispersion) | `compute_gap_rdp()` |
| Diversidad por iteración | `calculate_diversity()` |
| XPL/XPT (explore/exploit ratio) | `initialize_diversity()` |
| w(t) trayectoria | `fcs.w_history` (PSO_FCS) |
| Tiempo de ejecución | `time.time()` por experimento |
| NFE consumidos | `nfe_counter` por experimento |

## Análisis específicos MDPI

| Módulo | Output |
|---|---|
| `mdpi_factorial_anova.py` | ANOVA 3-way (granularidad × rule × tipo_funcion) con η² |
| `mdpi_scaling_curves.py` | Gap mediano vs dim (F1–F13) por config, con IC95% |
| `mdpi_pareto_problemtype.py` | Top-3 configs por tipo (uni/multi-esc/multi-fija) |
| Existentes | Boxplots, violin, convergence curves, w-relationships, 3D surfaces |
