# WEA 2026 - Pre-Experimentation Task List

## Phase 0: Validation of Rule Variant Design
- [x] **T0.1** Revisar literatura: ¿existen estudios que varíen la base de reglas fuzzy en PSO? Confirmar novedad
- [x] **T0.2** Diseñar reglas con modelo factorial ortogonal (no ad-hoc)
  - Modelo aditivo: `output = clip(progress_effect + diversity_effect)`
  - 2 ejes semánticos: dirección de progreso (↓/↑/—) × reacción a diversidad (→/←/—)
  - 8 combinaciones: R1-R8 con pares espejo (R1↔R2, R3↔R4, R5↔R8, R6↔R7)
  - R1-R4 aíslan un factor (main effects), R5-R8 combinan ambos (interaction)
- [x] **T0.3** Verificar consistencia 3L↔5L: mismo modelo aditivo, 3L con effects ∈{-1,0,+1}, 5L con effects ∈{-2,-1,0,+1,+2}
- [x] **T0.4** Generar visualizaciones de validación (heatmaps + superficies 3D) → `FUZZY/plots/`

## Phase 1: Implementation - Rule Variants  
- [x] **T1.1** Implementar `RULE_SETS` en `FuzzyInertiaController_3L` (`fuzzy_controller_w_3L.py`)
  - 8 rule sets (R1-R8), 9 reglas cada uno
  - Parámetro `rule_set="R1"` con R1 como default
- [x] **T1.2** Implementar `RULE_SETS` en `FuzzyInertiaController_5L` (`fuzzy_controller_w_5L.py`)
  - 8 rule sets (R1-R8), 25 reglas cada uno
  - Mismo modelo aditivo que 3L, granularity extendida
- [x] **T1.3** Factory `get_fuzzy_controller()` propaga `rule_set` correctamente
- [x] **T1.4** Pipeline config→BD→solver funcional: `rule_set` se propaga via `paramMH` JSON string
- [x] **T1.5** Fix crítico: pBest bug en `population_BEN.py` y `population_SCP.py`
  - PSO_FCS no actualizaba pBest (condición `mh == 'PSO'` excluía PSO_FCS)
  - Corregido: `if mh in ('PSO', 'PSO_FCS') or mh.startswith('PSO_FCS:')`
- [x] **T1.6** Fix path relativo en `fuzzy_plots.py` y `2_generate_3d_plot.py`
  - `'./FUZZY/plots'` → `os.path.dirname(os.path.abspath(__file__))` 
  - Eliminada carpeta duplicada `FUZZY/FUZZY/plots`

## Phase 2: Configuration & Database
- [ ] **T2.1** Crear `experiments_config_wea2026.json` dedicado (NO modificar el actual)
  - `ben: true, scp: false, uscp: false`
  - `mhs: ["PSO", "PSO_FCS"]`
  - PSO_FCS: 16 variants (R1–R8 × {3L, 5L}), todas con `w_set="O1"`, `input_set="I1"`
  - Functions: F1, F5, F11, F21, F22, F23
  - `iter: 500, pop: 50, runs: 31, seed: 42`
- [ ] **T2.2** Verificar con `check_db.py` que los 17 configs × 6 funciones se poblaron bien
- [ ] **T2.3** Dry-run: ejecutar 1 run de cada variante en 1 función para validar pipeline

## Phase 3: Execution
- [ ] **T3.1** Backup de BD actual antes de correr nuevos experimentos
- [ ] **T3.2** `python reiniciarDB.py` → `python poblarDB.py` → `python main.py`
- [ ] **T3.3** Monitorear progreso con `check_db.py` (estado pendiente/ejecutando/completado)
- [ ] **T3.4** Estimar tiempo total: 3,162 experiments

## Phase 4: Analysis Pipeline
- [ ] **T4.1** Crear módulo `analysis_modules_wea/` para análisis específico de rule variants
- [ ] **T4.2** Generar Level 1 (raw CSV), Level 2 (estadísticas agregadas), Level 3 (rankings)
- [ ] **T4.3** Implementar visualizaciones específicas:
  - Heatmaps de las 8 bases de reglas para 3L y 5L (8×2 paneles) ✓ ya generados
  - Superficies 3D w(diversity, progress) para cada Ri (8×2) ✓ ya generados
  - Curvas de w en el tiempo para cada Ri (misma función, overlay)
  - Boxplots por categoría de función
  - Critical Difference diagram (Friedman + Nemenyi)
  - Comparación 3L vs 5L (mismo Ri, diferente granularidad)
  - **Mirror pair overlays**: R1 vs R2, R3 vs R4, R5 vs R8, R6 vs R7
  - **Factorial interaction plot**: progress_dir × diversity_dir → mean fitness
- [ ] **T4.4** Tests estadísticos: Wilcoxon pairwise + Friedman ranking + efecto Cohen's d
- [ ] **T4.5** Tabla resumen: ranking por categoría + efecto granularidad

## Phase 5: Paper Writing
- [ ] **T5.1** Completar `paper_wea2026.tex` con estructura LNCS/CCIS
- [ ] **T5.2** Sección 1 (Intro): Motivación + gap + contribución + serie de 3 papers
- [ ] **T5.3** Sección 2 (Related Work): Fuzzy-PSO papers + sensitivity analysis
- [ ] **T5.4** Sección 3 (Framework): FIS, PSO, aislamiento de reglas, 3L vs 5L
- [ ] **T5.5** Sección 4 (Experimental Design): Modelo aditivo factorial + tablas R1–R8 (3L y 5L) + justificación
- [ ] **T5.6** Sección 5 (Results): Figuras y tablas del análisis + mirror pair analysis
- [ ] **T5.7** Sección 6 (Conclusions): Hallazgos + future work (combinación óptima 3 ejes)
- [ ] **T5.8** Revisar 12–15 páginas + formato CCIS Springer (splncs04)

## Phase 6: Submission
- [ ] **T6.1** Revisión cruzada entre autores
- [ ] **T6.2** Verificar deadlines en web oficial WEA 2026
- [ ] **T6.3** Subir a Microsoft CMT: https://cmt3.research.microsoft.com/WEA2026/

---

## Dependencies

```
T0.x (Diseño factorial) ✅
  └──> T1.x (Implementación R1-R8 en controllers) ✅
         └──> T2.x (Config JSON + BD)
                └──> T3.x (Ejecución)
                       └──> T4.x (Análisis)
                              └──> T5.x (Escritura)
                                     └──> T6.x (Submission)
```

## Rule Design: Additive Factorial Model

### Semantic Axes
- **Progress effect** (eje horizontal): cómo w cambia con iteration_progress
  - ↓: early=+1, mid=0, late=-1 (3L) | VE=+2, E=+1, Mi=0, La=-1, VLa=-2 (5L)
  - ↑: early=-1, mid=0, late=+1 (3L) | inversión de ↓
  - —: sin efecto (0 para todas las columnas)
- **Diversity effect** (eje vertical): cómo w reacciona a la diversidad
  - → (following): low=-1, med=0, high=+1 (3L) | VL=-2, L=-1, M=0, H=+1, VH=+2 (5L)
  - ← (compensating): low=+1, med=0, high=-1 (3L) | inversión de →
  - —: sin efecto (0 para todas las filas)

### Construction
```
Para cada celda (diversity_label, progress_label):
    score = progress_effect[progress_label] + diversity_effect[diversity_label]
    output_label = map_score_to_label(score)

3L mapping: score ≤ -1 → low, score = 0 → medium, score ≥ +1 → high
5L mapping: ≤ -3 → VL, {-2,-1} → L, 0 → M, {+1,+2} → H, ≥ +3 → VH
```

### Factorial Table
```
                    Div— (agnostic)  Div→ (following)  Div← (compensating)
Progress ↓ (H→L):  R1               R5                R6
Progress ↑ (L→H):  R2               R7                R8
Progress — (flat):  (trivial)        R3                R4
```

## Experimental Matrix Summary

| # | Config Name | Labels | Rule Set | Progress | Diversity | Input | Output |
|---|-------------|--------|----------|----------|-----------|-------|--------|
| 0 | PSO-STD | — | — | — | — | — | — |
| 1 | PSO-FCS-R1-3L | 3 | R1 | ↓ | — | I1 | O1 |
| 2 | PSO-FCS-R2-3L | 3 | R2 | ↑ | — | I1 | O1 |
| 3 | PSO-FCS-R3-3L | 3 | R3 | — | → | I1 | O1 |
| 4 | PSO-FCS-R4-3L | 3 | R4 | — | ← | I1 | O1 |
| 5 | PSO-FCS-R5-3L | 3 | R5 | ↓ | → | I1 | O1 |
| 6 | PSO-FCS-R6-3L | 3 | R6 | ↓ | ← | I1 | O1 |
| 7 | PSO-FCS-R7-3L | 3 | R7 | ↑ | → | I1 | O1 |
| 8 | PSO-FCS-R8-3L | 3 | R8 | ↑ | ← | I1 | O1 |
| 9 | PSO-FCS-R1-5L | 5 | R1 | ↓ | — | I1 | O1 |
| 10 | PSO-FCS-R2-5L | 5 | R2 | ↑ | — | I1 | O1 |
| 11 | PSO-FCS-R3-5L | 5 | R3 | — | → | I1 | O1 |
| 12 | PSO-FCS-R4-5L | 5 | R4 | — | ← | I1 | O1 |
| 13 | PSO-FCS-R5-5L | 5 | R5 | ↓ | → | I1 | O1 |
| 14 | PSO-FCS-R6-5L | 5 | R6 | ↓ | ← | I1 | O1 |
| 15 | PSO-FCS-R7-5L | 5 | R7 | ↑ | → | I1 | O1 |
| 16 | PSO-FCS-R8-5L | 5 | R8 | ↑ | ← | I1 | O1 |

**Total: 17 configs × 6 funciones × 31 runs = 3,162 experimentos**
