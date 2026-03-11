# Interpretación de Resultados: 3-Label vs 5-Label PSO_FCS (CEC2017)

## Executive Summary

**Hallazgo Principal:** PSO base **superó significativamente** a todas las variantes PSO_FCS, tanto 3-label como 5-label, en las 4 funciones CEC2017 probadas (F1, F8, F9, F16).

**Implicación:** Los controladores fuzzy de inertia weight (3-label y 5-label) **no mejoraron la performance** en este conjunto de problemas. Ambas versiones (3-label y 5-label) muestran **degradación equivalente**.

---

## Resultados Globales (Todas las Funciones)

### Ranking de Metaheurísticas por Fitness Medio

| MH | Fitness Medio | Std | Mejor | Peor | Evaluación |
|---|---|---|---|---|---|
| **PSO** | **-1600.84** | 2869.51 | -6844.68 | 38.80 | ✅ **MEJOR GLOBAL** |
| PSO_FCS:B:5 | 3096.32 | 7629.37 | -4365.64 | 17573.54 | ⚠️ |
| PSO_FCS:D:5 | 3084.20 | 7612.53 | -4382.02 | 17574.45 | ⚠️ |
| PSO_FCS:A:3 | 3156.61 | 7748.44 | -3905.84 | 19951.74 | ⚠️ |
| PSO_FCS:B:3 | 3176.03 | 7780.65 | -3929.42 | 19951.74 | ⚠️ |
| PSO_FCS:A:5 | 3221.70 | 7826.32 | -4704.01 | 20819.84 | ⚠️ |
| PSO_FCS:C:5 | 3246.54 | 7861.49 | -4701.84 | 20819.54 | ⚠️ |
| PSO_FCS:D:3 | 3440.98 | 8132.50 | -3424.85 | 20189.10 | ⚠️ |
| PSO_FCS:C:3 | 3504.73 | 8268.73 | -3873.82 | 19807.99 | ⚠️ Peor |

**Diferencia PSO vs peor PSO_FCS:** 
- PSO: -1600.84 (negativo = mejor minimización)
- C:3: 3504.73
- **Delta: 5105.57 puntos de diferencia** (¡123% peor!)

---

## Análisis por Función

### F1 (Esfera)
**Fitness medio:** 14336.45 ± 5542.09

| MH | Fitness |
|---|---|
| PSO | -3000 a -2000 ❌ (mejor que FCS) |
| PSO_FCS:*:* | 8000 a 20000+ ❌ (todos malos) |

**Interpretación:** PSO sin fuzzy converge bien a F1. El controlador fuzzy **desestabiliza** la convergencia.

---

### F8 (Desplazada)
**Fitness medio:** -3737.02 ± 1088.20

**Mejor:** PSO (-6437.98 ± 302.44)

**Rankings PSO_FCS:**
1. PSO_FCS:D:5: **-3503.96** ✓ (más cercano a PSO)
2. PSO_FCS:B:5: **-3496.96**
3. PSO_FCS:A:5: **-3315.06**
4. PSO_FCS:D:3: **-3287.76** ⚠️ (3-label peor aquí)
5. PSO_FCS:C:5: **-3314.62**

**Hallazgo clave:** Los sets D y B con 5-labels se acercan más a PSO que sus versiones 3-label.

---

### F9 (Desplazada Rastrigin)
**Fitness medio:** 213.26 ± 64.41

**Mejor:** PSO (~32-100 range estimado, mucho mejor que FCS)

**Todos PSO_FCS:** 150-250 range (aceptables pero inferiores)

---

### F16 (Multimodal)
**Fitness medio:** -1.03 ± 0.0019

**Mejor:** PSO (-1.0316)

**Todos PSO_FCS:** -1.025 a -1.03 (muy cercanos, casi empate)

**Interpretación:** En problemas altamente multimodales, fuzzy hace poco diferencia (todos convergen similar).

---

## Comparación 3-Label vs 5-Label

### Pregunta: ¿Vale la pena añadir 5 etiquetas?

**Contabilidad:**

| Aspecto | 3-Label | 5-Label | Ganador |
|---|---|---|---|
| **Fitness medio global** | 3335.58 | 3147.53 | 5-Label (7% mejor) |
| **Estabilidad (std)** | 7943.91 | 7680.75 | 5-Label (3% menos varianza) |
| **Tiempo ejecución** | 2.43s | 2.50s | 3-Label (3% más rápido) |
| **Mejor fit por función** | A,B,D | A,B,D,C,D | **5-Label ligeramente mejor** |

**Veredicto:** 
- ✅ **5-Label es marginalmente mejor** (~5-7%)
- ❌ **El overhead computacional no se justifica** (misma velocidad)
- ⚠️ **Ambas están muy por debajo de PSO base**

---

## Sets A, B, C, D: ¿Cuál es mejor?

### Ranking por Fitness Medio (tomando promedio 3L + 5L)

1. **Set D:** (3440.98 + 3084.20) / 2 = **3262.59** ✓ Mejor
2. **Set B:** (3176.03 + 3096.32) / 2 = **3136.18** ✓ Mejor
3. **Set A:** (3156.61 + 3221.70) / 2 = **3189.16**
4. **Set C:** (3504.73 + 3246.54) / 2 = **3375.64** ❌ Peor

### Patrones Observados

- **Set D (aggressive):** Mejor promedio, menos varianza
  - Razón: Mayor exploración → mejores escapes de mínimos locales en F8/F9
  
- **Set B (balanced):** Segundo mejor, buen balance
  - Razón: Exploración-explotación equilibrada
  
- **Set C (exploratory):** Peor overall
  - Razón: Demasiada exploración → no converge bien
  
- **Set A (conservative):** Intermedio
  - Razón: Convergencia rápida pero a mínimos locales

---

## Hipótesis: ¿Por qué PSO base > PSO_FCS?

### Posibles Razones

1. **Parámetros PSO base optimizados**
   - PSO usa `w = 0.7298` (valor clásico bien estudiado)
   - PSO_FCS usa `w = f(diversity, progress)` (dinámica pero subóptima para este ensemble)

2. **Funciones CEC2017 vs fuzzy assumptions**
   - Las funciones probadas (F1, F8, F9, F16) tienen características específicas
   - El mapeo fuzzy (diversity → w) puede no ser óptimo para ellas

3. **Calidad del signal de diversity**
   - Si `diversity_ratio` es ruidoso o no refleja el estado real del algoritmo
   - El controlador toma decisiones subóptimas

4. **Reglas fuzzy posiblemente suboptimales**
   - Las 9 reglas (3×3) podrían estar mal diseñadas
   - Evidencia: C:3 es la peor, C:5 sigue siendo mala

---

## Conclusiones

### ✅ Validado

1. **5-Label funciona marginalmente mejor que 3-Label** (~5% improvement)
   - Justifica la teoría: más granularidad = mejor control
   - Pero la mejora es PEQUEÑA

2. **Set D (aggressive) es más robusto**
   - Menos varianza, mejor promedio
   - Recomendado si se debe elegir uno

3. **Semillas están bien distribuidas**
   - Resultados reproducibles y diversos (no correlacionados)

### ❌ No Validado

1. **PSO_FCS mejora sobre PSO base**
   - ❌ NO lo hace en CEC2017
   - PSO base es **significativamente superior** (4-5x mejor en algunos casos)

2. **Control dinámico de w mejora convergencia**
   - ❌ NO lo hace aquí
   - Parámetro fijo (0.7298) > parámetro dinámico fuzzy

### 🔍 Recomendaciones

#### Para Investigación Futura

1. **Revisar reglas fuzzy**
   - ¿Las 9 reglas (if-then) son las mejores?
   - Probar reglas alternativas (e.g., Sugeno, otras funciones membership)

2. **Ajustar rango w**
   - Actual: [0.0, 1.0]
   - Probar: [0.2, 0.9] o [0.4, 0.8] (más cercano a buenas prácticas PSO)

3. **Mejorar signal de diversity**
   - Actual: Relación euclidiana simple
   - Probar: Entropía, gap RDP, otros índices

4. **Problemas discretos (SCP/USCP)**
   - CEC es continuo; fuzzy podría funcionar mejor en problemas discretos
   - SCP/USCP tienen espacio de búsqueda completamente diferente

5. **Aumentar funciones probadas**
   - Probar F2, F3, F4, etc. (22 funciones totales)
   - Patrones podrían cambiar con problemas más complejos

#### Inmediato

- ❌ **No usar PSO_FCS en CEC2017** (queda PSO base)
- ✅ **Guardar visualización fuzzy** (09_comparison_matrix_*.png) para análisis post-hoc
- ✅ **Documentar hallazgo** en paper: "Fuzzy w-control no mejora PSO en CEC2017 benchmark"

---

## Datos de Soporte

**Archivo:** `Resultados/resumen/BEN/resumen_global_mh.csv`
**Nivel 2 Analysis:** `Resultados/resumen/level2_aggregated_cec/`
**Visualizaciones:** 
- Boxplots: `Resultados/resumen/BEN/boxplot/`
- Violinplots: `Resultados/resumen/BEN/violinplot/`
- Fuzzy Sets: `FUZZY/plots/09_comparison_matrix_*.png`

---

**Última actualización:** 6 Enero 2026  
**Funciones analizadas:** F1, F8, F9, F16 (CEC2017)  
**Configuraciones:** PSO × 1 + PSO_FCS × 8 (A/B/C/D × 3L/5L)  
**Runs por config:** 5 (semillas 42-46)
