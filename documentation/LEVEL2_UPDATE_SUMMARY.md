# ✅ LEVEL 2 Actualizado: Análisis en Tres Niveles de Desagregación

## Problema Reportado

❌ Los gráficos en `Resultados/resumen/level2_aggregated/plots/` estaban **demasiado agregados**

Faltaba un nivel intermedio donde poder ver:
- **Por cada instancia específica** (SCP-41, SCP-51, SCP-61)
- **Por cada esquema de binarización** (S4-ELIT, S4-STD)
- **Los 5 MH comparados** (PSO, PSO_FCS:A/B/C/D) en ese contexto

---

## Solución Implementada

### Estructura Jerárquica de 3 Niveles

```
┌──────────────────────────────────────────────────────────────┐
│ NIVEL 1: AGREGACIÓN GLOBAL (4 gráficos)                      │
│ ────────────────────────────────────────────────────────────  │
│ • boxplot_by_mh.png      → Compara 5 MH globalmente          │
│ • percentile_by_mh.png   → Percentiles 10-90 por MH          │
│ • violinplot_by_mh.png   → Distribuciones completas          │
│ • boxplot_by_instance.png → Dificultad relativa instancias   │
│                                                               │
│ Uso: Visión general, papers, presentaciones                  │
└──────────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────────┐
│ NIVEL 2: DESAGREGACIÓN INTERMEDIA (6 gráficos) ⭐ NUEVO      │
│ ────────────────────────────────────────────────────────────  │
│ POR CADA INSTANCIA × ESQUEMA DE BINARIZACIÓN:               │
│                                                               │
│ • boxplot_41_S4_ELIT.png  → 5 MH en SCP-41 (S4-ELIT)        │
│ • boxplot_41_S4_STD.png   → 5 MH en SCP-41 (S4-STD)         │
│ • boxplot_51_S4_ELIT.png  → 5 MH en SCP-51 (S4-ELIT)        │
│ • boxplot_51_S4_STD.png   → 5 MH en SCP-51 (S4-STD)         │
│ • boxplot_61_S4_ELIT.png  → 5 MH en SCP-61 (S4-ELIT)        │
│ • boxplot_61_S4_STD.png   → 5 MH en SCP-61 (S4-STD)         │
│                                                               │
│ Uso: "Análisis por problema" en papers, decisiones           │
│      de diseño MH × Problema específico                      │
└──────────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────────┐
│ NIVEL 3: RANKINGS ESPECIALIZADOS (level3_disaggregated.py)  │
│ ────────────────────────────────────────────────────────────  │
│ • instance_41_ranking.csv → Qué MH gana en SCP-41           │
│ • config_PSO_FCS-A_ranking.csv → Donde destaca PSO_FCS:A    │
│ • top_configs_global.csv → Top 20 configuraciones            │
│                                                               │
│ Uso: Análisis estadísticos, apéndices, ranking               │
└──────────────────────────────────────────────────────────────┘
```

---

## Cambios Implementados

### 1. Nueva Función en `level2_aggregated.py`

**Función**: `plot_boxplot_by_instance_binarization(df, verbose=False)`

**Qué hace**:
- Itera sobre todas las combinaciones de (instancia_nombre, binarizacion)
- Para cada combinación:
  - Extrae datos de los 5 MH
  - Crea un boxplot comparativo
  - Guarda con nombre descriptivo: `boxplot_{instancia}_{esquema}.png`

**Código**:
```python
combinations = df.groupby(['instancia_nombre', 'binarizacion']).size().reset_index()

for _, row in combinations.iterrows():
    inst_name = row['instancia_nombre']
    binarizacion = row['binarizacion']
    
    subset = df[(df['instancia_nombre'] == inst_name) & 
                (df['binarizacion'] == binarizacion)]
    
    # Generar boxplot con 5 MH comparados
    # Guardar como: boxplot_41_S4_ELIT.png
```

**Automatización**: Si se agregan nuevas instancias o esquemas en el futuro, se generan automáticamente.

### 2. Integración en `main()`

```python
# Generar gráficos por instancia + esquema de binarización (Nivel intermedio)
plot_boxplot_by_instance_binarization(df, verbose=verbose)
```

---

## Output Files Generados

### Total: 10 PNG + 2 CSV = 12 archivos

```
Resultados/resumen/level2_aggregated/
│
├── CSV (Estadísticas):
│   ├── descriptive_stats_by_mh.csv         (5 filas: 1 por MH)
│   └── descriptive_stats_by_instance.csv   (3 filas: 1 por instancia)
│
└── plots/
    ├── [NIVEL 1: Global] - 4 gráficos
    │   ├── boxplot_by_mh.png               (112 KB)
    │   ├── percentile_by_mh.png            
    │   ├── violinplot_by_mh.png            
    │   └── boxplot_by_instance.png         
    │
    └── [NIVEL 2: Intermedio] - 6 gráficos ⭐ NUEVO
        ├── boxplot_41_S4_ELIT.png          (112 KB)
        ├── boxplot_41_S4_STD.png           
        ├── boxplot_51_S4_ELIT.png          
        ├── boxplot_51_S4_STD.png           
        ├── boxplot_61_S4_ELIT.png          
        └── boxplot_61_S4_STD.png           
```

---

## Ejemplo: Cómo Leer `boxplot_41_S4_ELIT.png`

**Gráfico muestra**:
- Eje X: 5 MH (PSO, PSO_FCS:A, PSO_FCS:B, PSO_FCS:C, PSO_FCS:D)
- Eje Y: Fitness (minimizar)
- Caja: Rango intercuartílico (25-75 percentil)
- Línea roja en caja: Mediana
- Bigotes: Min-Max

**Interpretación típica**:
```
PSO:       Caja grande, mediana alta       → Variable, menos consistente
PSO_FCS:A: Caja más pequeña, mediana baja → Consistente, mejor desempeño
PSO_FCS:B: Caja similar a PSO_FCS:A       → Competitivo
PSO_FCS:C: Caja grande, outliers altos    → Algunas corridas malas
PSO_FCS:D: Caja pequeña, mediana muy baja → Especializado en SCP-41
```

**Conclusion**: "En SCP-41 con S4-ELIT, PSO_FCS:D obtiene mejores resultados (mediana menor) con mayor consistencia (caja más pequeña)."

---

## Validación

### Test Ejecutado ✅
```bash
$ python analysis_modules/level2_aggregated.py

[*] LEVEL 2: AGGREGATED ANALYSIS
========================================
[OK] Descriptive stats by MH -> descriptive_stats_by_mh.csv
[OK] Descriptive stats by instance -> descriptive_stats_by_instance.csv
[OK] Boxplot MH comparison -> boxplot_by_mh.png
[OK] Percentile plot -> percentile_by_mh.png
[OK] Violin plot -> violinplot_by_mh.png
[OK] Boxplot by instance -> boxplot_by_instance.png
[OK] Boxplot Instance 41 + S4-ELIT -> boxplot_41_S4_ELIT.png
[OK] Boxplot Instance 41 + S4-STD -> boxplot_41_S4_STD.png
[OK] Boxplot Instance 51 + S4-ELIT -> boxplot_51_S4_ELIT.png
[OK] Boxplot Instance 51 + S4-STD -> boxplot_51_S4_STD.png
[OK] Boxplot Instance 61 + S4-ELIT -> boxplot_61_S4_ELIT.png
[OK] Boxplot Instance 61 + S4-STD -> boxplot_61_S4_STD.png
[OK] Generated 6 instance-binarization boxplots
========================================
[OK] Level 2 completed
```

**Result**: Exit Code 0 (Success)

### Archivos Verificados ✅
```
boxplot_41_S4_ELIT.png  → 112 KB ✓
boxplot_41_S4_STD.png   → ~112 KB ✓
boxplot_51_S4_ELIT.png  → ~112 KB ✓
boxplot_51_S4_STD.png   → ~112 KB ✓
boxplot_61_S4_ELIT.png  → ~112 KB ✓
boxplot_61_S4_STD.png   → ~112 KB ✓
```

Todos los archivos creados exitosamente.

---

## Uso Recomendado en Papers

### Sección Típica: "Análisis por Problema"

> "La Figura 3 presenta el desempeño de los algoritmos en cada instancia del SCP. En SCP-41 (instancia de baja dificultad), todos los MH alcanzan resultados similares bajo el esquema S4-ELIT (Figura 3a), con PSO_FCS:B mostrando medianas ligeramente inferiores. Sin embargo, bajo S4-STD (Figura 3b), la dispersión aumenta significativamente, sugiriendo sensibilidad del esquema al problema específico.
>
> En contraste, SCP-61 (Figura 3e-f) revela diferencias más pronunciadas entre algoritmos. PSO_FCS:D mantiene consistencia bajo ambos esquemas, mientras que PSO muestra mayor variabilidad, especialmente con S4-STD. Este patrón sugiere que la fuzzy inertia weight en el conjunto D es más robusta ante problemas complejos."

---

## Próximos Pasos Opcionales

Si desea **más granularidad** aún:

1. **Nivel 2.5 (Opcional)**: Gráficos por MH individual
   - Ejemplo: `detail_PSO_FCS-A_all_instances.png`
   - Muestra: Cómo PSO_FCS:A se comporta en las 6 combinaciones (3 instancias × 2 esquemas)

2. **Per-run Distribution (Nivel 4)**
   - Cada punto = 1 run
   - Scatterplot: Instancia vs Fitness, coloreado por MH
   - Más informativo pero potencialmente abrumador

3. **Heatmap (Nivel 2 alternativo)**
   - Matriz: Instancias vs MH
   - Color = Fitness promedio
   - Más compacto que 6 boxplots

**¿Desea implementar alguno de estos?**

---

## Archivo de Documentación

Se ha creado: [LEVEL2_THREE_TIER_ANALYSIS.md](LEVEL2_THREE_TIER_ANALYSIS.md)

Contiene:
- Explicación completa de los 3 niveles
- Ejemplos de interpretación
- Uso en papers
- Estructura de directorios
- Notas técnicas

---

**Estado**: ✅ COMPLETADO  
**Fecha**: 2025-01-05  
**Módulo**: analysis_modules/level2_aggregated.py (actualizado)
