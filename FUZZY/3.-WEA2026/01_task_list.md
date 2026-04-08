# WEA 2026 - Pre-Experimentation Task List

## Phase 0: Validation of Rule Variant Design
- [ ] **T0.1** Revisar literatura: ¿existen estudios que varíen la base de reglas fuzzy en PSO? Confirmar novedad
- [ ] **T0.2** Validar que las 6 variantes de reglas (R1–R6) están semánticamente bien justificadas
- [ ] **T0.3** Verificar consistencia de las reglas 5-label (R1-5L a R6-5L) como extensiones de las 3-label

## Phase 1: Implementation - Rule Variants  
- [ ] **T1.1** Implementar parámetro `rule_set="R1"` en `FuzzyInertiaController` (3 labels)
  - Crear diccionario `RULE_SETS` con R1–R6 (9 reglas cada uno)
  - Seleccionar `self.rules` según `rule_set`
  - Mantener R1 como default (backward compatible)
- [ ] **T1.2** Implementar parámetro `rule_set="R1"` en `FuzzyInertiaController_5labels` (5 labels)
  - Crear diccionario `RULE_SETS_5L` con R1–R6 (25 reglas cada uno)
  - Refactorizar `_build_rules_5x5()` para aceptar `rule_set`
- [ ] **T1.3** Actualizar `get_fuzzy_controller()` factory para propagar `rule_set`
- [ ] **T1.4** Propagar `rule_set` por la cadena: JSON config → `poblarDB.py` → BD → `PSO_FCS.py`
  - Verificar si `paramMH` (JSON string en BD) ya cubre el campo via parsing
- [ ] **T1.5** Tests unitarios: verificar que cada Ri produce diferentes valores de w para mismos inputs
  - Test 3 labels: R1 a R6 con (diversity=0.5, progress=0.5) → 6 valores distintos
  - Test 5 labels: R1-5L a R6-5L con mismos inputs → 6 valores distintos
  - Test backward compat: sin rule_set → usa R1 por defecto

## Phase 2: Configuration & Database
- [ ] **T2.1** Crear `experiments_config_wea2026.json` dedicado (NO modificar el actual)
  - `ben: true, scp: false, uscp: false`
  - `mhs: ["PSO", "PSO_FCS"]`
  - PSO_FCS: 12 variants (R1–R6 × {3L, 5L}), todas con `w_set="A"`, `input_set="I1"`
  - Functions: F1, F5, F11, F21, F22, F23
  - `iter: 500, pop: 50, runs: 31, seed: 42`
- [ ] **T2.2** Actualizar `poblarDB.py` para leer `rule_set` del JSON y pasarlo a la BD
- [ ] **T2.3** Verificar con `check_db.py` que los 13 configs × 6 funciones se poblaron bien
- [ ] **T2.4** Dry-run: ejecutar 1 run de cada variante en 1 función para validar pipeline

## Phase 3: Execution
- [ ] **T3.1** Backup de BD actual antes de correr nuevos experimentos
- [ ] **T3.2** `python reiniciarDB.py` → `python poblarDB.py` → `python main.py`
- [ ] **T3.3** Monitorear progreso con `check_db.py` (estado pendiente/ejecutando/completado)
- [ ] **T3.4** Estimar tiempo total: 2,418 experiments

## Phase 4: Analysis Pipeline
- [ ] **T4.1** Crear módulo `analysis_modules_wea/` para análisis específico de rule variants
- [ ] **T4.2** Generar Level 1 (raw CSV), Level 2 (estadísticas agregadas), Level 3 (rankings)
- [ ] **T4.3** Implementar visualizaciones específicas:
  - Heatmaps de las 6 bases de reglas para 3L y 5L (6×2 paneles)
  - Curvas de w en el tiempo para cada Ri (misma función, overlay)
  - Boxplots por categoría de función
  - Critical Difference diagram (Friedman + Nemenyi)
  - Comparación 3L vs 5L (mismo Ri, diferente granularidad)
  - Superficie de respuesta w(diversity, progress) para cada Ri
- [ ] **T4.4** Tests estadísticos: Wilcoxon pairwise + Friedman ranking + efecto Cohen's d
- [ ] **T4.5** Tabla resumen: ranking por categoría + efecto granularidad

## Phase 5: Paper Writing
- [ ] **T5.1** Completar `paper_wea2026.tex` con estructura LNCS/CCIS
- [ ] **T5.2** Sección 1 (Intro): Motivación + gap + contribución + serie de 3 papers
- [ ] **T5.3** Sección 2 (Related Work): Fuzzy-PSO papers + sensitivity analysis
- [ ] **T5.4** Sección 3 (Framework): FIS, PSO, aislamiento de reglas, 3L vs 5L
- [ ] **T5.5** Sección 4 (Experimental Design): Tablas R1–R6 (3L y 5L) + justificación semántica
- [ ] **T5.6** Sección 5 (Results): Figuras y tablas del análisis
- [ ] **T5.7** Sección 6 (Conclusions): Hallazgos + future work (combinación óptima 3 ejes)
- [ ] **T5.8** Revisar 12–15 páginas + formato CCIS Springer (splncs04)

## Phase 6: Submission
- [ ] **T6.1** Revisión cruzada entre autores
- [ ] **T6.2** Verificar deadlines en web oficial WEA 2026
- [ ] **T6.3** Subir a Microsoft CMT: https://cmt3.research.microsoft.com/WEA2026/

---

## Dependencies

```
T0.x (Validación) 
  └──> T1.x (Implementación rule_set en controllers)
         └──> T2.x (Config JSON + BD)
                └──> T3.x (Ejecución)
                       └──> T4.x (Análisis)
                              └──> T5.x (Escritura)
                                     └──> T6.x (Submission)
```

## Experimental Matrix Summary

| # | Config Name | Labels | Rule Set | Input | Output |
|---|-------------|--------|----------|-------|--------|
| 0 | PSO-STD | — | — | — | — |
| 1 | PSO-FCS-R1-3L | 3 | R1 (baseline) | I1 | A |
| 2 | PSO-FCS-R2-3L | 3 | R2 (exploitation) | I1 | A |
| 3 | PSO-FCS-R3-3L | 3 | R3 (exploration) | I1 | A |
| 4 | PSO-FCS-R4-3L | 3 | R4 (diversity-reactive) | I1 | A |
| 5 | PSO-FCS-R5-3L | 3 | R5 (progress-dominant) | I1 | A |
| 6 | PSO-FCS-R6-3L | 3 | R6 (inverse) | I1 | A |
| 7 | PSO-FCS-R1-5L | 5 | R1 (baseline) | I1 | A |
| 8 | PSO-FCS-R2-5L | 5 | R2 (exploitation) | I1 | A |
| 9 | PSO-FCS-R3-5L | 5 | R3 (exploration) | I1 | A |
| 10 | PSO-FCS-R4-5L | 5 | R4 (diversity-reactive) | I1 | A |
| 11 | PSO-FCS-R5-5L | 5 | R5 (progress-dominant) | I1 | A |
| 12 | PSO-FCS-R6-5L | 5 | R6 (inverse) | I1 | A |

**Total: 13 configs × 6 funciones × 31 runs = 2,418 experimentos**
