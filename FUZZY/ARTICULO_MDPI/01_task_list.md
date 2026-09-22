# Task list — Artículo MDPI Biomimetics

Checklist accionable. Cada tarea referencia la fase del plan (`00_paper_plan.md`).

## Fase 0 — Carpeta MDPI
- [x] Crear `FUZZY/ARTICULO_MDPI/00_paper_plan.md` (copia canónica del plan)
- [x] Crear `FUZZY/ARTICULO_MDPI/01_task_list.md` (este archivo)
- [x] Crear `FUZZY/ARTICULO_MDPI/02_setup_experimental.md`
- [x] Crear `FUZZY/ARTICULO_MDPI/03_decisiones_metodologicas.md` (log de decisiones D1–D12, citable).
- [x] Crear `FUZZY/ARTICULO_MDPI/04_hipotesis_metricas_analisis.md` (H1–H5, métricas, tests, plan de análisis).

## Fase 1 — Refactor FIS paramétrico
- [x] Crear `config/fuzzy_partitions.json` con esquema 100% paramétrico (sin tripletes hardcoded).
- [x] Crear `FUZZY/fuzzy_controller_auto.py`:
  - [x] `tri(x, a, b, c)` con soporte de hombros.
  - [x] `make_partition_uniform(n, overlap, shoulders)` — generador único para cualquier n.
  - [x] `make_rule_matrix(pattern, n_labels)` — modelo aditivo (identidad si un solo efecto activo; bandas-de-2 si ambos activos).
  - [x] Clase `FuzzyInertiaController_Auto(w_set, num_labels, input_set, rule_set, wMin, wMax)`.
- [x] Modificar `FUZZY/fuzzy_controller_w_3L.py::get_fuzzy_controller`: enruta SIEMPRE a `_Auto` (sistematización total). `_3L`/`_5L` quedan como referencia histórica.
- [x] Crear `FUZZY/4_verify_fis_properties.py`: valida propiedades matemáticas (centros equiespaciados, cobertura, Ruspini iff overlap=1, cardinalidad de reglas, w ∈ [wMin,wMax], determinismo).
- [x] Ejecutar verificación: `python FUZZY/4_verify_fis_properties.py` → **PASS todos los chequeos** (n∈{3,5,7,9} × R1..R8 × overlap∈{0,0.5,1.0} × shoulders∈{T,F}).
- [x] Generar visualización: `python FUZZY/5_visualize_partitions.py` → `FUZZY/plots/partition_{I1,O1}_overview.png`.

**Configuración elegida para la corrida inicial (esquema simétrico con hombros, estándar académico):**
- **I1 (input)**: `scheme=uniform_triangular`, `overlap=1.0` (Ruspini), `shoulders=true`.
  - Centros equiespaciados incluyendo bordes: `c_i = i/(n-1)`.
  - MF[0] hombro izquierdo (a=b=0); MF[n-1] hombro derecho (b=c=1).
  - **Cobertura Ruspini Σμ=1 en TODO [0,1]** → evidencia completa para cualquier valor de diversity/progress, incluidos los bordes.
- **O1 (output)**: idéntico a I1 (mismas fórmulas y `shoulders=true`).
  - Saturación exacta del centroide en wMin y wMax cuando solo MF[0] o MF[n-1] están activas.
- **Esquema simétrico input/output:** justificable en una línea ante revisores (Pedrycz & Gomide 2007, estándar Mamdani).
- **Etiquetas lingüísticas** definidas para n∈{3,5,7,9}:
  - n=7: `very_low, low, medium_low, medium, medium_high, high, very_high`
  - n=9: `very_very_low, very_low, low, medium_low, medium, medium_high, high, very_high, very_very_high`
- **Configurabilidad**: `overlap` y `shoulders` se mantienen parametrizables en el JSON (futuros estudios de sensibilidad).

## Fase 2 — Configuración experimental
- [x] Crear `config/experiments_mdpi_smoke.json` (500 iter, pop 20, 2 runs, 4 variantes PSO_FCS + PSO, 6 funciones F1/F5/F9/F12/F21/F23 → 10 instancias → 100 experimentos).
- [x] Crear `config/experiments_mdpi_full.json` (1000 iter, pop 20, 31 runs, F1–F23, 32 variantes PSO_FCS + PSO → 62 instancias → ~63 426 experimentos).
- [ ] Actualizar `config/analysis_mdpi.json` con flags para módulos `analysis_modules_cec/*`.
- [ ] (Recomendado) Validar configs sin ejecutar: `python -c "from Util.util import cargar_configuracion; cargar_configuracion('config/experiments_mdpi_smoke.json')"` y lo mismo con full.

## Fase 3 — Smoke test
- [ ] Backup: `Copy-Item BD/resultados.db BD/resultados.db.bak_$(Get-Date -Format yyyyMMdd_HHmm)`.
- [ ] `$env:PSO_EXPERIMENTS_CONFIG = ".\config\experiments_mdpi_smoke.json"`
- [ ] `python 0_0_reiniciar.py`
- [ ] `python 1_0_poblarDB.py` → verificar # experimentos generados = **100** (10 instancias × 5 configs × 2 runs).
- [ ] `python 2_main.py` (esperar finalización; estimar costo por experimento para extrapolar a la fase 4).
- [ ] Verificar en BD: SELECT COUNT(*) FROM experimentos WHERE estado='completado' → 100 (cero `error`, cero `ejecutando`, cero `pendiente`).
- [ ] Verificar CSVs en `Resultados/Transitorio/`: para los CSV de PSO_FCS la columna `w` debe estar siempre en `[0.1, 0.9]` y nunca contener NaN/Inf.
- [ ] Inspección cualitativa: graficar 2–3 CSV de configs distintas y comprobar que la trayectoria de `w` y la convergencia tengan forma sensata (no constantes, no oscilaciones extremas).

## Fase 4 — Batch completo
- [ ] Backup `BD/resultados.db`.
- [ ] `$env:PSO_EXPERIMENTS_CONFIG = ".\config\experiments_mdpi_full.json"`
- [ ] Reset → poblar → ejecutar.
- [ ] Monitor: % experimentos completados cada N horas, tiempo medio por experimento.

## Fase 5 — Análisis
- [ ] `$env:PSO_ANALYSIS_CONFIG = ".\config\analysis_mdpi.json"`
- [ ] `python 3_0_analisis.py`
- [ ] Generar nuevos módulos de análisis MDPI:
  - [ ] `analysis_modules_cec/mdpi_factorial_anova.py` (ANOVA 3-way).
  - [ ] `analysis_modules_cec/mdpi_scaling_curves.py` (gap vs dim).
  - [ ] `analysis_modules_cec/mdpi_pareto_problemtype.py` (config × tipo).

## Fase 6 — Manuscrito
- [ ] Bajar plantilla LaTeX MDPI Biomimetics (`https://www.mdpi.com/journal/biomimetics/instructions`).
- [ ] Esqueleto `FUZZY/ARTICULO_MDPI/manuscript/`: `main.tex`, `bibliography.bib`, `figures/`.
- [ ] Redactar secciones en orden: Métodos (Fase 1) → Diseño experimental (Fase 2) → Resultados (Fase 5) → Discusión → Intro + Related work → Conclusión + Limitaciones.
