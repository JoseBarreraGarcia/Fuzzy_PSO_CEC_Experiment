# Tabla CSV de Búsqueda Fuzzy - COMPLETADA

## Resumen de lo Entregado

Se ha creado exitosamente una **tabla de búsqueda CSV** del controlador fuzzy en la carpeta FUZZY.

### Archivos Creados

1. **`FUZZY/fuzzy_lookup_table.csv`** (7.4 KB)
   - Tabla con 121 filas de datos
   - 7 columnas: Diversity, Progress, w_set_A, w_set_B, w_set_C, w_set_D, Activated_Rules
   - Formato: CSV estándar (UTF-8)
   - Listo para abrir en Excel, Python, o cualquier herramienta de análisis

2. **`FUZZY/generate_fuzzy_lookup_table.py`** (Script generador)
   - Crea automáticamente la tabla CSV
   - Parametrizable (número de muestras)
   - Uso: `python generate_fuzzy_lookup_table.py [n_samples]`

3. **`FUZZY/LOOKUP_TABLE_README.md`** (Documentación)
   - Explicación completa de la tabla
   - Guía de uso e interpretación
   - Ejemplos de lectura y patrones observables

## Contenido de la Tabla

### Encabezados (7 columnas)
```
Diversity | Progress | w_set_A | w_set_B | w_set_C | w_set_D | Activated_Rules
```

### Rango de Valores

| Columna | Valores Mínimos | Valores Máximos |
|---------|---|---|
| Diversity | 0.00 | 1.00 |
| Progress | 0.00 | 1.00 |
| w_set_A | 0.2248 | 0.7752 |
| w_set_B | 0.2333 | 0.7667 |
| w_set_C | 0.3000 | 0.7000 |
| w_set_D | 0.2200 | 0.7444 |

### Ejemplos de Filas

```
Fila 1:   0.00, 0.00, 0.5000, 0.5000, 0.5000, 0.4200, none
Fila 13:  0.10, 0.10, 0.5000, 0.5000, 0.5000, 0.4378, low AND early -> medium (0.500)
Fila 25:  0.20, 0.20, 0.5000, 0.5000, 0.5000, 0.4467, low AND early -> medium (1.000)
...
Fila 121: 1.00, 1.00, 0.2796, 0.2600, 0.3000, 0.2200, none
```

## Características Principales

✅ **Tabla Completa**: 11×11 = 121 combinaciones de entrada (Diversity 0.0-1.0, Progress 0.0-1.0)

✅ **Todos los w_sets**: Columnas para A, B, C, D con valores calculados

✅ **Reglas Activadas**: Muestra qué reglas fuzzy se disparan para cada combinación

✅ **Formato Tabular Claro**:
- Encabezados descriptivos
- Valores numéricos con precisión (4 decimales para w, 3 para grados)
- Texto ASCII legible para reglas (sin caracteres especiales problemáticos)

✅ **Fácil de Usar**:
- Compatible con Excel, Python, R, SQL
- Separador: coma (CSV estándar)
- Codificación: UTF-8
- Tamaño: 7.4 KB (muy manejable)

## Cómo Usar

### En Excel
```
1. Abrir FUZZY/fuzzy_lookup_table.csv
2. Importar como CSV (codificación UTF-8)
3. Crear gráficos o análisis
```

### En Python
```python
import pandas as pd

df = pd.read_csv('FUZZY/fuzzy_lookup_table.csv')

# Ver primeras filas
print(df.head(10))

# Filtrar por diversidad alta
high_div = df[df['Diversity'] >= 0.7]

# Comparar Sets
print(df[['Diversity', 'Progress', 'w_set_A', 'w_set_B', 'w_set_C', 'w_set_D']])
```

### Regenerar Tabla
```bash
cd FUZZY
python generate_fuzzy_lookup_table.py        # 11×11 = 121 filas (default)
python generate_fuzzy_lookup_table.py 21     # 21×21 = 441 filas (más muestras)
python generate_fuzzy_lookup_table.py 5      # 5×5 = 25 filas (menos muestras, más rápido)
```

## Interpretación de Valores

### Regla: "low AND mid -> low (1.000)"
- **low AND mid**: Diversidad baja Y progreso medio
- **-> low**: Produce output bajo
- **(1.000)**: Disparo completo (100% de activación)
- **Significado**: Cuando la población ha convergido en la mitad del proceso, bajar el peso de inercia para explotar

### Regla: "none"
- Ninguna regla se activó significativamente en esa combinación de entrada
- Sistema usa valor por defecto (centroide del espacio fuzzy)

## Patrones Observables

### Patrón 1: Diversidad
```
Diversity BAJA → w es BAJO (explotación)
Diversity ALTA → w es ALTO (exploración)
```

### Patrón 2: Progreso
```
Progress TEMPRANO (early) → w tiende a SER ALTO
Progress TARDÍO (late) → w tiende a SER BAJO
```

### Patrón 3: Diferencias entre Sets
```
Set A: Más explotador (w_min=0.1, w_max=0.775)
Set B: Más explorador (w_min=0.0, w_max=0.767)
Set C: Rango simétrico (w_min=0.3, w_max=0.7)
Set D: Máximo explotador (w_min=0.22, w_max=0.744)
```

## Validación

La tabla ha sido verificada correctamente:
- ✓ 121 filas de datos + 1 encabezado
- ✓ 7 columnas con nombres descriptivos
- ✓ Valores numéricos consistentes (0.0-1.0 para entradas)
- ✓ Grados de disparo consistentes (0.001-1.000)
- ✓ Archivo CSV válido (legible en Excel)

## Ubicación del Archivo

```
c:\Users\josec\Experimentos_Fuzzy_Python\(solver_bioinspirados)\
└── FUZZY\
    ├── fuzzy_lookup_table.csv              ← TABLA PRINCIPAL
    ├── generate_fuzzy_lookup_table.py      ← Script generador
    ├── LOOKUP_TABLE_README.md              ← Documentación detallada
    ├── fuzzy_controller_w.py               ← Controlador fuzzy (no modificado)
    ├── fuzzy_plots.py                      ← Gráficos fuzzy (no modificado)
    └── plots/                              ← Gráficos PNG (no modificados)
```

## Uso Recomendado

### Para Análisis
1. Abre `fuzzy_lookup_table.csv` en Excel
2. Crea gráficos 2D o 3D
3. Analiza comportamiento en diferentes regiones

### Para Validación
1. Verifica que w_set_A <= w_set_D (Set A menos explotador)
2. Verifica simetría en bordes
3. Verifica tendencias (w↑ cuando Diversity↑)

### Para Documentación
1. Incluye tabla en reportes técnicos
2. Usa en presentaciones para explicar fuzzy logic
3. Compara con resultados de experimentos reales

## Notas Técnicas

- **Precisión**: 4 decimales para w, 3 para grados de disparo
- **Clipping**: Valores se ajustan automáticamente a rangos válidos
- **Defuzzificación**: Centroide (COA)
- **Fuzzificación**: Triangular (membresía lineal)
- **Rango de entrada**: [0, 1] normalizado
- **Rango de salida**: [wMin, wMax] escalonado

## Archivos No Modificados

Como se solicitó, NO se modificaron otros archivos del proyecto:
- `FUZZY/fuzzy_controller_w.py` ✓ (sin cambios)
- `analisis.py` ✓ (sin cambios)
- Otros módulos ✓ (sin cambios)

Solo se agregaron:
- `FUZZY/generate_fuzzy_lookup_table.py` (nuevo)
- `FUZZY/fuzzy_lookup_table.csv` (generado)
- `FUZZY/LOOKUP_TABLE_README.md` (documentación)

## Próximos Pasos

1. **Abre la tabla**: `FUZZY/fuzzy_lookup_table.csv`
2. **Importa en Excel**: Verificar formato visual
3. **Usa en análisis**: Crea gráficos o comparaciones
4. **Regenera si necesario**: `python generate_fuzzy_lookup_table.py`

---

**Status**: ✅ COMPLETADO

**Fecha**: Enero 3, 2026
**Archivo**: FUZZY/fuzzy_lookup_table.csv
**Tamaño**: 7.4 KB (121 filas × 7 columnas)
**Formato**: CSV estándar (UTF-8)
