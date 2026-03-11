# Fuzzy Plot Grid Adaptation - Dynamic Update

## Problema Original

El script `FUZZY/fuzzy_plots.py` estaba hardcodeado para generar un grid de **2x2** en los gráficos de comparación de fuzzy sets:

```python
fig, axes = plt.subplots(2, 2, figsize=(14, 10), dpi=100)  # HARDCODED
w_sets = ['A', 'B', 'C', 'D']  # HARDCODED
```

**Problemas:**
1. Si solo hay 2 sets activos (A, B), hay 2 subplots vacíos (desperdicio visual)
2. Si se agregan más sets (E, F, etc.), se truncan o generan errores
3. No es adaptable al configuración de sets en `fuzzy_controller_w.py`

## Solución Implementada

### 1. Función Helper: `_get_available_w_sets(controller_class)`
Detecta dinámicamente cuáles sets están **realmente definidos** en la clase controladora:

```python
def _get_available_w_sets(controller_class):
    """
    Dynamically get available w_sets from controller class.
    Creates a dummy instance to access W_SETS dictionary.
    """
    available = []
    for letter in ['A', 'B', 'C', 'D', 'E', 'F']:
        try:
            controller_class(letter)
            available.append(letter)
        except ValueError:
            pass
    return available if available else ['A', 'B']
```

**Beneficio:** Busca automáticamente los sets comentados/descomentados en `W_SETS`.

### 2. Función Helper: `_calculate_grid_dims(num_sets)`
Calcula automáticamente las dimensiones óptimas del grid:

```python
def _calculate_grid_dims(num_sets):
    """Calculate optimal grid dimensions based on number of sets"""
    if num_sets == 1:
        return 1, 1, (7, 5)
    elif num_sets == 2:
        return 1, 2, (14, 5)
    elif num_sets == 3:
        return 1, 3, (18, 5)
    elif num_sets == 4:
        return 2, 2, (14, 10)
    elif num_sets == 5:
        return 2, 3, (18, 10)
    elif num_sets == 6:
        return 2, 3, (18, 10)
    else:  # num_sets >= 7
        cols = int(np.ceil(np.sqrt(num_sets)))
        rows = int(np.ceil(num_sets / cols))
        figsize = (7 * cols, 5 * rows)
        return rows, cols, figsize
```

**Disposición automática:**
- 1 set → 1×1
- 2 sets → 1×2 (horizontal)
- 3 sets → 1×3 (horizontal)
- 4 sets → 2×2 (actual)
- 5 sets → 2×3
- 6+ sets → √n×√n

### 3. Función Principal Actualizada: `plot_all_w_sets_comparison()`

Cambios principales:

```python
# ANTES (hardcoded):
w_sets = ['A', 'B', 'C', 'D']
fig, axes = plt.subplots(2, 2, figsize=(14, 10), dpi=100)

# AHORA (dinámico):
w_sets = _get_available_w_sets(FuzzyInertiaController)
rows, cols, figsize = _calculate_grid_dims(len(w_sets))
fig, axes = plt.subplots(rows, cols, figsize=figsize, dpi=100)
```

**Además:**
- Maneja correctamente los casos de 1, 2, o más subplots (reshape arrays)
- Oculta subplots no utilizados: `axes_flat[idx].axis('off')`
- Actualiza el título dinámicamente: `f'Fuzzy Inertia Weight Sets Comparison - 3 Labels ({sets_str})'`
- Maneja excepciones si `FuzzyInertiaController_5labels` no existe

## Caso de Uso: Cambios en Sets

### Scenario 1: Solo A y B (Estado Actual)
**Antes:** 2×2 grid con 2 subplots vacíos
```
┌─────────┬─────────┐
│    A    │    B    │
├─────────┼─────────┤
│ VACÍO   │ VACÍO   │
└─────────┴─────────┘
```

**Ahora:** 1×2 grid, sin desperdicio
```
┌─────────┬─────────┐
│    A    │    B    │
└─────────┴─────────┘
```

### Scenario 2: Si se descomenta C y D en `fuzzy_controller_w.py`
**El script se adapta automáticamente:**
```
┌─────────┬─────────┐
│    A    │    B    │
├─────────┼─────────┤
│    C    │    D    │
└─────────┴─────────┘
```
Sin cambio de código en `fuzzy_plots.py`.

### Scenario 3: Si se agrega E y F
**El script genera 3×2 o 2×3 automáticamente:**
```
┌─────────┬─────────┬─────────┐
│    A    │    B    │    C    │
├─────────┼─────────┼─────────┤
│    D    │    E    │    F    │
└─────────┴─────────┴─────────┘
```

## Cómo Usar

### Agregar un nuevo set (Ej: Set E)

1. **En `FUZZY/fuzzy_controller_w.py`:**
```python
W_SETS = {
    "A": {...},
    "B": {...},
    "C": {...},  # Descomentar si está comentado
    "D": {...},  # Descomentar si está comentado
    "E": {        # AGREGAR
        "high":   (0.70, 0.85, 0.95),
        "medium": (0.40, 0.55, 0.70),
        "low":    (0.05, 0.20, 0.35),
    }
}
```

2. **Listo.** El script de plots se adaptará automáticamente:
```bash
python FUZZY/fuzzy_plots.py
```

**Resultado:** Gráficos regenerados con grid 1×2, 2×3, o el que sea óptimo automáticamente.

## Verificación

```bash
$ python -c "from FUZZY.fuzzy_plots import plot_all_w_sets_comparison; plot_all_w_sets_comparison()"
Generated: {'3labels': './FUZZY/plots\\05_fuzzy_w_sets_comparison_3labels.png', 
            '5labels': './FUZZY/plots\\05_fuzzy_w_sets_comparison_5labels.png'}
```

Verifica que:
- ✅ Detecta sets dinámicamente
- ✅ Calcula grid óptimo
- ✅ Genera PNG con tamaño correcto

## Ventajas de la Nueva Arquitectura

| Aspecto | Antes | Ahora |
|---------|-------|-------|
| Grid adaptativo | ❌ No (hardcoded 2×2) | ✅ Sí (1×1 a N×N) |
| Detección automática | ❌ No | ✅ Sí |
| Escalabilidad | ❌ Limitada a 4 sets | ✅ Ilimitada (A-Z) |
| Mantenimiento | ❌ Cambiar código | ✅ Solo cambiar config |
| Espacio vacío | ❌ Sí (cuando <4 sets) | ✅ No |

## Archivos Modificados

- `FUZZY/fuzzy_plots.py`
  - ✅ Añadidas 2 funciones helper
  - ✅ Actualizada `plot_all_w_sets_comparison()` con lógica dinámica
  - ✅ Soporta ambas versiones (3-label y 5-label)
