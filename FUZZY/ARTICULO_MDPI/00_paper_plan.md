# Plan: Artículo MDPI — Granularidad y reglas del FCS Mamdani en PSO sobre CEC

> **Copia canónica versionada en Git.** Espejo de `/memories/session/plan.md`. Cualquier cambio del plan debe propagarse a ambos lados.
>
> **Estado al 2026-10-15 — artículo y análisis finalizados.** El dataset consolidado contiene 63 426 corridas (33 configuraciones, 62 instancias, 31 corridas por grupo), incluida la corrección canónica de F14. Las semillas son únicas por corrida (`42 + historical_exp_id`); no se usa `run_id` como bloque común entre configuraciones. RQ3 es descriptiva, sin prueba de interacción. RQ4 usa Mann–Whitney independiente con Bonferroni (1 984 pruebas); la Tabla 11 usa una familia separada de 1 984 pruebas con Holm. El manuscrito compila a 62 páginas y el Supplementary Information a 43; la entrega está en `manuscript/Supplementary_Information_20261015.zip`. Las Fases 0–6 siguientes conservan el plan y registro históricos; el estado vigente es este resumen y `01_task_list.md`.

## Posicionamiento dentro de la tesis doctoral

Este paper es el **paso preparatorio** de la tesis (ver `documentation/Tesis_DII/proposal.tex`). La tesis propone un **Adaptive Fuzzy Control System (AFCS)** con *dual-level adaptation* (parameter + semantic). Antes de definir formalmente los "fuzzy schemes" y diseñar mecanismos de selección dinámica, este paper responde una pregunta previa:

> **¿Es realmente necesario adaptar la semántica del FCS al tipo de problema, o existe una configuración estática del FCS que domine globalmente?**

Si una sola configuración estática del FCS Mamdani (granularidad y reglas fijas) domina toda la familia F1–F23 del Classical Benchmark Suite, la línea de adaptación semántica de la tesis es injustificable. Si por el contrario el desempeño óptimo varía con el tipo de problema, el paper **motiva empíricamente** la línea de investigación posterior (definición formal de fuzzy schemes + selector dinámico).

**Vocabulario:** este paper habla de **"configuración del FCS Mamdani"** o **"parametrización del FIS"** (granularidad `n` + patrón de reglas `R`). Los términos *fuzzy scheme* y *AFCS* se reservan para *Discussion / Future Work* como continuación natural sugerida por los resultados.

## TL;DR

Estudio factorial de 32 configuraciones estáticas del FCS Mamdani ($n\in\{3,5,7,9\}$ × R1–R8) frente a PSO clásico en F1–F23. El batch final comprende 63 426 corridas y usa F14 canónica. El ranking global favorece FCS-3-R1 (rango medio 4.774) y PSO ocupa el segundo lugar (6.363), en el mismo grupo Nemenyi. Los líderes por clase/subconjunto varían; la dispersión entre reglas no disminuye consistentemente con granularidad. La dirección de los ocho contrastes de la Tabla 11 se conserva tras Holm. El estudio es descriptivo donde se indica y no establece causalidad ni una configuración universal transferible.

**Estado de análisis y entrega.** Los resultados vigentes, métodos, PDFs y paquete suplementario se describen en `04_hipotesis_metricas_analisis.md` y `01_task_list.md`. No se planifican nuevas corridas PSO para cerrar este artículo. Las fases siguientes documentan cómo se llegó al diseño y deben leerse como historial, no como tareas pendientes.

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

### Fase 5 — Análisis MDPI *(plan histórico; ejecución final completada)*
El análisis final está consolidado en `results/final_dataset_20261015/`: RQ1–RQ5, tablas, runtime independiente, dinámicas y figuras. RQ3 se presenta solo como dispersión descriptiva; el bootstrap factorial histórico por `run_id` no forma parte de la evidencia final porque los identificadores no son bloques de semilla compartida. RQ4 y Tabla 11 usan familias independientes de Mann–Whitney con Bonferroni y Holm, respectivamente. El cálculo y salidas históricos se preservan en sus carpetas de archivo.

### Fase 6 — Manuscrito MDPI Mathematics
- Esqueleto en `FUZZY/ARTICULO_MDPI/manuscript/` con plantilla **MDPI Mathematics** (LaTeX oficial, `\documentclass[journal=mathematics,...]`).
- Título tentativo: *"Granularity and Rule-Base Sensitivity of Fuzzy-Controlled PSO over the Classical F1–F23 Benchmark Suite: an empirical study of static FCS configurations"*.
- Secciones: Intro (problema del FCS Mamdani estático para parámetros de MH), Trabajo relacionado con literatura pertinente (los antecedentes OLA/CLEI/WEA solo se usan internamente; no se citan por esa relación, D19), FIS paramétrico (Fase 1), Diseño experimental factorial, Results, Discussion por tipo de función y conclusión/future work.

### Fase 7 — Consolidación editorial *(completada al 2026-10-15)*

El manuscrito presenta resultados finales, preguntas RQ1–RQ5, inferencia y alcance coherentes; incluye la tabla por función, análisis formal de las familias de reglas, resultados por clase, granularidad, runtime, dinámica y apéndices. La guía vigente es `EDITORIAL_BEST_PRACTICES.md`; las fuentes editoriales anteriores se conservan en `archive/editorial_guidance_sources_20261015/`.

El artículo se compila a 62 páginas y el Supplementary Information a 43. La entrega contiene datos finales y figuras en `manuscript/Supplementary_Information_20261015.zip`. La carpeta suplementaria activa fue depurada y los materiales legados/no usados se preservan fuera de `manuscript` en `archive/legacy_supplementary_20261015/` y `archive/unused_manuscript_assets_20261015/`.

**Pendientes editoriales de los autores:** aprobar contribuciones CRediT y decidir si se hará un depósito público con DOI. El suplemento incluido en la entrega no equivale a un repositorio público. No se requiere reejecutar PSO para cerrar el artículo.

## Relevant files
- `FUZZY/fuzzy_controller_w_3L.py`, `FUZZY/fuzzy_controller_w_5L.py` — referencia de la lógica Mamdani actual.
- `documentation/6_fuzzy_partition_generator_design.md` — diseño del generador paramétrico.
- `Metaheuristics/Codes/PSO_FCS.py` — consumidor del FIS.
- `Solver/solverBEN.py` (`get_fuzzy_controller`) — punto de inyección del nuevo controlador.
- `1_0_poblarDB.py` — construye `paramMH` ya soporta `num_labels`, `input_set`, `rule_set`.
- `Problem/Benchmark/README_benchmark_functions.md` — catálogo F1–F23.
- `EDITORIAL_BEST_PRACTICES.md` — guía editorial canónica para futuras redacciones y revisiones.
- `FUZZY/1.-OLA2026/`, `FUZZY/2.-CLEI2026/`, `FUZZY/3.-WEA2026/` — antecedentes internos: referencia de organización de análisis/figuras, **no** texto fuente (D19).
- `config/experiments_mdpi_smoke.json`, `config/experiments_mdpi_full.json` — configs experimentales del paper (Fase 2). El antiguo `experiments_mdpi.json` (snapshot inicial con dim=100 únicamente) fue eliminado para evitar confusión.
- `FUZZY/ARTICULO_MDPI/code/03_run_factorial_anova.py` — script histórico; no es parte de la inferencia final ni del paquete suplementario vigente.

## Verification
1. Property-based tests del FIS (`FUZZY/4_verify_fis_properties.py`): centros equiespaciados, Ruspini exacto, cardinalidad de reglas = n², saturación de w, determinismo. **PASS al 2026-06-27.**
2. Smoke test corre sin errores; tabla `experimentos` queda en estado `completado`; CSVs por iteración existen para todos los experimentos.
3. Los reportes estadísticos vigentes están en `results/final_dataset_20261015/`; no se usa `3_0_analisis.py` como generador del artículo final.
4. Dataset final: 63 426 corridas, 33 configuraciones, 62 instancias y 31 réplicas por grupo; 63 426 semillas verificadas y únicas.
5. Inferencia final: RQ4 usa 1 984 pruebas independientes Mann–Whitney con Bonferroni; Tabla 11 usa su familia independiente de 1 984 pruebas con Holm; RQ3 es descriptiva y no estima interacción.
6. PDFs y paquete final validados; artículo y tablas A1–A3 compilan con los recursos activos presentes.

## Decisiones tomadas
- **Revista objetivo:** MDPI **Mathematics** (confirmado 2026-09-24; sustituye a Biomimetics). Implica que la subsección formal `3.4 Formal characterization of the rule-base families` pasa de recomendable a **obligatoria** (ver `03_decisiones_metodologicas.md::D16`).
- **Alcance: un solo artículo.** No se divide en dos papers; la propuesta adaptativa queda para el siguiente trabajo del roadmap (D13).
- **Nomenclatura canónica de configuración:** `FCS-n-Rk` (p. ej. `FCS-3-R1`), formato único en texto, tablas y figuras (D17).
- **Framing del paper:** *"Granularity and Rule-Base Sensitivity of Fuzzy-Controlled PSO over the Classical F1–F23 Benchmark Suite: an empirical study of static FCS configurations"*. El paper **NO** propone un nuevo algoritmo ni mecanismos de adaptación; estudia el FCS Mamdani como caja con dos parámetros (granularidad, reglas) y evalúa si existe configuración estática óptima global.
- **Posicionamiento en la tesis (ver `03_decisiones_metodologicas.md::D0`):** prepara empíricamente el terreno para la tesis (AFCS / fuzzy schemes / selector dinámico). *Future Work* explícito: si los resultados muestran heterogeneidad de óptimos, ese hallazgo motiva la línea de adaptación semántica.
- **Roadmap incremental tesis:** (1) este MDPI = PSO+CEC, FCS estático, justifica necesidad. (2) Definición formal de fuzzy schemes + selector dinámico, PSO+CEC. (3) PSO + SCP + KP. (4) PSO + Feature Selection. (5) Misma cadena con GA.
- Mantener R1–R8 como conjunto ortogonal fijo, extendidos algorítmicamente a `n_labels=7,9`.
- Solapamiento fijo (overlap=1.0, Ruspini) + shoulders=True para ambos universos (estándar Mamdani). `overlap` y `shoulders` permanecen paramétricos en el JSON; barrido sensibilidad → trabajo futuro.
- Output: solo `O1` (cubo principal ya es 4×8 = 32 variantes).
- Dimensiones F1–F13: {10, 30, 50, 100}.
- **Baseline único:** PSO clásico con w lineal 0.9→0.1 (tal como está implementado y ejecutado en `Metaheuristics/Codes/PSO.py`). PSO auto-adaptativo NO se incluye.
- `pop=20` consistente con la línea de la rama.
