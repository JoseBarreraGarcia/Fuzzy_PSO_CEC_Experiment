# Quick Reference: Fuzzy Dynamic Grid Update

## ¿Qué cambió?

El script `FUZZY/fuzzy_plots.py` ahora **se adapta automáticamente** al número de fuzzy sets disponibles en lugar de estar hardcodeado a una grilla 2×2.

## Status Actual

```
Detected: 2 available sets (A, B)
Grid: 1 row × 2 columns (optimal, sin subplots vacíos)
Plots generated successfully:
  ✓ 05_fuzzy_w_sets_comparison_3labels.png (279 KB)
  ✓ 05_fuzzy_w_sets_comparison_5labels.png (365 KB)
```

## Ejemplo: Si quieres agregar Sets C y D

### 1. En `FUZZY/fuzzy_controller_w.py`, descomentar C y D:

```python
W_SETS = {
    "A": {...},
    "B": {...},
    "C": {        # ← DESCOMENTAR
        "high":   (0.60, 0.75, 0.90),
        "medium": (0.35, 0.5, 0.65),
        "low":    (0.10, 0.25, 0.40),
    },
    "D": {        # ← DESCOMENTAR
        "high":   (0.60, 0.80, 0.80),
        "medium": (0.35, 0.5, 0.65),
        "low":    (0.20, 0.20, 0.40),
    },
}
```

### 2. Ejecutar plots:

```bash
python FUZZY/fuzzy_plots.py
# O directamente:
python -c "from FUZZY.fuzzy_plots import plot_all_w_sets_comparison; plot_all_w_sets_comparison()"
```

### 3. ¡Listo!

El script automáticamente:
- Detecta 4 sets disponibles (A, B, C, D)
- Calcula grid óptimo: **2 rows × 2 columns**
- Regenera las imágenes sin cambios de código

## Grid Adaptation Table

| Num Sets | Grid | Figsize | Uso |
|----------|------|---------|-----|
| 1 | 1×1 | (7, 5) | Un solo set |
| 2 | 1×2 | (14, 5) | A, B (actual) |
| 3 | 1×3 | (18, 5) | A, B, C |
| 4 | 2×2 | (14, 10) | A, B, C, D |
| 5 | 2×3 | (18, 10) | A, B, C, D, E |
| 6+ | √n×√n | variable | 6 o más sets |

## Test Script

Para verificar que todo funciona:

```bash
python test_fuzzy_dynamic_grid.py
```

Verás un reporte detallado del sistema.

## Archivos Afectados

- ✅ `FUZZY/fuzzy_plots.py` - Actualizado con funciones helper dinámicas
- ✅ `test_fuzzy_dynamic_grid.py` - Script de prueba (nuevo)
- ✅ `documentation/FUZZY_DYNAMIC_GRID_UPDATE.md` - Documentación detallada (nuevo)

---

**TL;DR:** Ahora los gráficos de fuzzy sets se adaptan automáticamente. No hay más subplots vacíos, y puedes agregar/quitar sets sin tocar código Python.
