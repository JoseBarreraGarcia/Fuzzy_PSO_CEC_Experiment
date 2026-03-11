# Level 2 Analysis: Tres Niveles de Desagregación de Gráficos

## Resumen

El análisis **Level 2** (`level2_aggregated.py`) ahora genera gráficos en **TRES niveles jerárquicos** de desagregación, proporcionando tanto una vista agregada como visiones más detalladas para análisis específicos.

---

## Estructura de los 3 Niveles

### Nivel 1: Agregación Global (General Overview)

**Propósito**: Comparación de alto nivel sin desagregaciones.

**Gráficos generados**:

1. **boxplot_by_mh.png**
   - Compara los 5 MH (PSO, PSO_FCS:A/B/C/D) en todas las instancias y esquemas
   - Útil para: Ranking global de algoritmos
   - Cómo leer: Altura de la caja = rango de desempeño; línea roja = mediana

2. **percentile_by_mh.png**
   - Muestra percentiles 10%, 25%, 50%, 75%, 90% para cada MH
   - Útil para: Ver conservatismo vs agresividad de cada algoritmo
   - Cómo leer: Barras cercanas = algoritmo consistente; barras separadas = variable

3. **violinplot_by_mh.png**
   - Distribución completa de fitness para cada MH (forma de la curva)
   - Útil para: Detectar multimodalidad en desempeño
   - Cómo leer: Ancho en altura Y = cuántos resultados hay en ese rango

4. **boxplot_by_instance.png**
   - Compara dificultad relativa de las 3 instancias (SCP-41, SCP-51, SCP-61)
   - Útil para: Identificar instancias "fáciles" vs "difíciles"
   - Cómo leer: SCP-41 vs SCP-51 vs SCP-61 - qué instancia es mejor/peor para todos los MH

**Características**:
- Sin desagregación por MH individual
- Sin desagregación por esquema de binarización
- Visión global para papers y presentaciones

---

### Nivel 2: Desagregación Intermedia (POR INSTANCIA + BINARIZACIÓN)

**NUEVO**: Estos gráficos fueron AGREGADOS en esta iteración.

**Propósito**: Desagregar por cada combinación (Instancia, Esquema Binarización) para ver cómo se comportan los 5 MH en contextos específicos.

**Gráficos generados** (6 total):

1. **boxplot_41_S4_ELIT.png**
   - Compara PSO, PSO_FCS:A/B/C/D SOLO en instancia 41 con esquema S4-ELIT
   - Diferencia crítica: Muestra cuál MH es mejor en esta configuración específica

2. **boxplot_41_S4_STD.png**
   - Misma instancia 41, pero esquema S4-STD
   - Permite ver: ¿Cambia el MH ganador según el esquema de binarización?

3. **boxplot_51_S4_ELIT.png**
   - Instancia 51 (más fácil) con S4-ELIT
   - Patrón esperado: diferencias menores entre MH (la instancia es fácil para todos)

4. **boxplot_51_S4_STD.png**
   - Instancia 51 con S4-STD

5. **boxplot_61_S4_ELIT.png**
   - Instancia 61 (más difícil) con S4-ELIT
   - Patrón esperado: mayores diferencias entre MH (la instancia es difícil)

6. **boxplot_61_S4_STD.png**
   - Instancia 61 con S4-STD

**Características**:
- ✅ NUEVO NIVEL INTERMEDIO
- Muestra 5 MH comparados en contextos específicos
- Permite análisis de interacción: ¿MH × Instancia × Esquema?
- Ideal para secciones de "análisis por problema" en papers

**Preguntas que se pueden responder con estos gráficos**:
- ¿PSO_FCS:A es mejor que PSO en SCP-41 con S4-ELIT?
- ¿Existen diferencias entre S4-ELIT y S4-STD para la misma instancia?
- ¿Qué MH maneja mejor las instancias "difíciles" (61)?

---

### Nivel 3: Desagregación Máxima (Rankings Especializados)

**Módulo**: `level3_disaggregated.py` (ejecutable por separado)

**Propósito**: Tablas de rankings para análisis de especialización.

**Archivos generados**:

1. **instance_41_ranking.csv** / **instance_51_ranking.csv** / **instance_61_ranking.csv**
   - Ranking: ¿Cuál MH ganó en cada instancia?
   - Formato: MH | Best Fitness | Mean Fitness | Rank | Win Rate (%)

2. **config_PSO_FCS-A_S4-ELIT_A_ranking.csv** (x10 configuraciones)
   - Pregunta inversa: Para una configuración MH específica, ¿en qué instancias destaca?
   - Permite ver: PSO_FCS:A es mejor en [instancia 41, 51] pero no en [61]

3. **top_configs_global.csv**
   - Top 20 combinaciones (MH + esquema) globalmente

**Características**:
- Datos crudos (CSV), no gráficos
- Útil para análisis estadísticos post-hoc (ANOVA, Kruskal-Wallis)
- Especialización por algoritmo vs instancia

---

## Flujo de Análisis Recomendado

```
┌─────────────────────────────────────────────────────────┐
│  NIVEL 1: Overview Global (Agregado Total)              │
│  boxplot_by_mh.png, percentile_by_mh.png, etc.         │
│  Público: Introducción, decisiones iniciales            │
└──────────────┬──────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────┐
│  NIVEL 2: Desagregación Intermedia                       │
│  boxplot_41_S4_ELIT.png, boxplot_51_S4_STD.png, etc.   │
│  Público: "Análisis detallado por instancia"           │
│  Usuarios: Investigadores que necesitan precisión       │
└──────────────┬──────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────┐
│  NIVEL 3: Rankings Especializados                        │
│  instance_41_ranking.csv, config_PSO_FCS-A_ranking.csv │
│  Público: Apéndices, análisis estadísticos             │
│  Usuarios: Data scientists, análisis post-hoc           │
└─────────────────────────────────────────────────────────┘
```

---

## Ejemplos de Interpretación

### Ejemplo 1: Decisión de MH para SCP-41

**Pasos**:
1. Mirar `boxplot_41_S4_ELIT.png` (Nivel 2)
2. Observar: ¿Cuál MH tiene la mediana más baja (mejor)?
3. Validar en `instance_41_ranking.csv` (Nivel 3)

**Conclusión típica**: "PSO_FCS:B es 3% mejor que PSO en SCP-41"

---

### Ejemplo 2: ¿Importa el esquema de binarización?

**Pasos**:
1. Comparar `boxplot_41_S4_ELIT.png` vs `boxplot_41_S4_STD.png` (Nivel 2)
2. ¿Las medianas y rangos cambian significativamente?

**Conclusión típica**: "S4-ELIT produce mejores resultados (~5% mejor) que S4-STD"

---

### Ejemplo 3: Instancia difícil vs fácil

**Pasos**:
1. Observar `boxplot_41_S4_ELIT.png` (instancia fácil)
2. Observar `boxplot_61_S4_ELIT.png` (instancia difícil)
3. Comparar la altura de las cajas

**Conclusión típica**: "En SCP-61 (difícil) los MH tienen 2x más variabilidad; PSO_FCS:D sobresale"

---

## Uso en Papers

### Párrafo típico con Nivel 2:

> "Figura 3 muestra el desempeño de PSO y sus variantes PSO_FCS:A-D en tres instancias del Set Cover Problem con dos esquemas de binarización. En SCP-41 con S4-ELIT (Figura 3a), todos los algoritmos convergen a calidad similar, siendo PSO_FCS:B ligeramente superior. Sin embargo, en SCP-61 con S4-STD (Figura 3f, más difícil), las diferencias son apreciables: PSO_FCS:D mantiene mejor control de la diversidad, consiguiendo un rango menor de fitness."

---

## Tablas CSV Agregadas (Nivel 2)

El módulo `level2_aggregated.py` TAMBIÉN genera:

1. **descriptive_stats_by_mh.csv**
   ```
   MH          Count  Mean    Median  Min  Max   Std   CV%
   PSO         186    15878   11115   141  49355 17720 111.6%
   PSO_FCS:A   186    15874   11115   141  49355 17718 111.6%
   PSO_FCS:B   186    15873   11115   141  49355 17718 111.6%
   ...
   ```

2. **descriptive_stats_by_instance.csv**
   ```
   Instance  Optimum  Mean    Std   CV%
   41        429      15934   17512 109.8%
   51        253      15813   17943 113.5%
   61        138      15877   17712 111.5%
   ```

---

## Estructura del Directorio

```
Resultados/resumen/level2_aggregated/
├── descriptive_stats_by_mh.csv          [CSV con stats]
├── descriptive_stats_by_instance.csv    [CSV con stats]
└── plots/
    ├── boxplot_by_mh.png                [NIVEL 1]
    ├── percentile_by_mh.png             [NIVEL 1]
    ├── violinplot_by_mh.png             [NIVEL 1]
    ├── boxplot_by_instance.png          [NIVEL 1]
    ├── boxplot_41_S4_ELIT.png           [NIVEL 2]
    ├── boxplot_41_S4_STD.png            [NIVEL 2]
    ├── boxplot_51_S4_ELIT.png           [NIVEL 2]
    ├── boxplot_51_S4_STD.png            [NIVEL 2]
    ├── boxplot_61_S4_ELIT.png           [NIVEL 2]
    └── boxplot_61_S4_STD.png            [NIVEL 2]
```

**Total**: 10 gráficos PNG + 2 CSV = 12 archivos de salida

---

## Notas Técnicas

### Combinaciones generadas automáticamente

La función `plot_boxplot_by_instance_binarization()` itera sobre:
```python
combinations = df.groupby(['instancia_nombre', 'binarizacion']).size()
```

**Resultado**:
- 3 instancias (41, 51, 61)
- 2 esquemas (S4-ELIT, S4-STD)
- 3 × 2 = 6 combinaciones = 6 gráficos

Si en el futuro se agregan más instancias o esquemas, los gráficos se generarán automáticamente.

### Validación en código

```python
if 'binarizacion' not in df.columns or 'instancia_nombre' not in df.columns:
    print("[SKIP] Required columns not found")
    return
```

Esto evita errores si los datos están en formato diferente.

---

## Conclusión

El nuevo **Nivel 2 Intermedio** (6 gráficos boxplot por instancia+binarización) proporciona exactamente lo que pidió:

✅ **Más granular** que el agregado total  
✅ **Menos granular** que el análisis completo por cada run  
✅ **Ideal para papers**: Sección "Análisis por problema"  
✅ **Generado automáticamente** desde level1_raw_data.py

Ahora puede:
- Comparar cómo se comportan los 5 MH en cada contexto específico
- Identificar especialización (ej: PSO_FCS:A domina en SCP-41 pero no en SCP-61)
- Mostrar el impacto del esquema de binarización en la misma instancia

---

**Última actualización**: 2025-01-05  
**Módulo**: analysis_modules/level2_aggregated.py (Updated)
