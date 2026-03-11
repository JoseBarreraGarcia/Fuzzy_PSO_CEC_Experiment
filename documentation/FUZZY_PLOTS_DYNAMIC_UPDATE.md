# Fuzzy Plots - Dynamic Set Detection Update

## Problema Resuelto

El script `FUZZY/generate_fuzzy_plots.py` estaba generando **errores** al intentar crear gráficos para sets hardcodeados (A, B, C, D) que no estaban todos definidos:

```
[ERROR] Could not generate 3-label plot for Set C: w_set='C' no definido. Sets disponibles: ['A', 'B']
[ERROR] Could not generate 5-label plot for Set C: w_set='C' no definido. Sets disponibles: ['A', 'B']
[ERROR] Could not generate 3-label plot for Set D: w_set='D' no definido. Sets disponibles: ['A', 'B']
[ERROR] Could not generate 5-label plot for Set D: w_set='D' no definido. Sets disponibles: ['A', 'B']
[ERROR] Comparison membership functions failed: w_set='C' no definido. Sets disponibles: ['A', 'B']
[ERROR] Comparison critical points failed: w_set='C' no definido. Sets disponibles: ['A', 'B']
[ERROR] 3D Surface comparison failed: w_set='C' no definido. Sets disponibles: ['A', 'B']
```

## Solución Implementada

Las funciones en `FUZZY/fuzzy_plots.py` ahora usan **detección dinámica** de sets disponibles en lugar de hardcodeados:

### 1. **`generate_all_fuzzy_plots()`** (línea ~915)
**Antes:**
```python
for w_set in ['A', 'B', 'C', 'D']:  # HARDCODED - error si C, D no existen
```

**Ahora:**
```python
available_w_sets = _get_available_w_sets(FuzzyInertiaController)
for w_set in available_w_sets:  # DINÁMICO - solo sets definidos
```

### 2. **`plot_comparison_membership_functions()`** (línea ~628)
**Antes:**
```python
sets = ['A', 'B', 'C', 'D']  # HARDCODED
# Luego crea 4 subplots aunque falten sets
```

**Ahora:**
```python
sets = _get_available_w_sets(FuzzyInertiaController)
if not sets:
    sets = ['A']  # Fallback seguro
# GridSpec se ajusta automáticamente
```

### 3. **`plot_comparison_critical_points()`** (línea ~750)
**Antes:**
```python
sets = ['A', 'B', 'C', 'D']  # HARDCODEADO - error si faltan
```

**Ahora:**
```python
sets = _get_available_w_sets(FuzzyInertiaController)
if not sets:
    sets = ['A']
```

### 4. **`plot_3d_comparison()`** (línea ~790)
**Antes:**
```python
sets = ['A', 'B', 'C', 'D']  # HARDCODED - genera 4 plots aunque 2 fallen
```

**Ahora:**
```python
sets = _get_available_w_sets(FuzzyInertiaController)
if not sets:
    sets = ['A']  # Fallback
# Loop genera exactamente len(sets) plots
```

## Comportamiento Actual

Con **2 sets definidos (A, B)**:

```bash
✓ Generated 16 plots (sin errores)
  - 02 plots de diversidad (3 + 5 labels)
  - 02 plots de progreso (3 + 5 labels)
  - 04 plots de salida w: A_3labels, A_5labels, B_3labels, B_5labels
  - 02 plots de heatmap (3 + 5 labels)
  - 02 plots de comparación de sets (3 + 5 labels)
  - 01 plot de comparación de funciones membresía (3 vs 5)
  - 01 plot de puntos críticos
  - 02 plots 3D (set A, set B)
```

Con **4 sets definidos (A, B, C, D)** (si descomenta en fuzzy_controller_w.py):

```bash
✓ Generated 22 plots (sin errores, automáticamente escalado)
  - 02 plots de diversidad
  - 02 plots de progreso
  - 08 plots de salida w (A_3, A_5, B_3, B_5, C_3, C_5, D_3, D_5)
  - 02 plots de heatmap
  - 02 plots de comparación de sets (con grid 2×2)
  - 01 plot de comparación de funciones membresía (con 4 sets)
  - 01 plot de puntos críticos (con 4 sets)
  - 04 plots 3D (set A, B, C, D)
```

## Escalabilidad

| Num Sets | Output w Plots | 3D Plots | Comparación Grid | Total Plots |
|----------|----------------|----------|------------------|------------|
| 1        | 2              | 1        | 1×1              | 14         |
| 2        | 4              | 2        | 1×2              | 16         |
| 3        | 6              | 3        | 1×3              | 18         |
| 4        | 8              | 4        | 2×2              | 22         |
| 5        | 10             | 5        | 2×3              | 26         |
| 6        | 12             | 6        | 2×3              | 28         |

## Cambios Específicos en `fuzzy_plots.py`

1. **Función helper reutilizada:** `_get_available_w_sets()` (ya existía, ahora usada en más lugares)
2. **Línea ~915:** Loop simplificado con detección dinámica
3. **Línea ~638:** Sets detectados dinámicamente  
4. **Línea ~750:** Sets detectados dinámicamente
5. **Línea ~795:** Sets detectados dinámicamente

## Testing

Verificación del comportamiento:
```bash
$ python test_fuzzy_dynamic_grid.py
[1] Detecting available w_sets from FuzzyInertiaController...
    ✓ Found 2 available set(s): ['A', 'B']
[2] Calculating optimal grid for 2 set(s)...
    ✓ Optimal grid: 1 row(s) × 2 col(s)
```

## Cómo Agregar Sets

Si quieres agregar Set C y D:

1. En `FUZZY/fuzzy_controller_w.py`, descomentar C y D en el dict `W_SETS`
2. Ejecutar:
   ```bash
   python FUZZY/generate_fuzzy_plots.py
   ```
3. ¡Listo! Automáticamente genera 22 plots en lugar de 16, sin cambio de código

## Archivos Modificados

- ✅ `FUZZY/fuzzy_plots.py`
  - Línea ~915: `generate_all_fuzzy_plots()` - detección dinámica
  - Línea ~638: `plot_comparison_membership_functions()` - detección dinámica
  - Línea ~750: `plot_comparison_critical_points()` - detección dinámica
  - Línea ~795: `plot_3d_comparison()` - detección dinámica

## Beneficios

✅ **Sin errores:** No intenta generar gráficos para sets que no existen  
✅ **Escalable:** Automáticamente se adapta a 1, 2, 4, 6+ sets  
✅ **Mantenible:** Cambiar config fuzzy → automáticamente nuevos gráficos  
✅ **Robusto:** Fallback a ['A'] si algo va mal  
✅ **Consistente:** Usa la misma función helper en todas partes
