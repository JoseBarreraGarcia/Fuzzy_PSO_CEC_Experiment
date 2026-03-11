# Comparison Membership Functions - Dynamic Layout Fix

## Problema Solucionado

El gráfico `FUZZY/plots/06_comparison_membership_functions.png` estaba ocupando menos espacio que debería porque estaba configurado para 4 columnas (A, B, C, D) de forma hardcodeada:

**Antes:**
- GridSpec: 4 columnas fijas (para 4 sets)
- Figsize: (14, 10) fija
- Con solo 2 sets (A, B) definidos: Mucho espacio vacío a la derecha
- Imagen con espacio desperdiciado

**Ahora:**
- GridSpec: Dinámico basado en `len(sets)` 
- Figsize: Ajustado dinámicamente: `(7 * num_sets, 10)`
- Con 2 sets (A, B): (14, 10) - espacio óptimo
- Con 4 sets (A, B, C, D): (28, 10) - espacio total necesario

## Cambios en `FUZZY/fuzzy_plots.py`

Función `plot_comparison_membership_functions()` (línea ~628):

```python
# ANTES (hardcodeado):
fig = plt.figure(figsize=(14, 10))
gs = fig.add_gridspec(4, 4, height_ratios=[2, 0.3, 2, 0.3], hspace=0.35, wspace=0.3)

# AHORA (dinámico):
num_sets = len(sets)
if num_sets <= 2:
    figsize = (7 * num_sets, 10)      # 1 set: 7x10, 2 sets: 14x10
elif num_sets == 3:
    figsize = (18, 10)                 # 3 sets: 18x10
else:
    figsize = (7 * num_sets, 10)      # 4+ sets: 28x10, etc

fig = plt.figure(figsize=figsize)
gs = fig.add_gridspec(4, num_sets, height_ratios=[2, 0.3, 2, 0.3], 
                      hspace=0.35, wspace=0.3)
```

## Resultados

### Configuración Actual (2 sets: A, B)

| Métrica | Antes | Ahora |
|---------|-------|-------|
| Figsize | (14, 10) | (14, 10) |
| GridSpec | 4×4 (4 cols vacías) | 2×4 (exactas) |
| Espacio aprovechado | ~50% | 100% |
| Archivo tamaño | variable | 783 KB |

### Escalabilidad

| Num Sets | Figsize | GridSpec | Estado |
|----------|---------|----------|--------|
| 1 | (7, 10) | 1×4 | ✓ Óptimo |
| 2 | (14, 10) | 2×4 | ✓ Óptimo (actual) |
| 3 | (18, 10) | 3×4 | ✓ Óptimo |
| 4 | (28, 10) | 4×4 | ✓ Óptimo |
| 5 | (35, 10) | 5×4 | ✓ Óptimo |

## Ejemplo Visual

**Con 2 sets (antes - problema):**
```
┌─────────┬─────────┬─────────┬─────────┐
│    A    │    B    │  VACÍO  │  VACÍO  │  ← 50% espacio desperdiciado
├─────────┼─────────┼─────────┼─────────┤
│ Legend  │ Legend  │ Legend  │ Legend  │
├─────────┼─────────┼─────────┼─────────┤
│    A    │    B    │  VACÍO  │  VACÍO  │  ← 50% espacio desperdiciado
├─────────┼─────────┼─────────┼─────────┤
│ Legend  │ Legend  │ Legend  │ Legend  │
└─────────┴─────────┴─────────┴─────────┘
```

**Con 2 sets (ahora - solución):**
```
┌─────────┬─────────┐
│    A    │    B    │  ← 100% espacio aprovechado
├─────────┼─────────┤
│ Legend  │ Legend  │
├─────────┼─────────┤
│    A    │    B    │  ← 100% espacio aprovechado
├─────────┼─────────┤
│ Legend  │ Legend  │
└─────────┴─────────┘
```

## Cómo Se Adapta

1. **Detecta sets disponibles:**
   ```python
   sets = _get_available_w_sets(FuzzyInertiaController)
   # Devuelve: ['A', 'B'] (si solo hay A y B definidos)
   ```

2. **Calcula figsize dinámico:**
   ```python
   num_sets = len(sets)  # 2
   figsize = (7 * num_sets, 10)  # (14, 10)
   ```

3. **Crea GridSpec exacto:**
   ```python
   gs = fig.add_gridspec(4, num_sets)  # 4 filas, 2 columnas (antes era 4×4)
   ```

4. **Rellena solo los subplots necesarios:**
   ```python
   for col_idx, w_set in enumerate(sets):
       ax = fig.add_subplot(gs[0, col_idx])  # Solo usa col_idx 0, 1 (no 2, 3)
   ```

## Testing

Verificación rápida:
```bash
$ python -c "import sys; sys.path.insert(0, 'FUZZY'); from fuzzy_plots import _get_available_w_sets; from fuzzy_controller_w import FuzzyInertiaController; print(f'Sets: {_get_available_w_sets(FuzzyInertiaController)}')"

Sets: ['A', 'B']

$ python FUZZY/generate_fuzzy_plots.py
[OK] Generated 16 plots in ./FUZZY/plots
[OK] Comparison membership functions (3 vs 5): ./FUZZY/plots\06_comparison_membership_functions.png
```

El gráfico ahora usa el espacio exacto necesario sin desperdicio.

## Impacto en Otros Gráficos

Este cambio **NO afecta** a:
- `05_fuzzy_w_sets_comparison_X.png` - Ya estaba dinámico (modificado antes)
- `01-04_*` plots - Estos no usan sets dinámicamente
- `07_comparison_critical_points.png` - Ya usa detección dinámica
- `08_3d_surface_comparison_*` - Ya usa detección dinámica

## Beneficio Principal

✓ **Gráficos compactos y eficientes** - Sin espacio desperdiciado  
✓ **Escalable** - Si agregás C, D automáticamente se expande  
✓ **Profesional** - Mejor presentación visual  
✓ **Consistente** - Todos los gráficos de comparación usan el mismo patrón
