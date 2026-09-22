# Plan: Artículo MDPI — Granularidad y reglas del FCS Mamdani en PSO sobre CEC

> **Copia canónica versionada en Git.** Espejo de `/memories/session/plan.md`. Cualquier cambio del plan debe propagarse a ambos lados.

## Posicionamiento dentro de la tesis doctoral

Este paper es el **paso preparatorio** de la tesis (ver `documentation/Tesis_DII/proposal.tex`). La tesis propone un **Adaptive Fuzzy Control System (AFCS)** con *dual-level adaptation* (parameter + semantic). Antes de definir formalmente los "fuzzy schemes" y diseñar mecanismos de selección dinámica, este paper responde una pregunta previa:

> **¿Es realmente necesario adaptar la semántica del FCS al tipo de problema, o existe una configuración estática del FCS que domine globalmente?**

Si una sola configuración estática del FCS Mamdani (granularidad y reglas fijas) domina toda la familia F1–F23 del Classical Benchmark Suite, la línea de adaptación semántica de la tesis es injustificable. Si por el contrario el desempeño óptimo varía con el tipo de problema, el paper **motiva empíricamente** la línea de investigación posterior (definición formal de fuzzy schemes + selector dinámico).

**Vocabulario:** este paper habla de **"configuración del FCS Mamdani"** o **"parametrización del FIS"** (granularidad `n` + patrón de reglas `R`). Los términos *fuzzy scheme* y *AFCS* se reservan para *Discussion / Future Work* como continuación natural sugerida por los resultados.

## TL;DR

Evaluar empíricamente, sobre las funciones F1–F23 del **Classical Benchmark Suite** (Abualigah et al., 2021), si distintas configuraciones estáticas del FCS Mamdani (n ∈ {3,5,7,9} × R ∈ {R1…R8} = 32 configuraciones) presentan o no un óptimo único global, o si en cambio la configuración óptima depende del tipo de problema. Infraestructura: FIS paramétrico (`fuzzy_controller_auto.py` + `config/fuzzy_partitions.json`). Smoke test (500 iter, pop 20, 2 runs) → batch completo (1000 iter, pop 20, 31 runs).

## Fases

### Fase 0 — Carpeta y manifiesto MDPI
- Crear `FUZZY/ARTICULO_MDPI/` con `00_paper_plan.md` (este plan), `01_task_list.md` (checklist accionable) y `02_setup_experimental.md` (definición de configs).
- **`FUZZY/ARTICULO_MDPI/00_paper_plan.md` es la copia canónica del plan** — debe sincronizarse con `/memories/session/plan.md` en cada actualización (memoria = working copy, repo = entregable versionado en Git).
- No tocar todavía `1.-OLA2026/`, `2.-CLEI2026/`, `3.-WEA2026/`.

### Fase 1 — Refactor FIS a generador paramétrico  [✅ DONE]
- Módulo `FUZZY/fuzzy_controller_auto.py` con la lógica Mamdani genérica para cualquier `n_labels`.
- JSON `config/fuzzy_partitions.json` con esquema 100% paramétrico:
  - `partitions.I1` y `partitions.O1` ambas con `scheme=uniform_triangular`, `overlap=1.0` (Ruspini), `shoulders=true`.
  - Esquema simétrico estándar Mamdani (Pedrycz & Gomide 2007). Sin tripletes (a,b,c) hardcoded.
- Reglas R1–R8 generadas algorítmicamente con `make_rule_matrix(pattern, n_labels)` (modelo aditivo de dos regímenes).
- Validación: property-based tests (`FUZZY/4_verify_fis_properties.py`). PASS todos los chequeos.
- **Decisión:** se descarta la equivalencia bit-a-bit con WEA/CLEI/OLA. Los resultados se vuelven a ejecutar bajo el esquema sistematizado (ver `03_decisiones_metodologicas.md::D3`).

### Fase 2 — Configuración experimental (no ejecución)
- `config/experiments_mdpi_smoke.json` (test rápido):
  - `iter=500, pop=20, num_experimentos=2, parallel_workers=6`
  - Funciones: F1, F5, F9, F12, F21, F23 (1 unimodal, 1 valle, 2 multimodal escalable, 2 multimodal fija)
  - Dims escalables: {30, 100}
  - Configs PSO_FCS: 4 → {3L-R1, 9L-R1, 3L-R8, 9L-R8} (extremos del cubo)
  - MH: `["PSO", "PSO_FCS"]`
  - ≈ 200 experimentos (~5–15 min)
- `config/experiments_mdpi_full.json` (batch MDPI):
  - `iter=1000, pop=20, num_experimentos=31, parallel_workers=6`
  - Funciones: F1–F23 completas
  - Dims F1–F13: {10, 30, 50, 100} (curva de escalabilidad para revisor)
  - Dims F14–F23: fijas por fórmula
  - Configs PSO_FCS: 32 = n_labels × R1..R8 = {3,5,7,9} × {R1..R8}, todas con `overlap=100%`, `w_set=O1`, `input_set=I1`, `wMin=0.1`, `wMax=0.9`
  - MH: `["PSO", "PSO_FCS"]`
  - ≈ 62 instancias × 33 configs × 31 runs ≈ **63.5k experimentos**

### Fase 3 — Smoke test (validar pipeline)
- `$env:PSO_EXPERIMENTS_CONFIG = ".\config\experiments_mdpi_smoke.json"`
- Reset DB: `python 0_0_reiniciar.py`
- Poblar: `python 1_0_poblarDB.py`
- Ejecutar: `python 2_main.py`
- Verificar: tiempos por experimento, ausencia de crashes, CSVs en `Resultados/Transitorio/`, contenido de tabla `iteraciones`, valores `w` dentro de [0.1, 0.9].
- Verificar equivalencia: para R1–R8 con n_labels ∈ {3,5}, los fitness/w deben coincidir bit-a-bit con corridas previas WEA (seed=42).

### Fase 4 — Batch completo MDPI
- Solo tras smoke verde.
- `$env:PSO_EXPERIMENTS_CONFIG = ".\config\experiments_mdpi_full.json"`
- Mismo flujo (0_0 → 1_0 → 2_main).
- Backup automático de `BD/resultados.db` antes de empezar.

### Fase 5 — Análisis MDPI
- `config/analysis_mdpi.json` ya existe; ampliar para activar todos los módulos `analysis_modules_cec/*`.
- Añadir 3 análisis específicos del paper unificado:
  1. **Efecto factorial** (3-way ANOVA: `output × input × rule × granularidad` sobre gap%). Heatmaps por par.
  2. **Curva de escalabilidad** por (función, config): mediana de gap vs dim ∈ {10,30,50,100}.
  3. **Pareto config → tipo de problema** (unimodal F1–F7 / multimodal-esc F8–F13 / multimodal-fija F14–F23).
- Reutilizar pipeline jerárquico de 3 niveles ya existente (`level1_raw_cec`, `level2_aggregated`, `level3_disaggregated`).

### Fase 6 — Manuscrito MDPI Biomimetics
- Esqueleto en `FUZZY/ARTICULO_MDPI/manuscript/` con plantilla **MDPI Biomimetics** (LaTeX oficial).
- Título tentativo: *"Granularity and Rule-Base Sensitivity of Fuzzy-Controlled PSO over the Classical F1–F23 Benchmark Suite: an empirical study of static FCS configurations"*.
- Secciones: Intro (problema del FCS Mamdani estático para parámetros de MH), Trabajo relacionado (citar OLA/CLEI/WEA propios), FIS paramétrico (Fase 1), Diseño experimental factorial (Fase 2/4), Resultados (Fase 5), Discusión por tipo de función (uni/multi-esc/multi-fija), **Conclusión y future work**: si la heterogeneidad de óptimos se confirma, motivar como continuación natural el diseño de mecanismos que adapten la semántica del FCS al tipo de problema (NO mencionar AFCS por nombre hasta tenerlo implementado).

## Relevant files
- `FUZZY/fuzzy_controller_w_3L.py`, `FUZZY/fuzzy_controller_w_5L.py` — referencia de la lógica Mamdani actual.
- `documentation/6_fuzzy_partition_generator_design.md` — diseño del generador paramétrico.
- `Metaheuristics/Codes/PSO_FCS.py` — consumidor del FIS.
- `Solver/solverBEN.py` (`get_fuzzy_controller`) — punto de inyección del nuevo controlador.
- `1_0_poblarDB.py` — construye `paramMH` ya soporta `num_labels`, `input_set`, `rule_set`.
- `Problem/Benchmark/README_benchmark_functions.md` — catálogo F1–F23.
- `config/experiments_mdpi_smoke.json`, `config/experiments_mdpi_full.json` — configs experimentales del paper (Fase 2). El antiguo `experiments_mdpi.json` (snapshot inicial con dim=100 únicamente) fue eliminado para evitar confusión.
- `config/analysis_mdpi.json` — flags de análisis a actualizar en Fase 5.

## Verification
1. Property-based tests del FIS (`FUZZY/4_verify_fis_properties.py`): centros equiespaciados, Ruspini exacto, cardinalidad de reglas = n², saturación de w, determinismo. **PASS al 2026-06-27.**
2. Smoke test corre sin errores; tabla `experimentos` queda en estado `completado`; CSVs por iteración existen para todos los experimentos.
3. `python 3_0_analisis.py` con `PSO_ANALYSIS_CONFIG=analysis_mdpi.json` genera reportes de los 3 niveles.
4. Para batch completo: NFE = `iter × pop` queda registrado en CSV; mediana de gap entre runs <5% de variación intra-config.

## Decisiones tomadas
- **Revista objetivo:** MDPI **Biomimetics** (tiene descuento; scope acepta bio-inspired metaheuristics + fuzzy control).
- **Framing del paper:** *"Granularity and Rule-Base Sensitivity of Fuzzy-Controlled PSO over the Classical F1–F23 Benchmark Suite: an empirical study of static FCS configurations"*. El paper **NO** propone un nuevo algoritmo ni mecanismos de adaptación; estudia el FCS Mamdani como caja con dos parámetros (granularidad, reglas) y evalúa si existe configuración estática óptima global.
- **Posicionamiento en la tesis (ver `03_decisiones_metodologicas.md::D0`):** prepara empíricamente el terreno para la tesis (AFCS / fuzzy schemes / selector dinámico). *Future Work* explícito: si los resultados muestran heterogeneidad de óptimos, ese hallazgo motiva la línea de adaptación semántica.
- **Roadmap incremental tesis:** (1) este MDPI = PSO+CEC, FCS estático, justifica necesidad. (2) Definición formal de fuzzy schemes + selector dinámico, PSO+CEC. (3) PSO + SCP + KP. (4) PSO + Feature Selection. (5) Misma cadena con GA.
- Mantener R1–R8 como conjunto ortogonal fijo, extendidos algorítmicamente a `n_labels=7,9`.
- Solapamiento fijo (overlap=1.0, Ruspini) + shoulders=True para ambos universos (estándar Mamdani). `overlap` y `shoulders` permanecen paramétricos en el JSON; barrido sensibilidad → trabajo futuro.
- Output: solo `O1` (cubo principal ya es 4×8 = 32 variantes).
- Dimensiones F1–F13: {10, 30, 50, 100}.
- **Baseline único:** PSO clásico con w lineal 0.9→0.4. PSO auto-adaptativo NO se incluye (si revisores lo piden, se añade como 1 MH extra sin tocar FIS).
- `pop=20` consistente con la línea de la rama.
