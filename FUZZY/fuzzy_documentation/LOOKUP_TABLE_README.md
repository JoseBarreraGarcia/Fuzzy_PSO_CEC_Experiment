# Fuzzy Lookup Table - Guía

## Descripción

El archivo `fuzzy_lookup_table.csv` contiene una **tabla de búsqueda completa** del sistema fuzzy de control de peso de inercia. Muestra los valores calculados de salida para todas las combinaciones posibles de entrada.

## Estructura de la Tabla

```
Diversity, Progress, w_set_A, w_set_B, w_set_C, w_set_D, Activated_Rules
0.00,      0.00,     0.5000,  0.5000,  0.5000,  0.4200,  none
0.10,      0.10,     0.5000,  0.5000,  0.5000,  0.4378,  low AND early -> medium (0.500)
...
```

### Columnas

| Columna | Rango | Descripción |
|---------|-------|-------------|
| **Diversity** | 0.0 - 1.0 | Diversidad de la población (0=convergida, 1=exploración máxima) |
| **Progress** | 0.0 - 1.0 | Progreso de iteraciones (0=inicio, 1=final) |
| **w_set_A** | 0.1 - 0.9 | Peso de inercia calculado para Set A (explotación-favorecida) |
| **w_set_B** | 0.0 - 1.0 | Peso de inercia calculado para Set B (balanceado) |
| **w_set_C** | 0.0 - 1.0 | Peso de inercia calculado para Set C (simétrico) |
| **w_set_D** | 0.0 - 0.75 | Peso de inercia calculado para Set D (máxima explotación) |
| **Activated_Rules** | texto | Reglas fuzzy que se disparan para esa combinación |

## Interpretación de Valores

### Peso de Inercia (w)
- **w bajo (0.1 - 0.3)**: Explotación fuerte → el PSO enfatiza soluciones actuales
- **w medio (0.3 - 0.6)**: Balance exploración-explotación
- **w alto (0.6 - 0.9)**: Exploración fuerte → el PSO busca nuevas regiones

### Reglas Activadas
Formato: `{input1} AND {input2} -> {output} (grado_de_disparo)`

**Ejemplo**: `low AND early -> medium (0.500)`
- Si diversidad es LOW (baja) Y progreso es EARLY (temprano)
- Entonces activar regla que produce OUTPUT MEDIUM
- Con grado de disparo 0.500 (50% de activación)

**Especial**: `none` significa que ninguna regla se activó significativamente en esos valores de entrada

## Casos de Uso

### 1. Validación del Sistema Fuzzy
Verificar que los valores de w tienen sentido:
```
- Diversidad BAJA + Progreso TEMPRANO → w BAJO (explotación)
- Diversidad ALTA + Progreso TEMPRANO → w ALTO (exploración)
- Diversidad ALTA + Progreso TARDÍO → w BAJO (convergencia final)
```

### 2. Análisis de Sensibilidad
Ver cómo cambia w cuando varía ligeramente la entrada:
```
Diversity=0.40, Progress=0.40 → w_set_A ≈ 0.5000
Diversity=0.41, Progress=0.40 → w_set_A ≈ 0.5000 (pequeño cambio)
Diversity=0.50, Progress=0.40 → w_set_A ≈ 0.5000 (similar)
```

### 3. Comparación de Configuraciones
Ver diferencias entre Sets A, B, C, D en mismo punto:
```
Diversity=0.50, Progress=0.50:
  Set A: 0.5000
  Set B: 0.5000
  Set C: 0.5000
  Set D: 0.4378 ← Set D es MÁS explotador
```

### 4. Documentación y Papers
Insertar tabla o gráfico derivado en reportes técnicos.

## Generación de la Tabla

### Automática
```bash
cd FUZZY
python generate_fuzzy_lookup_table.py
```

### Con Parámetro Personalizado
```bash
# Usar 21 muestras (0, 0.05, 0.10, ..., 1.0) en lugar de 11
python generate_fuzzy_lookup_table.py 21
```

### Parámetros Disponibles
- **n_samples**: Número de muestras por dimensión (default: 11)
  - 11 → 121 filas (0.0, 0.1, 0.2, ..., 1.0)
  - 21 → 441 filas (0.0, 0.05, 0.10, ..., 1.0)
  - 101 → 10,201 filas (0.0, 0.01, 0.02, ..., 1.0)

## Estadísticas de la Tabla Actual

- **Filas de datos**: 121
- **Columnas**: 7
- **Tamaño del archivo**: ~12 KB
- **Rango de w_set_A**: 0.2248 - 0.7752
- **Rango de w_set_B**: 0.2333 - 0.7667
- **Rango de w_set_C**: 0.3000 - 0.7000 (rango fijo)
- **Rango de w_set_D**: 0.2200 - 0.7444

## Patrones Observables

### Patrón 1: Diversidad vs Peso de Inercia
```
Cuando Diversidad BAJA:
  → w es BAJO (explotación)
Cuando Diversidad ALTA:
  → w es ALTO (exploración)
```

### Patrón 2: Progreso vs Peso de Inercia
```
Cuando Progreso es TEMPRANO:
  → w tiende a SER ALTO (mantener exploración)
Cuando Progreso es TARDÍO:
  → w tiende a SER BAJO (convergencia)
```

### Patrón 3: Diferencias entre Sets
```
Set A: MÁS explotador (w_min=0.1)
Set B: Balanceado (w_min=0.0, w_max=1.0)
Set C: Rango fijo en 0.3-0.7 (más estable)
Set D: Máximo explotador (w_max=0.75)
```

## Ejemplos de Lectura

### Ejemplo 1
**Entrada**: Diversity=0.20, Progress=0.50
**Salida**:
- w_set_A: 0.2248 (muy bajo → explotación fuerte)
- w_set_B: 0.2333
- w_set_C: 0.3000
- w_set_D: 0.2200 (mínimo absoluto)
- Regla: `low AND mid -> low (1.000)` (disparo completo)

**Interpretación**: Diversidad baja en mitad del proceso → bajar peso de inercia para explotar

### Ejemplo 2
**Entrada**: Diversity=0.80, Progress=0.20
**Salida**:
- w_set_A: 0.7752 (muy alto → exploración máxima)
- w_set_B: 0.7667
- w_set_C: 0.7000
- w_set_D: 0.7444
- Regla: `high AND early -> high (1.000)`

**Interpretación**: Alta diversidad temprano → mantener exploración con peso alto

## Notas Técnicas

- **Precisión**: 4 decimales para w, 3 decimales para grados de disparo
- **Clipping**: Valores fuera de rango se ajustan automáticamente a [0, 1]
- **Defuzzificación**: Centroide (COA) del área fuzzy agregada
- **Fuzzificación**: Triangular (membresía lineal por tramos)

## Uso Avanzado

### Importar en Python
```python
import pandas as pd

# Leer tabla
df = pd.read_csv('FUZZY/fuzzy_lookup_table.csv')

# Filtrar por Diversity
high_div = df[df['Diversity'] >= 0.7]

# Obtener w_set_A para Progress=0.5
w_at_50 = df[df['Progress'] == 0.50]['w_set_A']

# Comparar Sets
print(df[['Diversity', 'Progress', 'w_set_A', 'w_set_D']].head(10))
```

### Graficar
```python
import matplotlib.pyplot as plt

# Crear gráfico 3D: Diversity vs Progress vs w
# (Ver ejemplos en fuzzy_plots.py)
```

### Exportar a Excel
```bash
# Copiar archivo a carpeta de trabajo
cp FUZZY/fuzzy_lookup_table.csv path/to/excel/
# Abrir en Excel y aplicar formato
```

## Mantenimiento

### Regenerar Tabla
Si cambias las funciones de membresía en `fuzzy_controller_w.py`:
```bash
python generate_fuzzy_lookup_table.py
```

La tabla se actualizará automáticamente con los nuevos valores.

### Validación
Para verificar que la tabla es correcta:
1. Abre `fuzzy_lookup_table.csv` en Excel
2. Verifica que w_set_A < w_set_D (Set A menos explotador)
3. Verifica tendencias: w↑ cuando Diversity↑
4. Verifica simetría: filas iguales en bordes (0.0 y 1.0)

---

**Archivo**: `FUZZY/fuzzy_lookup_table.csv`
**Generado por**: `FUZZY/generate_fuzzy_lookup_table.py`
**Última actualización**: 2025-02-04
**Formato**: CSV (UTF-8, compatible con Excel, Python, R)
